class_name BattleCore
extends RefCounted
## 1세대 배틀 로직 (UI 없음). run_turn() 이 이벤트 목록을 반환하고, 화면은 이를 재생한다.
## 사이드 0/1. 메시지의 {A..} 는 행동하는 쪽(a), {D..} 는 반대쪽 포켓몬 이름으로 치환된다.

const PHYSICAL := ["NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "BIRD"]
const STAGE_NUM := [25, 28, 33, 40, 50, 66, 100, 150, 200, 250, 300, 350, 400]
const HIGH_CRIT := ["KARATE_CHOP", "RAZOR_LEAF", "CRABHAMMER", "SLASH"]
const STAT_KO := {"atk": "공격", "def": "방어", "spd": "스피드", "spc": "특수", "acc": "명중률", "eva": "회피율"}
const STATUS_KO := {"PSN": "독", "BRN": "화상", "PAR": "마비", "SLP": "잠듦", "FRZ": "얼음"}
const BALL_RAND := {"POKE_BALL": 256, "GREAT_BALL": 201, "ULTRA_BALL": 151, "SAFARI_BALL": 151}

var parties := [[], []]
var active := [0, 0]
var vol := [{}, {}]
var kind := "wild"  # wild | trainer | pvp
var events: Array = []
var ended := ""  # "" | "run" | "caught" | "teleport"
var run_attempts := 0
var catch_rate := -1  # 사파리존: 먹이/돌로 바뀐 포획률
var safari_mood := 0  # >0 먹는 중, <0 화남 (남은 턴)
var no_catch := false
var _moved := [false, false]


func _init(p0: Array, p1: Array, k := "wild") -> void:
	parties = [p0, p1]
	kind = k
	active = [_first_alive(0), _first_alive(1)]
	reset_vol(0)
	reset_vol(1)


func _first_alive(s: int) -> int:
	for i in parties[s].size():
		if parties[s][i].hp > 0:
			return i
	return 0


func mon(s: int) -> Dictionary:
	return parties[s][active[s]]


func alive_count(s: int) -> int:
	var n := 0
	for m in parties[s]:
		if m.hp > 0:
			n += 1
	return n


func reset_vol(s: int) -> void:
	vol[s] = {
		"stages": {"atk": 0, "def": 0, "spd": 0, "spc": 0, "acc": 0, "eva": 0},
		"confuse": 0, "flinch": false, "seeded": false, "reflect": false, "lscreen": false,
		"focus": false, "sub": 0, "charging": "", "invul": false, "recharge": false,
		"lock_move": "", "lock_turns": 0, "lock_kind": "", "trapped": false,
		"disabled": "", "disable_turns": 0, "mist": false, "toxic": 0, "bide_dmg": 0,
		"last_move": "", "types": [], "stats": {}, "moves": [], "last_dmg": 0,
	}
	# 교체되면 상대의 조이기 등도 풀림
	var o: Dictionary = vol[1 - s] if vol[1 - s].size() > 0 else {}
	if o.size() > 0 and o.lock_kind == "trap":
		o.lock_move = ""
		o.lock_turns = 0
		o.lock_kind = ""


# ------------------------------------------------------------------ 이벤트
func msg(text: String, a := 0) -> void:
	events.append({"t": "msg", "text": text, "a": a})


func _hp_event(s: int) -> void:
	var m := mon(s)
	events.append({"t": "hp", "s": s, "hp": m.hp, "max": m.max_hp})


func _status_event(s: int) -> void:
	events.append({"t": "status", "s": s, "status": mon(s).status})


# ------------------------------------------------------------------ 능력치
func types_of(s: int) -> Array:
	if vol[s].types.size() > 0:
		return vol[s].types
	return DB.pokemon[mon(s).species].types


func moves_of(s: int) -> Array:
	if vol[s].moves.size() > 0:
		return vol[s].moves
	return mon(s).moves


func raw_stat(s: int, st: String) -> int:
	if vol[s].stats.has(st):
		return vol[s].stats[st]
	return mon(s)[st + "_stat"]


func stat(s: int, st: String) -> int:
	var v := raw_stat(s, st)
	v = v * STAGE_NUM[vol[s].stages[st] + 6] / 100
	if st == "spd" and mon(s).status == "PAR":
		v /= 4
	if st == "atk" and mon(s).status == "BRN":
		v /= 2
	return maxi(1, v)


# ------------------------------------------------------------------ 턴 진행
## 행동: {"type":"move","slot":i} | {"type":"switch","to":i} | {"type":"item","item":X,"target":i}
##       {"type":"ball","item":X} | {"type":"run"}
func run_turn(a0: Dictionary, a1: Dictionary) -> Array:
	events = []
	_moved = [false, false]
	var acts := [a0, a1]
	for s in 2:
		var f := _forced_action(s)
		if not f.is_empty():
			acts[s] = f
	# 교체/도구/도망 먼저
	for s in 2:
		if acts[s].type != "move":
			_do_action(s, acts[s])
			if ended != "":
				return events
	var order := [0, 1]
	if acts[0].type == "move" and acts[1].type == "move":
		var p0 := _priority(0, acts[0])
		var p1 := _priority(1, acts[1])
		var s0 := stat(0, "spd")
		var s1 := stat(1, "spd")
		if p1 > p0 or (p1 == p0 and (s1 > s0 or (s1 == s0 and randi() % 2 == 0))):
			order = [1, 0]
	for s in order:
		if acts[s].type != "move":
			continue
		if mon(s).hp <= 0 or mon(1 - s).hp <= 0:
			break
		_use_move(s, acts[s])
		_moved[s] = true
		if ended != "":
			return events
		if mon(0).hp <= 0 or mon(1).hp <= 0:
			break
		_residual(s)
		if mon(0).hp <= 0 or mon(1).hp <= 0:
			break
	vol[0].flinch = false
	vol[1].flinch = false
	return events


func _priority(s: int, act: Dictionary) -> int:
	var mid := _move_id_for(s, act)
	if mid == "QUICK_ATTACK":
		return 1
	if mid == "COUNTER":
		return -1
	return 0


func _move_id_for(s: int, act: Dictionary) -> String:
	if vol[s].charging != "":
		return vol[s].charging
	if vol[s].lock_move != "":
		return vol[s].lock_move
	var slot: int = act.get("slot", -1)
	var ms := moves_of(s)
	if slot < 0 or slot >= ms.size():
		return "STRUGGLE"
	return ms[slot].id


## 반동/모으기/난동 등 강제 행동
func _forced_action(s: int) -> Dictionary:
	var v: Dictionary = vol[s]
	if v.recharge or v.charging != "" or v.lock_move != "":
		return {"type": "move", "slot": -2}
	return {}


func can_switch(s: int) -> bool:
	return vol[s].lock_move == "" and vol[s].charging == "" and not vol[s].recharge


func _do_action(s: int, act: Dictionary) -> void:
	match act.type:
		"switch":
			msg("돌아와, {A}!", s)
			events.append({"t": "recall", "s": s})
			active[s] = act.to
			reset_vol(s)
			events.append({"t": "send", "s": s, "idx": act.to})
			msg("가라! {A}!", s)
		"run":
			_try_run(s)
		"ball":
			_throw_ball(s, act.item)
		"item":
			_use_item(s, act.item, act.get("target", active[s]))
		"scared":
			msg("{A:은} 너무 무서워서 움직일 수 없다!", s)
		"ghost":
			msg("유령: 나가라... 나가라...", s)
		"bait":
			msg("{PLAYER}는(은) 먹이를 던졌다!", s)
			msg("{D:은} 먹이를 먹고 있다!", s)
			catch_rate = maxi(1, _base_catch() / 2)
			safari_mood = randi_range(1, 5)
		"rock":
			msg("{PLAYER}는(은) 돌을 던졌다!", s)
			msg("{D:은} 화가 났다!", s)
			catch_rate = mini(255, _base_catch() * 2)
			safari_mood = -randi_range(1, 5)
		"safari_watch":
			if safari_mood > 0:
				msg("{A:은} 먹이를 먹고 있다!", s)
			elif safari_mood < 0:
				msg("{A:은} 화가 나 있다!", s)
			else:
				msg("{A:은} 이쪽을 살피고 있다...", s)
			var x: int = mon(s).spd_stat * 2
			if safari_mood < 0:
				x *= 2
			elif safari_mood > 0:
				x /= 4
			if safari_mood != 0:
				safari_mood += -1 if safari_mood > 0 else 1
			if randi() % 256 < mini(255, x):
				msg("{A:은} 도망쳐 버렸다!", s)
				ended = "run"


func switch_in(s: int, idx: int) -> Array:
	events = []
	active[s] = idx
	reset_vol(s)
	events.append({"t": "send", "s": s, "idx": idx})
	msg("가라! {A}!", s)
	return events


func _try_run(s: int) -> void:
	run_attempts += 1
	var mine = mon(s).spd_stat
	var theirs := int(mon(1 - s).spd_stat / 4) % 256
	var ok = theirs == 0 or mine >= mon(1 - s).spd_stat
	if not ok:
		var odds = mine * 32 / theirs + 30 * (run_attempts - 1)
		ok = odds > 255 or randi() % 256 < odds
	if ok:
		msg("무사히 도망쳤다!", s)
		ended = "run"
	else:
		msg("도망칠 수 없었다!", s)


func _base_catch() -> int:
	return catch_rate if catch_rate >= 0 else DB.pokemon[mon(1).species].catch


func _throw_ball(s: int, ball: String) -> void:
	var o := 1 - s
	var m := mon(o)
	msg("{PLAYER}는(은) %s을(를) 던졌다!" % DB.item_name(ball), s)
	var caught := false
	var shakes := 0
	if no_catch:
		events.append({"t": "ball", "s": s, "caught": false, "shakes": 0})
		msg("볼을 피해 버렸다!\n이 포켓몬은 잡을 수 없다!", s)
		return
	if ball == "MASTER_BALL":
		caught = true
	else:
		var r1 = randi() % BALL_RAND.get(ball, 256)
		var status_v := 25 if m.status in ["SLP", "FRZ"] else (12 if m.status != "" else 0)
		if r1 < status_v:
			caught = true
		elif r1 - status_v <= _base_catch():
			var factor := 8 if ball == "GREAT_BALL" else 12
			var w = m.max_hp * 255 / factor / maxi(1, m.hp / 4)
			w = mini(w, 255)
			if randi() % 256 <= w:
				caught = true
			else:
				var x = _base_catch() * 100 / BALL_RAND.get(ball, 256)
				x = x * w / 255 + (10 if status_v == 25 else (5 if status_v == 12 else 0))
				shakes = 0 if x < 10 else (1 if x < 30 else (2 if x < 70 else 3))
		else:
			shakes = 0
	events.append({"t": "ball", "s": s, "caught": caught, "shakes": 3 if caught else shakes})
	if caught:
		msg("신난다! {D}을(를) 잡았다!", s)
		ended = "caught"
	else:
		msg(["이런! 포켓몬이 볼에서 나와버렸다!", "아앗! 잡았다고 생각했는데!", "아깝다! 조금만 더하면 됐는데!", "으으! 거의 잡았는데!"][shakes], s)


func _use_item(s: int, item: String, target: int) -> void:
	var m: Dictionary = parties[s][target]
	var name := Mon.name_of(m)
	match item:
		"POKE_DOLL":
			msg("{PLAYER}는(은) 삐삐인형을 던졌다!\n그 틈에 무사히 도망쳤다!", s)
			ended = "run"
			return
		"POKE_FLUTE":
			msg("{PLAYER}는(은) 포켓몬 피리를 불었다!", s)
			var woke := false
			for side in 2:
				for pm in parties[side]:
					if pm.status == "SLP":
						pm.status = ""
						pm.sleep = 0
						woke = true
			msg("모든 포켓몬이 잠에서 깨어났다!" if woke else "흥겨운 멜로디가 울려 퍼진다!", s)
			_status_event(0)
			_status_event(1)
			return
		"POTION", "SUPER_POTION", "HYPER_POTION", "MAX_POTION", "FULL_RESTORE":
			var amt := {"POTION": 20, "SUPER_POTION": 50, "HYPER_POTION": 200}.get(item, 9999)
			m.hp = mini(m.max_hp, m.hp + amt)
			if item == "FULL_RESTORE":
				m.status = ""
			msg("%s의 체력이 회복되었다!" % name, s)
		"ANTIDOTE", "BURN_HEAL", "ICE_HEAL", "AWAKENING", "PARLYZ_HEAL", "FULL_HEAL":
			m.status = ""
			m.sleep = 0
			msg("%s의 상태가 회복되었다!" % name, s)
		"REVIVE", "MAX_REVIVE":
			m.hp = m.max_hp if item == "MAX_REVIVE" else m.max_hp / 2
			msg("%s의 기력이 돌아왔다!" % name, s)
		"X_ATTACK", "X_DEFEND", "X_SPEED", "X_SPECIAL", "X_ACCURACY", "DIRE_HIT", "GUARD_SPEC":
			var st := {"X_ATTACK": "atk", "X_DEFEND": "def", "X_SPEED": "spd", "X_SPECIAL": "spc", "X_ACCURACY": "acc"}.get(item, "")
			if st != "":
				_change_stage(s, st, 1, s)
			elif item == "DIRE_HIT":
				vol[s].focus = true
				msg("{A:은} 의욕이 넘친다!", s)
			else:
				vol[s].mist = true
				msg("{A:은} 흰안개에 둘러싸였다!", s)
	if target == active[s]:
		_hp_event(s)
		_status_event(s)


# ------------------------------------------------------------------ 기술 사용
func _use_move(s: int, act: Dictionary) -> void:
	var d := 1 - s
	var m := mon(s)
	var v: Dictionary = vol[s]
	if v.recharge:
		v.recharge = false
		msg("{A:은} 반동으로 움직일 수 없다!", s)
		return
	if m.status == "SLP":
		m.sleep -= 1
		if m.sleep <= 0:
			m.status = ""
			_status_event(s)
			msg("{A:은} 잠에서 깨어났다!", s)
		else:
			msg("{A:은} 쿨쿨 잠들어 있다.", s)
		v.lock_move = ""
		return
	if m.status == "FRZ":
		msg("{A:은} 얼어버려서 움직일 수 없다!", s)
		return
	if _opponent_traps(s):
		msg("{A:은} 몸이 조여져서 움직일 수 없다!", s)
		return
	if v.flinch:
		v.flinch = false
		msg("{A:은} 풀이 죽어 움직일 수 없다!", s)
		return
	if v.disable_turns > 0:
		v.disable_turns -= 1
		if v.disable_turns == 0:
			v.disabled = ""
			msg("{A}의 사슬묶기가 풀렸다!", s)
	if v.confuse > 0:
		v.confuse -= 1
		if v.confuse == 0:
			msg("{A}의 혼란이 풀렸다!", s)
		else:
			msg("{A:은} 혼란에 빠져 있다!", s)
			if randi() % 2 == 0:
				var dmg := _raw_damage(m.level, 40, stat(s, "atk"), stat(s, "def"), false)
				msg("영문도 모른 채 자신을 공격했다!", s)
				v.charging = ""
				v.invul = false
				v.lock_move = ""
				_damage(s, dmg)
				return
	if m.status == "PAR" and randi() % 4 == 0:
		msg("{A:은} 몸이 저려서 움직일 수 없다!", s)
		v.charging = ""
		v.invul = false
		v.lock_move = ""
		return

	var move_id := ""
	var continuing := false
	if v.charging != "":
		move_id = v.charging
		v.charging = ""
		v.invul = false
		continuing = true
	elif v.lock_move != "":
		move_id = v.lock_move
		continuing = true
	else:
		var slot: int = act.get("slot", -1)
		var ms := moves_of(s)
		if slot < 0 or slot >= ms.size() or ms[slot].pp <= 0 or ms[slot].id == v.disabled:
			move_id = "STRUGGLE"
		else:
			move_id = ms[slot].id
			ms[slot].pp -= 1
			events.append({"t": "pp", "s": s, "slot": slot, "pp": ms[slot].pp})
	v.last_move = move_id
	_execute(s, d, move_id, continuing)


func _opponent_traps(s: int) -> bool:
	var o: Dictionary = vol[1 - s]
	return o.lock_kind == "trap" and o.lock_turns > 0


func _execute(s: int, d: int, move_id: String, continuing := false) -> void:
	var mv: Dictionary = _move_data(move_id)
	var eff: String = mv.effect
	var v: Dictionary = vol[s]
	var vd: Dictionary = vol[d]
	var name: String = mv.name

	# 모으는 기술 1턴째
	if not continuing and eff in ["CHARGE_EFFECT", "FLY_EFFECT"]:
		msg("{A}의 %s!" % name, s)
		var t := {
			"RAZOR_WIND": "{A:은} 회오리를 일으켰다!", "SOLARBEAM": "{A:은} 빛을 흡수했다!",
			"SKULL_BASH": "{A:은} 목을 움츠렸다!", "SKY_ATTACK": "{A:을} 격렬한 빛이 감쌌다!",
			"FLY": "{A:은} 하늘 높이 날아올랐다!", "DIG": "{A:은} 땅으로 파고들었다!",
		}.get(move_id, "{A:은} 힘을 모으고 있다!")
		msg(t, s)
		v.charging = move_id
		v.invul = eff == "FLY_EFFECT"
		events.append({"t": "hide", "s": s, "on": v.invul})
		return
	if continuing and eff == "FLY_EFFECT":
		events.append({"t": "hide", "s": s, "on": false})

	if v.lock_kind == "bide":
		v.lock_turns -= 1
		if v.lock_turns > 0:
			msg("{A:은} 참고 있다!", s)
			return
		v.lock_move = ""
		v.lock_kind = ""
		msg("{A:은} 참았던 에너지를 방출했다!", s)
		if v.bide_dmg == 0:
			msg("그러나 실패했다!", s)
			return
		_damage(d, v.bide_dmg * 2)
		v.bide_dmg = 0
		return

	if not continuing or v.lock_kind == "thrash":
		msg("{A}의 %s!" % name, s)

	match eff:
		"METRONOME_EFFECT":
			var pool := DB.moves.keys().filter(func(k): return k not in ["METRONOME", "STRUGGLE"])
			_execute(s, d, pool.pick_random())
			return
		"MIRROR_MOVE_EFFECT":
			if vd.last_move == "" or vd.last_move == "MIRROR_MOVE":
				msg("그러나 실패했다!", s)
				return
			_execute(s, d, vd.last_move)
			return
		"SPLASH_EFFECT":
			msg("그러나 아무 일도 일어나지 않았다!", s)
			return

	# 자신 대상 기술
	if _is_self_move(eff):
		_self_effect(s, d, move_id, eff)
		return

	# 명중 판정
	if not _hits(s, d, mv, eff):
		msg("그러나 {A}의 공격은 빗나갔다!", s)
		if eff == "JUMP_KICK_EFFECT":
			msg("{A:은} 기세가 넘쳐 땅에 부딪혔다!", s)
			_damage(s, 1)
		if eff == "EXPLODE_EFFECT":
			_damage(s, mon(s).hp)
		_end_lock_on_miss(s)
		return

	if mv.power == 0 and not eff in ["SPECIAL_DAMAGE_EFFECT", "SUPER_FANG_EFFECT", "OHKO_EFFECT"]:
		_status_move(s, d, move_id, eff)
		return

	# 공격 기술
	var mtype: String = mv.type
	var mult := 1.0
	for t in types_of(d):
		mult *= DB.type_mult(mtype, t)
	if mult == 0.0 and eff not in ["SPECIAL_DAMAGE_EFFECT"]:
		msg("{D}에게는 효과가 없는 것 같다...", s)
		_end_lock_on_miss(s)
		return

	var total := 0
	var hits := 1
	if eff == "TWO_TO_FIVE_ATTACKS_EFFECT":
		hits = [2, 2, 2, 3, 3, 3, 4, 5].pick_random()
	elif eff in ["ATTACK_TWICE_EFFECT", "TWINEEDLE_EFFECT"]:
		hits = 2
	var landed := 0
	var crit_any := false
	for i in hits:
		var dmg := 0
		var crit := false
		match eff:
			"SPECIAL_DAMAGE_EFFECT":
				dmg = {"SONICBOOM": 20, "DRAGON_RAGE": 40}.get(move_id, mon(s).level)
				if move_id == "PSYWAVE":
					dmg = randi_range(1, maxi(1, mon(s).level * 3 / 2))
			"SUPER_FANG_EFFECT":
				dmg = maxi(1, mon(d).hp / 2)
			"OHKO_EFFECT":
				if stat(s, "spd") < stat(d, "spd"):
					msg("그러나 실패했다!", s)
					return
				dmg = mon(d).hp
				msg("일격필살!", s)
			_:
				var r := _calc_damage(s, d, mv, mult)
				dmg = r[0]
				crit = r[1]
		if vd.sub > 0:
			vd.sub -= dmg
			msg("대타가 공격을 대신 받았다!", s)
			if vd.sub <= 0:
				vd.sub = 0
				msg("{D}의 대타는 사라졌다!", s)
				events.append({"t": "sub", "s": d, "on": false})
			landed += 1
			continue
		if crit:
			crit_any = true
		total += dmg
		vd.last_dmg = dmg
		_damage(d, dmg)
		landed += 1
		if crit and hits == 1:
			msg("급소에 맞았다!", s)
		if mon(d).hp <= 0:
			break
	if hits > 1:
		if crit_any:
			msg("급소에 맞았다!", s)
		msg("%d번 맞았다!" % landed, s)
	if eff not in ["SPECIAL_DAMAGE_EFFECT", "SUPER_FANG_EFFECT", "OHKO_EFFECT"]:
		if mult > 1.0:
			msg("효과가 굉장했다!", s)
		elif mult < 1.0:
			msg("효과가 별로인 듯하다...", s)
	# 얼음 상태는 불꽃 기술로 녹음
	if mtype == "FIRE" and mon(d).status == "FRZ" and mon(d).hp > 0:
		mon(d).status = ""
		_status_event(d)
		msg("{D}의 얼음이 녹았다!", s)
	_after_damage(s, d, move_id, eff, total, mtype)


func _end_lock_on_miss(s: int) -> void:
	var v: Dictionary = vol[s]
	if v.lock_kind == "trap":
		v.lock_move = ""
		v.lock_kind = ""
		v.lock_turns = 0


func _after_damage(s: int, d: int, move_id: String, eff: String, total: int, mtype: String) -> void:
	var v: Dictionary = vol[s]
	var vd: Dictionary = vol[d]
	var target_alive = mon(d).hp > 0
	match eff:
		"DRAIN_HP_EFFECT", "DREAM_EATER_EFFECT":
			var heal := maxi(1, total / 2)
			mon(s).hp = mini(mon(s).max_hp, mon(s).hp + heal)
			_hp_event(s)
			msg("{D}의 체력을 흡수했다!", s)
		"RECOIL_EFFECT":
			var rec := maxi(1, total / (2 if move_id == "STRUGGLE" else 4))
			msg("{A:은} 반동으로 데미지를 입었다!", s)
			_damage(s, rec)
		"EXPLODE_EFFECT":
			_damage(s, mon(s).hp)
		"PAY_DAY_EFFECT":
			events.append({"t": "payday", "s": s, "amount": mon(s).level * 2})
			msg("동전이 주변에 흩어졌다!", s)
		"HYPER_BEAM_EFFECT":
			if target_alive:
				v.recharge = true
		"THRASH_PETAL_DANCE_EFFECT":
			if v.lock_kind != "thrash":
				v.lock_move = move_id
				v.lock_kind = "thrash"
				v.lock_turns = randi_range(2, 3)
			v.lock_turns -= 1
			if v.lock_turns <= 0:
				v.lock_move = ""
				v.lock_kind = ""
				v.confuse = randi_range(2, 5)
				msg("{A:은} 지쳐서 혼란에 빠졌다!", s)
		"TRAPPING_EFFECT":
			if v.lock_kind != "trap":
				v.lock_move = move_id
				v.lock_kind = "trap"
				v.lock_turns = [2, 2, 2, 3, 3, 3, 4, 5].pick_random()
			v.lock_turns -= 1
			if v.lock_turns <= 0 or not target_alive:
				v.lock_move = ""
				v.lock_kind = ""
	if not target_alive or vd.sub > 0:
		return
	var st := ""
	var chance := 0.0
	match eff:
		"POISON_SIDE_EFFECT1", "TWINEEDLE_EFFECT":
			st = "PSN"; chance = 0.2
		"POISON_SIDE_EFFECT2":
			st = "PSN"; chance = 0.4
		"BURN_SIDE_EFFECT1":
			st = "BRN"; chance = 0.1
		"BURN_SIDE_EFFECT2":
			st = "BRN"; chance = 0.3
		"FREEZE_SIDE_EFFECT1":
			st = "FRZ"; chance = 0.1
		"FREEZE_SIDE_EFFECT2":
			st = "FRZ"; chance = 0.3
		"PARALYZE_SIDE_EFFECT1":
			st = "PAR"; chance = 0.1
		"PARALYZE_SIDE_EFFECT2":
			st = "PAR"; chance = 0.3
		"FLINCH_SIDE_EFFECT1", "FLINCH_SIDE_EFFECT2":
			if randf() < (0.1 if eff.ends_with("1") else 0.3) and not _moved[d]:
				vd.flinch = true
		"CONFUSION_SIDE_EFFECT":
			if randf() < 0.1 and vd.confuse == 0:
				vd.confuse = randi_range(2, 5)
				msg("{D:은} 혼란에 빠졌다!", s)
		"ATTACK_DOWN_SIDE_EFFECT", "DEFENSE_DOWN_SIDE_EFFECT", "SPEED_DOWN_SIDE_EFFECT", "SPECIAL_DOWN_SIDE_EFFECT":
			if randf() < 0.33:
				var which = {"ATTACK": "atk", "DEFENSE": "def", "SPEED": "spd", "SPECIAL": "spc"}[eff.split("_")[0]]
				_change_stage(d, which, -1, s)
	if st != "" and randf() < chance and mon(d).status == "" and not types_of(d).has(mtype):
		_inflict(d, st, s)


func _is_self_move(eff: String) -> bool:
	return eff.contains("_UP") or eff in [
		"FOCUS_ENERGY_EFFECT", "HEAL_EFFECT", "MIST_EFFECT", "LIGHT_SCREEN_EFFECT", "REFLECT_EFFECT",
		"SUBSTITUTE_EFFECT", "HAZE_EFFECT", "CONVERSION_EFFECT", "BIDE_EFFECT",
	] or (eff == "SWITCH_AND_TELEPORT_EFFECT" and false)


func _self_effect(s: int, d: int, move_id: String, eff: String) -> void:
	var v: Dictionary = vol[s]
	var m := mon(s)
	if eff.contains("_UP"):
		var parts := eff.split("_")
		var which = {"ATTACK": "atk", "DEFENSE": "def", "SPEED": "spd", "SPECIAL": "spc", "ACCURACY": "acc", "EVASION": "eva"}[parts[0]]
		_change_stage(s, which, 2 if parts[1] == "UP2" else 1, s)
		return
	match eff:
		"FOCUS_ENERGY_EFFECT":
			v.focus = true
			msg("{A:은} 의욕이 넘친다!", s)
		"HEAL_EFFECT":
			if m.hp >= m.max_hp:
				msg("그러나 실패했다!", s)
				return
			if move_id == "REST":
				m.hp = m.max_hp
				m.status = "SLP"
				m.sleep = 2
				_status_event(s)
				msg("{A:은} 잠들어 체력을 회복했다!", s)
			else:
				m.hp = mini(m.max_hp, m.hp + m.max_hp / 2)
				msg("{A}의 체력이 회복되었다!", s)
			_hp_event(s)
		"MIST_EFFECT":
			v.mist = true
			msg("{A:은} 흰안개에 둘러싸였다!", s)
		"LIGHT_SCREEN_EFFECT":
			v.lscreen = true
			msg("{A:은} 특수공격에 강해졌다!", s)
		"REFLECT_EFFECT":
			v.reflect = true
			msg("{A:은} 물리공격에 강해졌다!", s)
		"SUBSTITUTE_EFFECT":
			var cost = m.max_hp / 4
			if v.sub > 0 or m.hp <= cost:
				msg("그러나 실패했다!", s)
				return
			m.hp -= cost
			v.sub = cost + 1
			_hp_event(s)
			events.append({"t": "sub", "s": s, "on": true})
			msg("{A}의 대타가 나타났다!", s)
		"HAZE_EFFECT":
			for i in 2:
				for k in vol[i].stages:
					vol[i].stages[k] = 0
				vol[i].confuse = 0
				vol[i].seeded = false
				vol[i].reflect = false
				vol[i].lscreen = false
				vol[i].focus = false
				vol[i].mist = false
			if mon(d).status != "":
				mon(d).status = ""
				_status_event(d)
			msg("모든 능력 변화가 원래대로 돌아왔다!", s)
		"CONVERSION_EFFECT":
			v.types = types_of(d).duplicate()
			msg("{A}의 타입이 {D}와(과) 같아졌다!", s)
		"BIDE_EFFECT":
			v.lock_move = move_id
			v.lock_kind = "bide"
			v.lock_turns = randi_range(2, 3)
			v.bide_dmg = 0
			msg("{A:은} 참기 시작했다!", s)


func _status_move(s: int, d: int, move_id: String, eff: String) -> void:
	var vd: Dictionary = vol[d]
	var md := mon(d)
	if vd.sub > 0 and eff not in ["SWITCH_AND_TELEPORT_EFFECT"]:
		msg("그러나 실패했다!", s)
		return
	if eff.contains("_DOWN"):
		var parts := eff.split("_")
		var which = {"ATTACK": "atk", "DEFENSE": "def", "SPEED": "spd", "SPECIAL": "spc", "ACCURACY": "acc", "EVASION": "eva"}[parts[0]]
		if vd.mist:
			msg("{D:은} 흰안개에 보호받고 있다!", s)
			return
		_change_stage(d, which, -2 if parts[1] == "DOWN2" else -1, s)
		return
	match eff:
		"SLEEP_EFFECT":
			if md.status != "":
				msg("그러나 실패했다!", s)
			else:
				_inflict(d, "SLP", s)
		"POISON_EFFECT":
			if md.status != "" or types_of(d).has("POISON"):
				msg("그러나 실패했다!", s)
			else:
				_inflict(d, "PSN", s)
				if move_id == "TOXIC":
					vd.toxic = 1
		"PARALYZE_EFFECT":
			var mt: String = DB.moves[move_id].type
			if md.status != "" or (mt == "ELECTRIC" and types_of(d).has("GROUND")):
				msg("그러나 실패했다!", s)
			else:
				_inflict(d, "PAR", s)
		"CONFUSION_EFFECT":
			if vd.confuse > 0:
				msg("그러나 실패했다!", s)
			else:
				vd.confuse = randi_range(2, 5)
				msg("{D:은} 혼란에 빠졌다!", s)
		"LEECH_SEED_EFFECT":
			if vd.seeded or types_of(d).has("GRASS"):
				msg("그러나 실패했다!", s)
			else:
				vd.seeded = true
				msg("{D}에게 씨앗을 심었다!", s)
		"DISABLE_EFFECT":
			var cand := []
			for mv in moves_of(d):
				if mv.pp > 0:
					cand.append(mv.id)
			if vd.disabled != "" or cand.is_empty():
				msg("그러나 실패했다!", s)
			else:
				vd.disabled = cand.pick_random()
				vd.disable_turns = randi_range(1, 8)
				msg("{D}의 %s을(를) 봉인했다!" % DB.move_name(vd.disabled), s)
		"MIMIC_EFFECT":
			var picked: String = moves_of(d).pick_random().id
			var ms := moves_of(s)
			if vol[s].moves.is_empty():
				vol[s].moves = ms.duplicate(true)
			for mv in vol[s].moves:
				if mv.id == "MIMIC":
					mv.id = picked
					break
			msg("{A:은} %s을(를) 따라 배웠다!" % DB.move_name(picked), s)
		"TRANSFORM_EFFECT":
			vol[s].types = types_of(d).duplicate()
			vol[s].stats = {"atk": raw_stat(d, "atk"), "def": raw_stat(d, "def"), "spd": raw_stat(d, "spd"), "spc": raw_stat(d, "spc")}
			vol[s].stages = vol[d].stages.duplicate()
			var nm := []
			for mv in moves_of(d):
				nm.append({"id": mv.id, "pp": 5, "max": 5})
			vol[s].moves = nm
			events.append({"t": "transform", "s": s, "species": mon(d).species})
			msg("{A:은} {D}(으)로 변신했다!", s)
		"SWITCH_AND_TELEPORT_EFFECT":
			if kind == "wild":
				if move_id == "TELEPORT":
					msg("{A:은} 순간이동으로 사라졌다!", s)
				else:
					msg("{D:은} 날아가 버렸다!", s)
				ended = "teleport"
			else:
				msg("그러나 실패했다!", s)
		_:
			msg("그러나 아무 일도 일어나지 않았다!", s)


func _inflict(d: int, st: String, s: int) -> void:
	var md := mon(d)
	md.status = st
	if st == "SLP":
		md.sleep = randi_range(1, 7)
	_status_event(d)
	var t = {
		"PSN": "{D:은} 독에 걸렸다!", "BRN": "{D:은} 화상을 입었다!", "FRZ": "{D:은} 얼어붙었다!",
		"PAR": "{D:은} 마비되어 기술이 나오기 어려워졌다!", "SLP": "{D:은} 잠들어 버렸다!",
	}[st]
	msg(t, s)
	# 1세대: 상대가 모으는/반동 중이면 해제
	if st in ["SLP", "FRZ"]:
		vol[d].recharge = false


func _change_stage(target: int, which: String, delta: int, a: int) -> void:
	var cur: int = vol[target].stages[which]
	var nv := clampi(cur + delta, -6, 6)
	var who := "{A}" if target == a else "{D}"
	if nv == cur:
		msg("그러나 아무 일도 일어나지 않았다!", a)
		return
	vol[target].stages[which] = nv
	var word := ("크게 올라갔다!" if delta > 1 else "올라갔다!") if delta > 0 else ("크게 떨어졌다!" if delta < -1 else "떨어졌다!")
	msg("%s의 %s이(가) %s" % [who, STAT_KO[which], word], a)


func _hits(s: int, d: int, mv: Dictionary, eff: String) -> bool:
	if vol[d].invul:
		return false
	if eff == "SWIFT_EFFECT":
		return true
	if eff == "DREAM_EATER_EFFECT" and mon(d).status != "SLP":
		return false
	var acc: int = mv.acc * 255 / 100
	acc = acc * STAGE_NUM[vol[s].stages.acc + 6] / 100
	acc = acc * STAGE_NUM[6 - vol[d].stages.eva] / 100
	acc = clampi(acc, 1, 255)
	return randi() % 256 < acc


func _calc_damage(s: int, d: int, mv: Dictionary, mult: float) -> Array:
	var phys: bool = mv.type in PHYSICAL
	var st_a := "atk" if phys else "spc"
	var st_d := "def" if phys else "spc"
	var base_spd: int = DB.pokemon[mon(s).species].spd
	var chance := base_spd / 2
	if HIGH_CRIT.has(mv.get("_id", "")):
		chance *= 8
	if vol[s].focus:
		chance *= 4
	var crit := randi() % 256 < mini(chance, 255)
	var lvl: int = mon(s).level
	var A: int
	var D: int
	if crit:
		A = raw_stat(s, st_a)
		D = raw_stat(d, st_d)
		lvl *= 2
	else:
		A = stat(s, st_a)
		D = stat(d, st_d)
		if phys and vol[d].reflect:
			D *= 2
		if not phys and vol[d].lscreen:
			D *= 2
	if mv.effect == "EXPLODE_EFFECT":
		D = maxi(1, D / 2)
	var dmg := _raw_damage(lvl, mv.power, A, D, false)
	if mv.type in types_of(s):
		dmg = dmg * 3 / 2
	dmg = int(dmg * mult)
	if dmg > 1:
		dmg = dmg * randi_range(217, 255) / 255
	return [maxi(1, dmg), crit]


func _raw_damage(level: int, power: int, A: int, D: int, _crit: bool) -> int:
	if A > 255 or D > 255:
		A = maxi(1, A / 4)
		D = maxi(1, D / 4)
	var dmg := (level * 2 / 5 + 2) * power * A / maxi(1, D) / 50
	return mini(dmg, 997) + 2


func _move_data(move_id: String) -> Dictionary:
	if move_id == "STRUGGLE" and not DB.moves.has("STRUGGLE"):
		return {"name": "발버둥", "effect": "RECOIL_EFFECT", "power": 50, "type": "NORMAL", "acc": 100, "pp": 10}
	var mv: Dictionary = DB.moves[move_id].duplicate()
	mv["_id"] = move_id
	return mv


func _damage(s: int, dmg: int) -> void:
	var m := mon(s)
	if vol[s].lock_kind == "bide":
		vol[s].bide_dmg += dmg
	m.hp = maxi(0, m.hp - dmg)
	_hp_event(s)
	if m.hp == 0:
		m.status = ""
		events.append({"t": "faint", "s": s})
		msg("{A:은} 쓰러졌다!", s)


## 행동 후 독/화상/씨뿌리기 데미지 (1세대 방식)
func _residual(s: int) -> void:
	var m := mon(s)
	var v: Dictionary = vol[s]
	if m.hp <= 0:
		return
	if m.status in ["PSN", "BRN"]:
		var dmg := maxi(1, m.max_hp / 16)
		if v.toxic > 0:
			dmg = maxi(1, m.max_hp * v.toxic / 16)
			v.toxic += 1
		msg("{A:은} %s의 데미지를 입고 있다!" % ("독" if m.status == "PSN" else "화상"), s)
		_damage(s, dmg)
	if m.hp > 0 and v.seeded:
		var dmg2 := maxi(1, m.max_hp / 16)
		msg("씨뿌리기가 {A}의 체력을 빼앗는다!", s)
		_damage(s, dmg2)
		var o := mon(1 - s)
		if o.hp > 0:
			o.hp = mini(o.max_hp, o.hp + dmg2)
			_hp_event(1 - s)


# ------------------------------------------------------------------ AI
func ai_choose(s: int, smart: bool) -> Dictionary:
	var ms := moves_of(s)
	var usable := []
	for i in ms.size():
		if ms[i].pp > 0 and ms[i].id != vol[s].disabled:
			usable.append(i)
	if usable.is_empty():
		return {"type": "move", "slot": -1}
	if not smart:
		return {"type": "move", "slot": usable.pick_random()}
	var best := []
	var best_score := -999.0
	for i in usable:
		var mv: Dictionary = DB.moves[ms[i].id]
		var score := randf() * 10.0
		if mv.power > 0:
			var mult := 1.0
			for t in types_of(1 - s):
				mult *= DB.type_mult(mv.type, t)
			score += mv.power * mult / 4.0
			if mult == 0.0:
				score -= 100
		elif mon(1 - s).status != "" and mv.effect in ["SLEEP_EFFECT", "POISON_EFFECT", "PARALYZE_EFFECT"]:
			score -= 50
		if score > best_score:
			best_score = score
			best = [i]
	return {"type": "move", "slot": best[0]}


## 상태 스냅샷 (PvP 동기화용)
func snapshot() -> Dictionary:
	return {"parties": parties, "active": active}
