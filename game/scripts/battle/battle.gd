class_name Battle
extends CanvasLayer
## 배틀 화면. 야생/트레이너(로컬)와 PvP(네트워크) 모두 처리.
## cfg: {kind:"wild", species, level} | {kind:"trainer", class, index, end_text} | {kind:"pvp", peer, authority, mine, theirs, their_name}

signal finished(result: String)

var cfg: Dictionary
var core: BattleCore
var kind := "wild"
var my_side := 0
var parties := [[], []]  # 표시용 (로컬이면 core.parties 와 동일)
var shown := [0, 0]
var root: Control
var pics := [null, null]
var huds := [{}, {}]
var trainer_pic: TextureRect
var participants := {}  # 적 인덱스 -> [내 파티 인덱스]
var leveled := {}  # 이번 배틀에서 레벨업한 파티 인덱스
var payday := 0
var enemy_trainer := {}
var enemy_name := ""
# PvP
var peer := 0
var authority := false
var _inbox: Array = []
var _last_menu := 0


func _ready() -> void:
	layer = 5
	root = Control.new()
	root.size = Vector2(160, 144)
	add_child(root)
	var bg := ColorRect.new()
	bg.color = Color(0.97, 0.97, 0.95)
	bg.size = Vector2(160, 144)
	root.add_child(bg)


func start(c: Dictionary) -> void:
	cfg = c
	kind = c.kind
	if kind == "pvp":
		peer = c.peer
		authority = c.authority
		my_side = 0 if authority else 1
		enemy_name = c.their_name
		parties[my_side] = c.mine
		parties[1 - my_side] = c.theirs
		if authority:
			core = BattleCore.new(parties[0], parties[1], "pvp")
		Net.pvp_message.connect(_on_pvp)
	else:
		var enemy := []
		if kind == "wild":
			enemy = [Mon.create(c.species, c.level)]
		else:
			enemy_trainer = DB.trainers[c["class"]]
			enemy_name = G.RIVAL_NAME if c["class"].begins_with("RIVAL") else enemy_trainer.name
			var party_def: Array = enemy_trainer.parties[c.index - 1]
			for pair in party_def:
				enemy.append(Mon.create(pair[1], pair[0]))
		parties = [G.party, enemy]
		core = BattleCore.new(G.party, enemy, kind)
	if kind != "pvp":
		core.no_catch = c.get("no_catch", false) or c.get("ghost", false)
	shown = [_first_alive(0), _first_alive(1)]
	Sound.music(_battle_music())
	_build_ui()
	await _intro()
	var result := ""
	if kind == "pvp":
		result = await _pvp_loop()
	else:
		result = await _local_loop()
	UI.close_box()
	if kind == "pvp":
		Net.pvp_message.disconnect(_on_pvp)
	else:
		await _evolutions()
	finished.emit(result)


const LEADERS := ["BROCK", "MISTY", "LT_SURGE", "ERIKA", "KOGA", "SABRINA", "BLAINE", "GIOVANNI", "LORELEI", "BRUNO", "AGATHA", "LANCE"]


func _battle_music() -> String:
	if cfg.has("music"):
		return cfg.music
	if kind == "wild":
		return "WildBattle"
	if kind == "trainer":
		var cls: String = cfg["class"]
		if cls == "RIVAL3":
			return "FinalBattle"
		if LEADERS.has(cls):
			return "GymLeaderBattle"
	return "TrainerBattle"


func _first_alive(s: int) -> int:
	for i in parties[s].size():
		if parties[s][i].hp > 0:
			return i
	return 0


# ------------------------------------------------------------------ UI 구성
func _view(s: int) -> int:
	# 화면 위치: 0 = 아래(내 쪽), 1 = 위(상대)
	return 0 if s == my_side else 1


