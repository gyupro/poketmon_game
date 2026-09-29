class_name Story
extends RefCounted
## 스토리 스크립트 공통 도우미. 대사는 원작 텍스트 라벨(DB.text)로 부르고,
## 한국어 번역은 data/ko.json 에 같은 라벨로 넣는다.

const RIVAL_OFFSET := {"SQUIRTLE": 0, "BULBASAUR": 1, "CHARMANDER": 2}


static func say(label: String, keep_open := false) -> void:
	var t := DB.text(label)
	if t == "":
		push_warning("텍스트 없음: " + label)
		return
	await UI.say(t, keep_open)


## 예/아니오 질문. 라벨 텍스트를 띄운 뒤 선택
static func ask(label_or_text: String) -> bool:
	var t := DB.text(label_or_text) if _is_label(label_or_text) else label_or_text
	await UI.say(t, true, false)
	var r: bool = await UI.yes_no()
	UI.close_box()
	return r


## 라이벌 파티 번호 (라이벌이 고른 스타팅에 따라 +0/+1/+2)
static func rival_idx(base: int) -> int:
	return base + RIVAL_OFFSET.get(G.flags.get("rival_starter", "SQUIRTLE"), 0)


static func step_npc(a: Actor, dirs: Array, speed := 1.0) -> void:
	for d in dirs:
		await a.step(d, speed)


## 목표 칸 옆까지 (가로 먼저) 이동
static func walk_to(a: Actor, target: Vector2i, horizontal_first := true, speed := 1.0) -> void:
	var guard := 0
	while a.cell != target and guard < 64:
		guard += 1
		var d := target - a.cell
		var dir := Vector2i.ZERO
		if horizontal_first and d.x != 0 or d.y == 0:
			dir = Vector2i(signi(d.x), 0)
		else:
			dir = Vector2i(0, signi(d.y))
		await a.step(dir, speed)


## NPC 를 플레이어 바로 앞까지 걸어오게
static func approach(ow: Overworld, a: Actor, speed := 1.0) -> void:
	var guard := 0
	while (ow.player.cell - a.cell).length_squared() > 1 and guard < 64:
		guard += 1
		var d := ow.player.cell - a.cell
		var dir := Vector2i(signi(d.x), 0) if absi(d.x) > absi(d.y) or (absi(d.x) > 0 and absi(d.y) <= 1) else Vector2i(0, signi(d.y))
		if a.cell + dir == ow.player.cell:
			break
		await a.step(dir, speed)
	face_each_other(ow, a)


static func face_each_other(ow: Overworld, a: Actor) -> void:
	var d := ow.player.cell - a.cell
	if d.length_squared() == 1:
		a.set_facing(d)
		ow.player.set_facing(-d)
		G.facing = -d


static func player_walk(ow: Overworld, dirs: Array, speed := 1.0) -> void:
	for d in dirs:
		await ow.player.step(d, speed)
	G.pos = ow.player.cell
	G.facing = ow.player.facing
	Net.send_state()


## 트레이너 배틀 (원작 클래스/번호)
static func battle(ow: Overworld, cls: String, idx: int, end_label := "", lose_label := "", extra := {}) -> String:
	var cfg := {"kind": "trainer", "class": cls, "index": idx}
	if end_label != "":
		cfg["end_text"] = DB.text(end_label) if _is_label(end_label) else end_label
	if lose_label != "":
		cfg["lose_text"] = DB.text(lose_label) if _is_label(lose_label) else lose_label
	cfg.merge(extra)
	return await ow.start_battle(cfg)


## 이 맵의 일반 트레이너들을 모두 이긴 것으로 (체육관 관장 격파 후)
static func beat_map_trainers(ow: Overworld) -> void:
	for n in ow.map.npcs:
		if not n.has("trainer_class"):
			continue
		var ti: Dictionary = ow.map.texts.get(n.text, {})
		if ti.has("trainer"):
			G.set_flag(ti.trainer.event)