func _build_ui() -> void:
	for s in 2:
		var v := _view(s)
		var p := TextureRect.new()
		p.stretch_mode = TextureRect.STRETCH_KEEP
		if v == 0:
			p.scale = Vector2(2, 2)
		root.add_child(p)
		pics[s] = p
		var h := {}
		if v == 1:
			h.name = GBBox.label("", Vector2(8, 0))
			h.level = GBBox.label("", Vector2(40, 10))
			h.bar = HPBar.new(Vector2(16, 23), 48)
			h.hp = GBBox.label("", Vector2(0, 0))
		else:
			h.name = GBBox.label("", Vector2(80, 53))
			h.level = GBBox.label("", Vector2(120, 62))
			h.bar = HPBar.new(Vector2(88, 75), 48)
			h.hp = GBBox.label("", Vector2(100, 78))
		h.hp.visible = v == 0
		h.deco = _hud_deco(v)
		root.add_child(h.deco)
		for k in ["name", "level", "bar", "hp"]:
			root.add_child(h[k])
		huds[s] = h
		_set_hud_visible(s, false)
		p.visible = false


func _hud_deco(v: int) -> Control:
	# 원작 HUD의 ㄴ자 선
	var c := Control.new()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func():
		var col := Color(0.1, 0.1, 0.1)
		if v == 1:
			c.draw_line(Vector2(8.5, 22), Vector2(8.5, 30.5), col, 1)
			c.draw_line(Vector2(8, 30.5), Vector2(80, 30.5), col, 1)
		else:
			c.draw_line(Vector2(152.5, 74), Vector2(152.5, 91.5), col, 1)
			c.draw_line(Vector2(80, 91.5), Vector2(153, 91.5), col, 1)
	)
	return c


func _set_hud_visible(s: int, on: bool) -> void:
	for k in ["name", "level", "bar", "hp", "deco"]:
		huds[s][k].visible = on and (k != "hp" or _view(s) == 0)


func _refresh_hud(s: int) -> void:
	var m: Dictionary = parties[s][shown[s]]
	var h: Dictionary = huds[s]
	h.name.text = Mon.name_of(m)
	h.level.text = (BattleCore.STATUS_KO[m.status] if m.status != "" else "Lv%d" % m.level)
	h.bar.ratio = float(m.hp) / m.max_hp
	h.hp.text = "%3d/%3d" % [m.hp, m.max_hp]


func _set_pic(s: int) -> void:
	var m: Dictionary = parties[s][shown[s]]
	var p: TextureRect = pics[s]
	if _view(s) == 0:
		p.texture = Mon.back_tex(m.species)
		p.position = Vector2(8, 32)
	else:
		p.texture = Mon.front_tex(m.species)
		var sz := p.texture.get_size() if p.texture else Vector2(56, 56)
		p.position = Vector2(96 + (56 - sz.x) / 2, 56 - sz.y)
	p.modulate = Color.WHITE


func _name(s: int) -> String:
	var n := Mon.name_of(parties[s][shown[s]])
	if s == my_side:
		return n
	return ("야생 " if kind == "wild" else "상대 ") + n


func _fmt(ev: Dictionary) -> String:
	var a: int = ev.get("a", 0)
	var t: String = ev.text
	for side_key in [["A", a], ["D", 1 - a]]:
		var nm := _name(side_key[1])
		for j in ["은", "이", "을", "와", "으로"]:
			t = t.replace("{%s:%s}" % [side_key[0], j], nm + "{" + j + "}")
		t = t.replace("{%s}" % side_key[0], nm)
	return t


func msg(text: String) -> void:
	await UI.say(text, true)


# ------------------------------------------------------------------ 연출
func _intro() -> void:
	UI.say("", true, false)
	var e := 1 - my_side
	if kind == "wild":
		_set_pic(e)
		var p: TextureRect = pics[e]
		p.visible = true
		var endx := p.position.x
		p.position.x = -60
		var tw := create_tween()
		tw.tween_property(p, "position:x", endx, 0.6)
		await tw.finished
		_refresh_hud(e)
		_set_hud_visible(e, true)
		if cfg.get("ghost", false):
			p.texture = DB.tex("res://assets/misc/ghost.png")
			huds[e].name.text = "유령"
			await msg("앗! 유령이 나타났다!")
			await msg("젠장! 유령의 정체를 알 수 없다!")
		else:
			G.register_seen(parties[e][shown[e]].species)
			Sound.cry(parties[e][shown[e]].species)
			await msg("앗! {W}{이} 튀어나왔다!".replace("{W}", _name(e)))
	else:
		trainer_pic = TextureRect.new()
		var tex_path := "res://assets/trainers/%s.png" % enemy_trainer.get("pic", "")
		trainer_pic.texture = DB.tex(tex_path) if kind == "trainer" else DB.tex("res://assets/misc/red_front.png")
		trainer_pic.position = Vector2(-60, 0)
		root.add_child(trainer_pic)
		var tw2 := create_tween()
		tw2.tween_property(trainer_pic, "position:x", 100.0, 0.6)
		await tw2.finished
		await msg("%s{이} 승부를 걸어왔다!" % enemy_name)
		var tw3 := create_tween()
		tw3.tween_property(trainer_pic, "position:x", 170.0, 0.3)
		await tw3.finished
		trainer_pic.visible = false
		await _send_out(e)
	await _send_out(my_side)
	_mark_participant()


func _send_out(s: int) -> void:
	_set_pic(s)
	var p: TextureRect = pics[s]
	if s == my_side:
		await msg("가라! %s!" % Mon.name_of(parties[s][shown[s]]))
	elif kind != "wild":
		await msg("%s{은} %s{을} 내보냈다!" % [enemy_name, Mon.name_of(parties[s][shown[s]])])
		G.register_seen(parties[s][shown[s]].species)
	p.visible = true
	p.scale = Vector2.ZERO if _view(s) == 1 else Vector2(0, 0)
	var target := Vector2(2, 2) if _view(s) == 0 else Vector2.ONE
	var tw := create_tween()
	tw.tween_property(p, "scale", target, 0.25)
	await tw.finished
	Sound.cry(parties[s][shown[s]].species)
	_refresh_hud(s)
	_set_hud_visible(s, true)


func _play(evs: Array) -> void:
	for ev in evs:
		match ev.t:
			"msg":
				await msg(_fmt(ev))
			"hp":
				var s: int = ev.s
				var m: Dictionary = parties[s][shown[s]]
				var from := float(huds[s].bar.ratio)
				var to: float = float(ev.hp) / ev.max
				if to < from:
					Sound.sfx("Damage")
					await _flash(s)
				var tw := create_tween()
				tw.tween_method(func(r): huds[s].bar.ratio = r; huds[s].hp.text = "%3d/%3d" % [int(round(r * ev.max)), ev.max], from, to, clampf(absf(from - to) * 1.2, 0.15, 0.8))
				await tw.finished
				m.hp = ev.hp
				_refresh_hud(s)
			"faint":
				Sound.sfx("Faint_Fall")
				var p: TextureRect = pics[ev.s]
				var tw2 := create_tween()
				tw2.tween_property(p, "modulate:a", 0.0, 0.3)
				await tw2.finished
				p.visible = false
				_set_hud_visible(ev.s, false)
			"status":
				parties[ev.s][shown[ev.s]].status = ev.status
				_refresh_hud(ev.s)
			"recall":
				pics[ev.s].visible = false
				_set_hud_visible(ev.s, false)
			"send":
				shown[ev.s] = ev.idx
				pics[ev.s].visible = false
				await _send_out_silent(ev.s)
			"hide":
				pics[ev.s].visible = not ev.on
			"transform":
				if _view(ev.s) == 1:
					pics[ev.s].texture = Mon.front_tex(ev.species)
				else:
					pics[ev.s].texture = Mon.back_tex(ev.species)
			"payday":
				if ev.s == my_side:
					payday += ev.amount
			"ball":
				await _ball_anim(ev)
			"pp":
				pass


func _send_out_silent(s: int) -> void:
	_set_pic(s)
	pics[s].visible = true
	_refresh_hud(s)
	_set_hud_visible(s, true)
	if s != my_side:
		G.register_seen(parties[s][shown[s]].species)


func _flash(s: int) -> void:
	var p: TextureRect = pics[s]
	for i in 3:
		p.visible = false
		await UI.wait(0.06)
		p.visible = true
		await UI.wait(0.06)


func _ball_anim(ev: Dictionary) -> void:
	var e := 1 - my_side
	var ball := TextureRect.new()
	ball.texture = DB.tex("res://assets/misc/balls.png")
	var at := AtlasTexture.new()
	at.atlas = ball.texture
	at.region = Rect2(0, 0, 8, 8)
	ball.texture = at
	ball.position = Vector2(40, 80)
	root.add_child(ball)
	Sound.sfx("Ball_Toss")
	var tw := create_tween()
	tw.tween_property(ball, "position", Vector2(120, 40), 0.4)
	await tw.finished
	pics[e].visible = false
	for i in ev.shakes:
		await UI.wait(0.3)
		var t2 := create_tween()
		t2.tween_property(ball, "position:x", 117.0, 0.08)
		t2.tween_property(ball, "position:x", 123.0, 0.08)
		t2.tween_property(ball, "position:x", 120.0, 0.08)
		await t2.finished
	await UI.wait(0.3)
	if not ev.caught:
		Sound.sfx("Ball_Poof")
		pics[e].visible = true
		ball.queue_free()
	else:
		ball.modulate = Color(0.6, 0.6, 0.6)