## 포켓몬 선물 받기 (파티가 가득 차면 박스로)
static func give_mon(species: String, level: int, nick_prompt := true) -> Dictionary:
	var m := Mon.create(species, level, G.player_name)
	var where := G.give_mon(m)
	Sound.jingle("Get_Key_Item")
	await UI.say("{PLAYER}{은} %s{을} 받았다!" % DB.mon_name(species))
	if nick_prompt:
		var nick := await UI.text_input("%s에게 별명을 지어 줄까? (빈칸이면 그대로)" % DB.mon_name(species), "", 10)
		if nick != "":
			m.nick = nick
	if where == "box":
		await UI.say("%s{은} PC의 박스로 전송되었다!" % Mon.name_of(m))
	return m


## 돈 지불. 부족하면 false
static func pay(amount: int) -> bool:
	if G.money < amount:
		return false
	G.add_money(-amount)
	Sound.sfx("Purchase")
	return true


static func has_mon(species: String) -> bool:
	for m in G.party:
		if m.species == species:
			return true
	return false


## NPC 교환 (원작 trades.asm 의 번호)
static func npc_trade(ow: Overworld, idx: int) -> void:
	var tr: Dictionary = DB.extra.trades[idx]
	var key := "trade:%d" % idx
	var set_n := {"TRADE_DIALOGSET_CASUAL": 1, "TRADE_DIALOGSET_EVOLUTION": 2, "TRADE_DIALOGSET_HAPPY": 3}.get(tr.dialog, 1)
	var give_name := DB.mon_name(tr.give)
	var get_name := DB.mon_name(tr.get)
	if G.flag(key):
		await UI.say(_trade_text("_AfterTrade%dText" % set_n, give_name, get_name))
		return
	await UI.say(_trade_text("_WannaTrade%dText" % set_n, give_name, get_name), true, false)
	if not await UI.yes_no():
		UI.close_box()
		await UI.say(_trade_text("_NoTrade%dText" % set_n, give_name, get_name))
		return
	UI.close_box()
	var i: int = await Menus.party_menu("select", -1)
	if i < 0:
		await UI.say(_trade_text("_NoTrade%dText" % set_n, give_name, get_name))
		return
	var mine: Dictionary = G.party[i]
	if mine.species != tr.give:
		await UI.say("음? 그건 %s{이} 아니잖아!\n%s{이} 있으면 다시 와 줘!" % [give_name, give_name])
		return
	var m := Mon.create(tr.get, mine.level, "NPC")
	m.nick = tr.nick
	G.party[i] = m
	G.register_caught(tr.get)
	G.set_flag(key)
	Sound.sfx("Trade_Machine")
	await UI.say("{PLAYER}{은} %s{와} %s{을} 교환했다!" % [give_name, get_name])
	await UI.say(_trade_text("_AfterTrade%dText" % set_n, give_name, get_name))
	var to := Mon.trade_evolution(m)
	if to != "":
		await Battle.evolve_scene(UI, m, to)


static func _trade_text(label: String, give_name: String, get_name: String) -> String:
	var t := DB.text(label)
	# 원작은 {RAM} 자리에 포켓몬 이름이 들어감 (1번째: 받을 것, 2번째: 줄 것)
	var parts := t.split("{RAM}")
	if parts.size() == 1:
		return t
	var names := [give_name, get_name]
	if label == "_AfterTrade1Text" or label == "_AfterTrade3Text":
		names = [get_name, give_name]
	var out := parts[0]
	for k in range(1, parts.size()):
		out += names[mini(k - 1, 1)] + parts[k]
	return out


## 텍스트 안의 {RAM} 을 차례로 치환
static func fill(label: String, values: Array) -> String:
	var t := DB.text(label) if _is_label(label) else label
	for v in values:
		var i1 := t.find("{RAM}")
		var i2 := t.find("{NUM}")
		var i := i1 if i2 < 0 or (i1 >= 0 and i1 < i2) else i2
		if i < 0:
			break
		t = t.substr(0, i) + str(v) + t.substr(i + 5)
	return t


static func _is_label(s: String) -> bool:
	return DB.texts_en.has(s) or DB.ko.has(s)