# ------------------------------------------------------------------ 행동 선택
func _choose_safari() -> Dictionary:
	while true:
		UI.say("사파리볼 ×%d\n무엇을 할까?" % int(G.flags.get("safari_balls", 0)), true, false)
		var c: int = await UI.choose(["볼", "먹이", "돌", "도망친다"], Rect2(56, 96, 104, 48), _last_menu, 2, false)
		_last_menu = c
		match c:
			0:
				G.flags.safari_balls = int(G.flags.get("safari_balls", 0)) - 1
				return {"type": "ball", "item": "SAFARI_BALL"}
			1:
				return {"type": "bait"}
			2:
				return {"type": "rock"}
			3:
				return {"type": "run"}
	return {}


func _choose_action() -> Dictionary:
	if cfg.get("safari", false):
		return await _choose_safari()
	var s := my_side
	while true:
		var m: Dictionary = parties[s][shown[s]]
		UI.say("%s{은}
무엇을 할까?" % Mon.name_of(m), true, false)
		var c: int = await UI.choose(["싸운다", "포켓몬", "가방", "도망친다"], Rect2(56, 96, 104, 48), _last_menu, 2, false)
		_last_menu = c
		match c:
			0:
				var usable := false
				for mv in m.moves:
					if mv.pp > 0:
						usable = true
				if not usable:
					await msg("%s{은} 쓸 수 있는 기술이 없다!" % Mon.name_of(m))
					return {"type": "move", "slot": -1}
				var slot := await _choose_move(m)
				if slot >= 0:
					return {"type": "move", "slot": slot}
			1:
				var idx: int = await Menus.party_menu("battle", shown[s], parties[s])
				if idx >= 0:
					if idx == shown[s]:
						await msg("%s{은} 이미 싸우고 있다!" % Mon.name_of(parties[s][idx]))
					elif parties[s][idx].hp <= 0:
						await msg("기절한 포켓몬은 싸울 수 없다!")
					elif core and not core.can_switch(s):
						await msg("지금은 교체할 수 없다!")
					else:
						return {"type": "switch", "to": idx}
			2:
				if kind == "pvp":
					await msg("통신 대전에서는 도구를 쓸 수 없다!")
					continue
				var r: Dictionary = await Menus.bag_menu("battle")
				if r.is_empty():
					continue
				if r.item.ends_with("_BALL"):
					if kind != "wild":
						await msg("안돼! 남의 포켓몬을 뺏으면 도둑이야!")
						continue
					G.remove_item(r.item)
					return {"type": "ball", "item": r.item}
				G.remove_item(r.item)
				return {"type": "item", "item": r.item, "target": r.get("target", shown[s])}
			3:
				if kind == "wild":
					return {"type": "run"}
				if kind == "pvp":
					UI.say("정말 항복할까?", true, false)
					if await UI.yes_no():
						return {"type": "forfeit"}
					continue
				await msg("안돼! 승부 도중에 등을 보일 수는 없어!")
	return {}


func _choose_move(m: Dictionary) -> int:
	var names := []
	for mv in m.moves:
		names.append(DB.move_name(mv.id))
	var info := GBBox.new(Rect2(0, 60, 64, 36))
	var info_l := GBBox.label("", Vector2(8, 5))
	info.add_child(info_l)
	UI.root().add_child(info)
	var upd := func(i):
		var mv: Dictionary = m.moves[i]
		info_l.text = "%s\nPP %2d/%2d" % [DB.type_name(DB.moves[mv.id].type), mv.pp, mv.max]
	var slot := -1
	while true:
		slot = await UI.choose(names, Rect2(32, 88, 128, 56), max(slot, 0), 1, true, upd)
		if slot < 0:
			break
		if m.moves[slot].pp <= 0:
			await msg("기술의 남은 포인트가 없다!")
			continue
		break
	info.queue_free()
	return slot


# ------------------------------------------------------------------ 로컬(야생/트레이너) 진행
func _local_loop() -> String:
	while true:
		var act := {}
		if not core._forced_action(0).is_empty():
			act = {"type": "move", "slot": -2}
		else:
			act = await _choose_action()
		var enemy_act := core.ai_choose(1, kind == "trainer")
		if cfg.get("ghost", false):
			if act.type == "move":
				act = {"type": "scared"}
			enemy_act = {"type": "ghost"}
		elif cfg.get("safari", false):
			enemy_act = {"type": "safari_watch"}
		var evs := core.run_turn(act, enemy_act)
		await _play(evs)
		if core.ended == "run" or core.ended == "teleport":
			return "run"
		if core.ended == "caught":
			return await _caught()
		if cfg.get("safari", false) and int(G.flags.get("safari_balls", 0)) <= 0:
			await msg("사파리볼을 다 써 버렸다!")
			return "run"
		# 적 기절
		if core.mon(1).hp <= 0:
			await _give_exp(core.active[1])
			if core.alive_count(1) == 0:
				return await _win()
			var nxt := core._first_alive(1)
			await _play(core.switch_in(1, nxt))
			_mark_participant()
		# 내 포켓몬 기절
		if core.mon(0).hp <= 0:
			if core.alive_count(0) == 0:
				return await _lose()
			var idx := await _forced_switch()
			await _play(core.switch_in(0, idx))
			_mark_participant()
		if core.mon(1).hp > 0 and core.mon(0).hp > 0:
			_mark_participant()
	return "run"


func _mark_participant() -> void:
	if kind == "pvp":
		return
	var e: int = core.active[1]
	if not participants.has(e):
		participants[e] = []
	if not participants[e].has(core.active[0]):
		participants[e].append(core.active[0])


func _forced_switch() -> int:
	while true:
		var idx: int = await Menus.party_menu("forced", -1, parties[my_side])
		if idx >= 0 and parties[my_side][idx].hp > 0:
			return idx
		await msg("다음 포켓몬을 골라야 한다!")
	return 0


func _give_exp(enemy_idx: int) -> void:
	var e: Dictionary = core.parties[1][enemy_idx]
	var base: Dictionary = DB.pokemon[e.species]
	var getters: Array = participants.get(enemy_idx, [core.active[0]]).filter(func(i): return G.party[i].hp > 0)
	if getters.is_empty():
		return
	var total: int = base.exp * e.level / 7
	if kind == "trainer":
		total = total * 3 / 2
	var each := maxi(1, total / getters.size())
	for i in getters:
		var m: Dictionary = G.party[i]
		for st in ["hp", "atk", "def", "spd", "spc"]:
			m.sexp[st] = mini(65535, m.sexp[st] + base[st])
		await msg("%s{은} %d 경험치를 얻었다!" % [Mon.name_of(m), each])
		var ups := Mon.add_exp(m, each)
		for up in ups:
			leveled[i] = true
			if i == core.active[0]:
				_refresh_hud(my_side)
			Sound.jingle("Level_Up")
			await msg("%s의 레벨이 %d{으로} 올랐다!" % [Mon.name_of(m), up.level])
			for mv in up.learn:
				await learn_move_flow(m, mv)
	participants.erase(enemy_idx)


## 새 기술 배우기 (4개면 잊을 기술 선택)
static func learn_move_flow(m: Dictionary, mv: String) -> void:
	if Mon.has_move(m, mv):
		return
	var nm := Mon.name_of(m)
	if m.moves.size() < 4:
		Mon.learn_move(m, mv)
		await UI.say("%s{은} %s{을} 배웠다!" % [nm, DB.move_name(mv)], true)
		return
	while true:
		await UI.say("%s{은} %s{을} 배우고 싶어한다!\f하지만 %s{은} 기술을 4개 알고 있다!\f다른 기술을 잊게 할까?" % [nm, DB.move_name(mv), nm], true, false)
		if await UI.yes_no():
			var names := []
			for x in m.moves:
				names.append(DB.move_name(x.id))
			await UI.say("어느 기술을 잊게 할까?", true, false)
			var k: int = await UI.choose(names, Rect2(40, 40, 120, 56))
			if k >= 0:
				var old := DB.move_name(m.moves[k].id)
				Mon.learn_move(m, mv, k)
				await UI.say("1, 2, 그리고... 짠!\f%s{은} %s{을} 깨끗이 잊었다!\f그리고 %s{을} 배웠다!" % [nm, old, DB.move_name(mv)], true)
				return
		else:
			await UI.say("%s{을} 배우는 것을 포기할까?" % DB.move_name(mv), true, false)
			if await UI.yes_no():
				await UI.say("%s{은} %s{을} 배우지 않았다!" % [nm, DB.move_name(mv)], true)
				return


func _caught() -> String:
	Sound.jingle("Caught_Mon")
	var m: Dictionary = core.mon(1)
	m.ot = G.player_name
	m.status = m.status
	var first_time := not G.caught.has(m.species)
	var where := G.give_mon(m)
	if first_time:
		await msg("%s의 데이터가 새로 포켓몬 도감에 등록되었다!" % DB.mon_name(m.species))
	if where == "box":
		await msg("%s{은} PC의 박스로 전송되었다!" % Mon.name_of(m))
	return "caught"


func _win() -> String:
	if kind == "trainer":
		Sound.music("DefeatedGymLeader" if LEADERS.has(cfg["class"]) or cfg["class"] == "RIVAL3" else "DefeatedTrainer")
	elif kind == "wild":
		Sound.music("DefeatedWildMon")
	if kind == "trainer":
		trainer_pic.visible = true
		trainer_pic.position.x = 170
		var tw := create_tween()
		tw.tween_property(trainer_pic, "position:x", 100.0, 0.4)
		await tw.finished
		await msg("{PLAYER}{은} %s{와} 승부에서 이겼다!" % enemy_name)
		if cfg.get("end_text", "") != "":
			await msg(cfg.end_text)
		var last_lv: int = core.parties[1][-1].level
		var prize: int = enemy_trainer.money * last_lv / 100
		G.add_money(prize + payday)
		await msg("{PLAYER}{은} 상금으로 %d원을 받았다!" % (prize + payday))
	elif payday > 0:
		G.add_money(payday)
		await msg("{PLAYER}{은} %d원을 주웠다!" % payday)
	return "win"


func _lose() -> String:
	if kind == "trainer" and cfg.get("lose_text", "") != "":
		await msg(cfg.lose_text)
	await msg("{PLAYER}에게는 싸울 수 있는 포켓몬이 없다!")
	await msg("{PLAYER}{은} 눈앞이 캄캄해졌다!")
	return "lose"


func _evolutions() -> void:
	for i in leveled:
		if i >= G.party.size():
			continue
		var m: Dictionary = G.party[i]
		if m.hp <= 0:
			continue
		var to := Mon.level_evolution(m)
		if to != "":
			await evolve_scene(self, m, to)


## 진화 연출 (B로 취소 가능). 반환: 진화했는지
static func evolve_scene(host: Node, m: Dictionary, to: String) -> bool:
	var layer := CanvasLayer.new()
	layer.layer = 20
	host.add_child(layer)
	var bg := ColorRect.new()
	bg.color = Color.WHITE
	bg.size = Vector2(160, 144)
	layer.add_child(bg)
	var pic := TextureRect.new()
	pic.texture = Mon.front_tex(m.species)
	pic.position = Vector2(52, 20)
	layer.add_child(pic)
	var nm := Mon.name_of(m)
	await UI.say("어라...?\n%s의 모습이...!" % nm, true)
	var old_tex := pic.texture
	var new_tex := Mon.front_tex(to)
	var cancelled := false
	for i in 16:
		pic.texture = new_tex if i % 2 == 1 else old_tex
		await UI.wait(0.35 - i * 0.015)
		if Input.is_action_pressed("b"):
			cancelled = true
			break
	if cancelled:
		pic.texture = old_tex
		await UI.say("어라? %s의 변화가 멈췄다!" % nm, true)
	else:
		pic.texture = new_tex
		var old_name := DB.mon_name(m.species)
		Mon.evolve(m, to)
		G.register_caught(to)
		await UI.say("축하합니다! %s{은} %s{으로} 진화했다!" % [nm if m.nick != "" else old_name, DB.mon_name(to)], true)
		for pair in DB.pokemon[to].learn:
			if pair[0] == m.level:
				await learn_move_flow(m, pair[1])
	UI.close_box()
	layer.queue_free()
	return not cancelled


# ------------------------------------------------------------------ PvP
func _on_pvp(from: int, m: Dictionary) -> void:
	if from == peer:
		_inbox.append(m)


func _recv(type: String) -> Dictionary:
	while true:
		for i in _inbox.size():
			if _inbox[i].type == type or _inbox[i].type in ["disconnect", "forfeit"]:
				var m: Dictionary = _inbox[i]
				_inbox.remove_at(i)
				return m
		await get_tree().process_frame
	return {}


func _pvp_loop() -> String:
	while true:
		# 내 행동 선택
		var forced := false
		if authority:
			forced = not core._forced_action(0).is_empty()
		else:
			forced = cfg.get("_forced_me", false)
		var act := {"type": "move", "slot": -2} if forced else await _choose_action()
		if act.type == "forfeit":
			Net.send_pvp(peer, {"type": "forfeit"})
			await msg("{PLAYER}{은} 항복했다...")
			return "lose"
		UI.say("통신 대기 중...", true, false)
		var res := {}
		if authority:
			var other := await _recv("action")
			if other.type == "disconnect":
				return await _pvp_disconnected()
			if other.type == "forfeit":
				await msg("%s{은} 항복했다!" % enemy_name)
				return "win"
			var evs := core.run_turn(act, other.act)
			res = _turn_result(evs)
			Net.send_pvp(peer, res)
		else:
			Net.send_pvp(peer, {"type": "action", "act": act})
			res = await _recv("turn")
			if res.type == "disconnect":
				return await _pvp_disconnected()
			if res.type == "forfeit":
				await msg("%s{은} 항복했다!" % enemy_name)
				return "win"
		await _play(res.events)
		_apply_snapshot(res)
		cfg["_forced_me"] = res.forced[my_side]
		var w := await _pvp_check_end(res)
		if w != "":
			return w
		# 기절 교체
		if res.need[0] or res.need[1]:
			var my_pick := -1
			if res.need[my_side]:
				my_pick = await _forced_switch()
			UI.say("통신 대기 중...", true, false)
			var sw := {}
			if authority:
				var their_pick := -1
				if res.need[1]:
					var r := await _recv("switch")
					if r.type == "disconnect":
						return await _pvp_disconnected()
					their_pick = r.to
				var evs2 := []
				if my_pick >= 0:
					evs2 += core.switch_in(0, my_pick)
				if their_pick >= 0:
					evs2 += core.switch_in(1, their_pick)
				sw = _turn_result(evs2)
				Net.send_pvp(peer, sw)
			else:
				if my_pick >= 0:
					Net.send_pvp(peer, {"type": "switch", "to": my_pick})
				sw = await _recv("turn")
				if sw.type == "disconnect":
					return await _pvp_disconnected()
			await _play(sw.events)
			_apply_snapshot(sw)
			cfg["_forced_me"] = sw.forced[my_side]
	return "run"


func _turn_result(evs: Array) -> Dictionary:
	var need := [core.mon(0).hp <= 0 and core.alive_count(0) > 0, core.mon(1).hp <= 0 and core.alive_count(1) > 0]
	return {
		"type": "turn", "events": evs, "parties": core.parties, "active": core.active,
		"need": need, "forced": [not core._forced_action(0).is_empty(), not core._forced_action(1).is_empty()],
		"alive": [core.alive_count(0), core.alive_count(1)],
	}


func _apply_snapshot(res: Dictionary) -> void:
	if authority:
		return
	# 호스트 계산 결과로 로컬 표시용 파티를 덮어씀
	for s in 2:
		var src: Array = res.parties[s]
		for i in src.size():
			parties[s][i] = src[i]
	shown = [res.active[0], res.active[1]]


func _pvp_check_end(res: Dictionary) -> String:
	var alive: Array = res.alive
	if alive[my_side] == 0:
		await msg("{PLAYER}{은} %s에게 졌다..." % enemy_name)
		return "lose"
	if alive[1 - my_side] == 0:
		await msg("{PLAYER}{은} %s{와} 승부에서 이겼다!" % enemy_name)
		return "win"
	return ""


func _pvp_disconnected() -> String:
	await msg("통신이 끊어졌다!")
	return "run"
