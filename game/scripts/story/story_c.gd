class_name StoryC
extends RefCounted
## 스토리 3구간: 홍련섬(연구소 화석, 체육관 퀴즈, 포켓몬 저택 스위치), 쌍둥이섬 바위, 22·23번도로(라이벌, 배지 검문),
## 챔피언로드 바위 스위치, 사천왕과 챔피언, 전당 등록, 엔딩 이후(블루시티 동굴).

const E4_ROOMS := ["LORELEIS_ROOM", "BRUNOS_ROOM", "AGATHAS_ROOM"]
const E4_EVENTS := ["EVENT_BEAT_LORELEIS_ROOM_TRAINER_0", "EVENT_BEAT_BRUNOS_ROOM_TRAINER_0",
	"EVENT_BEAT_AGATHAS_ROOM_TRAINER_0", "EVENT_BEAT_LANCES_ROOM_TRAINER_0"]
# 체육관 퀴즈 문: [블록x, 블록y, 잠긴 블록]
const QUIZ_GATES := [[9, 3, 0x54], [6, 3, 0x54], [6, 6, 0x54], [3, 8, 0x5F], [2, 6, 0x54], [2, 3, 0x54]]
# 저택 스위치: 맵 -> [[x, y, 꺼짐 블록, 켜짐 블록]...]
const MANSION := {
	"POKEMON_MANSION_1F": [[12, 6, 0x0E, 0x2D], [8, 3, 0x2D, 0x0E], [10, 8, 0x2D, 0x0E], [13, 13, 0x2D, 0x0E]],
	"POKEMON_MANSION_2F": [[4, 2, 0x0E, 0x5F], [9, 4, 0x54, 0x0E], [3, 11, 0x5F, 0x0E]],
	"POKEMON_MANSION_3F": [[7, 2, 0x0E, 0x5F], [7, 5, 0x5F, 0x0E]],
	"POKEMON_MANSION_B1F": [[13, 8, 0x0E, 0x2D], [6, 11, 0x0E, 0x5F], [4, 3, 0x5F, 0x0E], [8, 8, 0x54, 0x0E]],
}
# 23번도로 검문: y 좌표 -> 배지
const ROUTE23 := {136: "CASCADEBADGE", 119: "THUNDERBADGE", 105: "RAINBOWBADGE", 96: "SOULBADGE",
	85: "MARSHBADGE", 56: "VOLCANOBADGE", 35: "EARTHBADGE"}
# 쌍둥이섬 구멍: 맵 -> [[구멍 좌표, 떨어질 바위(아래층 오브젝트)]...], 아래층
const SEAFOAM_HOLES := {
	"SEAFOAM_ISLANDS_1F": [[Vector2i(17, 6), "SEAFOAMISLANDSB1F_BOULDER1"], [Vector2i(24, 6), "SEAFOAMISLANDSB1F_BOULDER2"]],
	"SEAFOAM_ISLANDS_B1F": [[Vector2i(18, 6), "SEAFOAMISLANDSB2F_BOULDER1"], [Vector2i(23, 6), "SEAFOAMISLANDSB2F_BOULDER2"]],
	"SEAFOAM_ISLANDS_B2F": [[Vector2i(19, 6), "SEAFOAMISLANDSB3F_BOULDER5"], [Vector2i(22, 6), "SEAFOAMISLANDSB3F_BOULDER6"]],
	"SEAFOAM_ISLANDS_B3F": [[Vector2i(3, 16), "SEAFOAMISLANDSB4F_BOULDER1"], [Vector2i(6, 16), "SEAFOAMISLANDSB4F_BOULDER2"]],
}
const SEAFOAM_DOWN := {
	"SEAFOAM_ISLANDS_1F": ["SEAFOAM_ISLANDS_B1F", Vector2i(18, 7), Vector2i(23, 7)],
	"SEAFOAM_ISLANDS_B1F": ["SEAFOAM_ISLANDS_B2F", Vector2i(19, 7), Vector2i(22, 7)],
	"SEAFOAM_ISLANDS_B2F": ["SEAFOAM_ISLANDS_B3F", Vector2i(18, 7), Vector2i(19, 7)],
	"SEAFOAM_ISLANDS_B3F": ["SEAFOAM_ISLANDS_B4F", Vector2i(4, 14), Vector2i(5, 14)],
}
const FOSSILS := {"DOME_FOSSIL": "KABUTO", "HELIX_FOSSIL": "OMANYTE", "OLD_AMBER": "AERODACTYL"}


static func on_npc_spawn(_ow: Overworld, _a: Actor) -> void:
	pass


static func on_build(ow: Overworld) -> void:
	var id := ow.map_id
	if id == "CINNABAR_GYM":
		for i in QUIZ_GATES.size():
			if not _gate_open(ow, i):
				var g: Array = QUIZ_GATES[i]
				ow._apply_block(g[1] * ow.map.w + g[0], g[2])
	if MANSION.has(id):
		var on := G.flag("mansion_switch")
		for b in MANSION[id]:
			ow._apply_block(b[1] * ow.map.w + b[0], b[3] if on else b[2])
	if E4_ROOMS.has(id):
		var idx := E4_ROOMS.find(id)
		ow._apply_block(2, 0x05 if G.flag(E4_EVENTS[idx]) else 0x24)


static func _gate_open(ow: Overworld, i: int) -> bool:
	if G.flag("quiz_gate:%d" % i):
		return true
	var nerd_id := "CINNABARGYM_SUPER_NERD%d" % (i + 2)
	for n in ow.map.npcs:
		if n.id == nerd_id:
			var ti: Dictionary = ow.map.texts.get(n.text, {})
			if ti.has("trainer") and G.flag(ti.trainer.event):
				return true
	return false


static func can_warp(ow: Overworld, dest: String) -> bool:
	if dest == "CINNABAR_GYM" and not G.bag.has("SECRET_KEY"):
		await Story.say("_CinnabarIslandDoorIsLockedText")
		return false
	return true


static func on_enter(ow: Overworld) -> void:
	match ow.map_id:
		"LORELEIS_ROOM":
			var from = G.flags.get("warp_from")
			if from != null and from[0] == "INDIGO_PLATEAU_LOBBY":
				for e in E4_EVENTS:
					G.flags.erase(e)
				G.flags.erase("beat_champion_this_run")
				on_build(ow)
				await Story.player_walk(ow, [Vector2i.UP, Vector2i.UP, Vector2i.UP, Vector2i.UP])
		"CHAMPIONS_ROOM":
			if not G.flag("champion_battle_done"):
				await _champion(ow)
		"HALL_OF_FAME":
			await _hall_of_fame(ow)
		"CINNABAR_LAB_FOSSIL_ROOM":
			pass
	# 화석: 연구소를 나가면 부활 완료
	if ow.map_id == "CINNABAR_ISLAND" and G.flags.has("fossil_given"):
		G.set_flag("fossil_ready")


static func on_step(ow: Overworld) -> bool:
	var c := ow.player.cell
	match ow.map_id:
		"ROUTE_22":
			if c == Vector2i(29, 4) or c == Vector2i(29, 5):
				if G.flag("got_pokedex") and not G.flag("beat_route22_rival1"):
					await _route22_rival(ow, 1)
					return true
				if G.bag.has("EARTHBADGE") and not G.flag("beat_route22_rival2"):
					await _route22_rival(ow, 2)
					return true
		"ROUTE_22_GATE":
			if (c == Vector2i(4, 2) or c == Vector2i(5, 2)) and ow.player.facing == Vector2i.UP:
				if not G.bag.has("BOULDERBADGE"):
					await Story.say("_Route22GateGuardNoBoulderbadgeText")
					await Story.say("_Route22GateGuardICantLetYouPassText")
					await Story.player_walk(ow, [Vector2i.DOWN])
					return true
		"ROUTE_23":
			if ROUTE23.has(c.y) and ow.player.facing == Vector2i.UP and not (c.y == 35 and c.x >= 14):
				var b: String = ROUTE23[c.y]
				if not G.flag("passed:" + b):
					var bn := DB.item_name(b)
					if G.bag.has(b):
						G.set_flag("passed:" + b)
						await UI.say(Story.fill("_Route23OhThatIsTheBadgeText", [bn, bn]))
						await Story.say("_Route23GoRightAheadText")
					else:
						await UI.say(Story.fill("_Route23YouDontHaveTheBadgeYetText", [bn, bn]))
						await Story.player_walk(ow, [Vector2i.DOWN])
						return true
		"LORELEIS_ROOM", "BRUNOS_ROOM", "AGATHAS_ROOM":
			if c.y >= 10 and (c.x == 4 or c.x == 5) and ow.player.facing == Vector2i.DOWN:
				await UI.say("누군가의 목소리:\n도망치지 마라!")
				await Story.player_walk(ow, [Vector2i.UP])
				return true
		"VICTORY_ROAD_3F":
			if c == Vector2i(23, 15):
				await ow.teleport_to("VICTORY_ROAD_2F", Vector2i(22, 16), Vector2i.DOWN)
				return true
	# 쌍둥이섬 구멍에 빠지기
	if SEAFOAM_DOWN.has(ow.map_id):
		var holes: Array = SEAFOAM_HOLES[ow.map_id]
		for i in holes.size():
			if c == holes[i][0]:
				var d: Array = SEAFOAM_DOWN[ow.map_id]
				Sound.sfx("Ledge")
				await ow.teleport_to(d[0], d[1 + i], Vector2i.DOWN)
				return true
	return false


## 괴력으로 바위를 민 뒤
static func on_boulder(ow: Overworld, b: Actor) -> void:
	var id := ow.map_id
	var c := b.cell
	match id:
		"VICTORY_ROAD_1F":
			if c == Vector2i(17, 13) and not G.flag("vr1_switch"):
				G.set_flag("vr1_switch")
				Sound.sfx("Go_Inside")
				ow.set_block_xy(4, 6, 0x1D)
		"VICTORY_ROAD_2F":
			if c == Vector2i(1, 16) and not G.flag("vr2_switch1"):
				G.set_flag("vr2_switch1")
				Sound.sfx("Go_Inside")
				ow.set_block_xy(3, 4, 0x15)
			elif c == Vector2i(9, 16) and not G.flag("vr2_switch2"):
				G.set_flag("vr2_switch2")
				Sound.sfx("Go_Inside")
				ow.set_block_xy(11, 7, 0x1D)
		"VICTORY_ROAD_3F":
			if c == Vector2i(3, 5) and not G.flag("vr3_switch"):
				G.set_flag("vr3_switch")
				Sound.sfx("Go_Inside")
				ow.set_block_xy(3, 5, 0x1D)
			elif c == Vector2i(23, 15):
				ow.remove_npc(b.data.id)
				G.set_object_visible("VICTORYROAD2F_BOULDER3", true)
	if SEAFOAM_HOLES.has(id):
		for h in SEAFOAM_HOLES[id]:
			if c == h[0]:
				Sound.sfx("Ledge")
				ow.remove_npc(b.data.id)
				G.set_object_visible(h[1], true)
				if id == "SEAFOAM_ISLANDS_B3F":
					G.set_flag("seafoam_b4f_boulder1" if h[1].ends_with("1") else "seafoam_b4f_boulder2")
				await UI.say("바위가 구멍으로 떨어졌다!")


## 일반 트레이너를 이긴 직후
static func on_trainer_beaten(ow: Overworld, a: Actor) -> void:
	if E4_ROOMS.has(ow.map_id):
		Sound.sfx("Go_Inside")
		ow._apply_block(2, 0x05)


static func on_hidden(ow: Overworld, h: Dictionary) -> bool:
	var hd: String = h.handler
	if hd.begins_with("Mansion") and hd.ends_with("Switches"):
		if await Story.ask("_PokemonMansion1FSwitchText"):
			await Story.say("_PokemonMansion1FSwitchPressedText")
			G.set_flag("mansion_switch", not G.flag("mansion_switch"))
			Sound.sfx("Go_Inside")
			var on := G.flag("mansion_switch")
			for b in MANSION.get(ow.map_id, []):
				ow._apply_block(b[1] * ow.map.w + b[0], b[3] if on else b[2])
		else:
			await Story.say("_PokemonMansion1FSwitchNotPressedText")
		return true
	if hd == "PrintCinnabarQuiz":
		if ow.player.facing != Vector2i.UP:
			return true
		var arg: String = h.arg
		var answer := 0 if arg.contains("FALSE") else 1
		var gate := int(arg.substr(arg.length() - 1)) - 1
		await Story.say("_CinnabarGymQuizIntroText")
		var yes := await Story.ask("_CinnabarQuizQuestionsText%d" % (gate + 1))
		if (0 if yes else 1) == answer:
			Sound.jingle("Get_Item1")
			await Story.say("_CinnabarGymQuizCorrectText")
			if not G.flag("quiz_gate:%d" % gate):
				G.set_flag("quiz_gate:%d" % gate)
				Sound.sfx("Go_Inside")
				var g: Array = QUIZ_GATES[gate]
				var bi: int = g[1] * ow.map.w + g[0]
				ow._apply_block(bi, DB.maps["CINNABAR_GYM"].blk[bi])
		else:
			Sound.sfx("Denied")
			await Story.say("_CinnabarGymQuizIncorrectText")
			var nerd := ow.find_npc("CINNABARGYM_SUPER_NERD%d" % (gate + 2))
			if nerd:
				var info := ow.trainer_info(nerd)
				if not info.is_empty() and not G.flag(info.event):
					await ow.engage_trainer(nerd, info)
					if G.flag(info.event):
						var g2: Array = QUIZ_GATES[gate]
						var bi2: int = g2[1] * ow.map.w + g2[0]
						ow._apply_block(bi2, DB.maps["CINNABAR_GYM"].blk[bi2])
		return true
	return false


static func on_talk(ow: Overworld, a: Actor) -> bool:
	var id: String = a.data.get("id", "")
	match id:
		"CINNABARLABFOSSILROOM_SCIENTIST1":
			await _fossil_scientist()
		"CINNABARLABMETRONOMEROOM_SCIENTIST1":
			if G.flag("gift:TM_METRONOME"):
				await Story.say("_CinnabarLabMetronomeRoomScientist1TM35ExplanationText")
			else:
				await Story.say("_CinnabarLabMetronomeRoomScientist1Text")
				G.set_flag("gift:TM_METRONOME")
				G.add_item("TM_METRONOME")
				Sound.jingle("Get_Item1")
				await UI.say(Story.fill("_CinnabarLabMetronomeRoomScientist1ReceivedTM35Text", [DB.item_name("TM_METRONOME")]))
				await Story.say("_CinnabarLabMetronomeRoomScientist1TM35ExplanationText")
		"VIRIDIANCITY_FISHER":
			if G.flag("gift:TM_DREAM_EATER"):
				await Story.say("_ViridianCityFisherTM42ExplanationText")
			else:
				await Story.say("ViridianCityFisherYouCanHaveThisText")
				G.set_flag("gift:TM_DREAM_EATER")
				G.add_item("TM_DREAM_EATER")
				Sound.jingle("Get_Item1")
				await Story.say("_ViridianCityFisherReceivedTM42Text")
				await Story.say("_ViridianCityFisherTM42ExplanationText")
		"VIRIDIANCITY_GAMBLER1":
			await Story.say("_ViridianCityGambler1GymLeaderReturnedText" if G.badge_count() >= 7 else "_ViridianCityGambler1GymAlwaysClosedText")
		"ROUTE22_RIVAL1", "ROUTE22_RIVAL2":
			pass
		"ROUTE22GATE_GUARD":
			await Story.say("_Route22GateGuardGoRightAheadText" if G.bag.has("BOULDERBADGE") else "_Route22GateGuardNoBoulderbadgeText")
		"LANCESROOM_LANCE":
			return false
		_:
			if id.begins_with("ROUTE23_GUARD") or id.begins_with("ROUTE23_SWIMMER"):
				await UI.say("여기는 포켓몬 리그로 가는 길이다.\n배지를 가진 트레이너만 지나갈 수 있다!")
				return true
			return false
	return true


# ------------------------------------------------------------------ 홍련섬 연구소 화석
static func _fossil_scientist() -> void:
	if G.flags.has("fossil_given"):
		if not G.flag("fossil_ready"):
			await Story.say("_CinnabarLabFossilRoomScientist1GoForAWalkText")
			return
		var sp: String = FOSSILS[G.flags.fossil_given]
		await UI.say(Story.fill("_CinnabarLabFossilRoomScientist1FossilIsBackToLifeText", [DB.mon_name(sp)]))
		G.flags.erase("fossil_given")
		G.flags.erase("fossil_ready")
		await Story.give_mon(sp, 30)
		return
	await Story.say("_CinnabarLabFossilRoomScientist1Text")
	var have := []
	for f in FOSSILS:
		if G.bag.has(f):
			have.append(f)
	if have.is_empty():
		await Story.say("_CinnabarLabFossilRoomScientist1NoFossilsText")
		return
	var names := []
	for f in have:
		names.append(DB.item_name(f))
	var c: int = await UI.choose(names, Rect2(56, 40, 104, names.size() * 14 + 10))
	if c < 0:
		await Story.say("_CinnabarLabFossilRoomScientist1ComeAgainText")
		return
	var fossil: String = have[c]
	var sp2: String = FOSSILS[fossil]
	await UI.say(Story.fill("_CinnabarLabFossilRoomScientist1SeesFossilText", [DB.item_name(fossil), DB.mon_name(sp2)]), true, false)
	var yes: bool = await UI.yes_no()
	UI.close_box()
	if not yes:
		await Story.say("_CinnabarLabFossilRoomScientist1ComeAgainText")
		return
	await UI.say(Story.fill("_CinnabarLabFossilRoomScientist1TakesFossilText", [DB.item_name(fossil)]))
	G.remove_item(fossil)
	G.flags["fossil_given"] = fossil
	await Story.say("_CinnabarLabFossilRoomScientist1GoForAWalkText2")


# ------------------------------------------------------------------ 22번도로 라이벌
static func _route22_rival(ow: Overworld, n: int) -> void:
	var rid := "ROUTE22_RIVAL%d" % n
	Sound.music("MeetRival")
	var r := ow.show_npc(rid)
	if r == null:
		return
	await ow.show_emote(r)
	r.teleport(Vector2i(ow.player.cell.x - 4, ow.player.cell.y))
	while r.cell.x < ow.player.cell.x - 1:
		await r.step(Vector2i.RIGHT)
	Story.face_each_other(ow, r)
	await Story.say("_Route22RivalBeforeBattleText%d" % n)
	var res: String
	if n == 1:
		res = await Story.battle(ow, "RIVAL1", Story.rival_idx(4), "_Route22Rival1DefeatedText", "_Route22Rival1VictoryText", {"no_blackout": true})
	else:
		res = await Story.battle(ow, "RIVAL2", Story.rival_idx(10), "_Route22Rival2DefeatedText", "_Route22Rival2VictoryText")
	G.set_flag("beat_route22_rival%d" % n)
	if n == 1 and res == "lose":
		G.heal_party()
	Sound.music("MeetRival")
	await Story.say("_Route22RivalAfterBattleText%d" % n)
	for i in 5:
		await r.step(Vector2i.RIGHT if i < 2 else Vector2i.DOWN)
	ow.remove_npc(rid)
	Sound.map_music(ow.map_id)


# ------------------------------------------------------------------ 챔피언 / 전당
static func _champion(ow: Overworld) -> void:
	var r := ow.find_npc("CHAMPIONSROOM_RIVAL")
	await Story.player_walk(ow, [Vector2i.UP, Vector2i.RIGHT, Vector2i.UP, Vector2i.UP, Vector2i.UP])
	if r:
		Story.face_each_other(ow, r)
	Sound.music("MeetRival")
	await Story.say("_ChampionsRoomRivalIntroText")
	var res := await Story.battle(ow, "RIVAL3", Story.rival_idx(1), "_RivalDefeatedText", "_RivalVictoryText")
	if res != "win":
		return
	G.set_flag("champion_battle_done")
	await Story.say("_ChampionsRoomRivalAfterBattleText")
	Sound.music("MeetProfOak")
	await Story.say("_ChampionsRoomOakText")
	var oak := ow.show_npc("CHAMPIONSROOM_OAK")
	if oak:
		oak.teleport(Vector2i(3, 7))
		for i in 4:
			await oak.step(Vector2i.UP)
		ow.player.set_facing(Vector2i.LEFT)
	await Story.say("_ChampionsRoomOakCongratulatesPlayerText")
	if oak:
		oak.set_facing(Vector2i.RIGHT)
	await Story.say("_ChampionsRoomOakDisappointedWithRivalText")
	if oak:
		oak.set_facing(Vector2i.DOWN)
	await Story.say("_ChampionsRoomOakComeWithMeText")
	await UI.fade_out(0.5)
	ow.remove_npc("CHAMPIONSROOM_OAK")
	await ow.teleport_to("HALL_OF_FAME", Vector2i(5, 7), Vector2i.UP, false)
	await UI.fade_in(0.5)
	await _hall_of_fame(ow)


static func _hall_of_fame(ow: Overworld) -> void:
	if G.flag("hof_done_now"):
		return
	G.set_flag("hof_done_now")
	Sound.music("HallOfFame")
	await Story.player_walk(ow, [Vector2i.UP, Vector2i.UP, Vector2i.UP, Vector2i.UP])
	await Story.say("_HallOfFameOakText")
	# 전당 등록 연출
	var layer := CanvasLayer.new()
	layer.layer = 30
	ow.add_child(layer)
	var bg := ColorRect.new()
	bg.color = Color.WHITE
	bg.size = Vector2(160, 144)
	layer.add_child(bg)
	var pic := TextureRect.new()
	pic.position = Vector2(52, 16)
	layer.add_child(pic)
	var lbl := GBBox.label("", Vector2(8, 96))
	layer.add_child(lbl)
	for m in G.party:
		pic.texture = Mon.front_tex(m.species)
		lbl.text = "%s  Lv%d\n%s" % [Mon.name_of(m), m.level, DB.mon_name(m.species)]
		Sound.cry(m.species)
		await UI.wait(2.2)
	pic.texture = DB.tex("res://assets/misc/red_front.png")
	lbl.text = "%s\n포켓몬 리그 챔피언!" % G.player_name
	await UI.wait(2.5)
	var hof: Array = G.flags.get("hall_of_fame", [])
	var team := []
	for m in G.party:
		team.append([m.species, m.level, Mon.name_of(m)])
	hof.append(team)
	G.flags["hall_of_fame"] = hof
	G.set_flag("champion")
	# 블루시티 동굴 입구를 막던 사람이 비킴
	G.set_object_visible("CERULEANCITY_SUPER_NERD3", false)
	G.save_game()
	await _credits(layer, lbl, pic)
	layer.queue_free()
	G.flags.erase("hof_done_now")
	G.flags.erase("champion_battle_done")
	for e in E4_EVENTS:
		G.flags.erase(e)
	G.heal_party()
	G.heal_map = "REDS_HOUSE_1F"
	G.heal_pos = Vector2i(5, 5)
	G.flags["heal_outdoor"] = "PALLET_TOWN"
	await ow.teleport_to("REDS_HOUSE_2F", Vector2i(3, 6), Vector2i.DOWN)
	G.save_game()
	await UI.say("{PLAYER}의 모험은 계속된다...\f(블루시티 서쪽 동굴에 강력한 포켓몬이 있다는 소문이...)")


static func _credits(layer: CanvasLayer, lbl: Label, pic: TextureRect) -> void:
	Sound.music("Credits")
	var lines := [
		"포켓몬스터 레드 온라인", "원작: GAME FREAK / Nintendo", "역어셈블리: pret/pokered",
		"Godot 이식판", "플레이어: " + G.player_name, "함께 모험한 포켓몬들", "THE END",
	]
	var mons := DB.dex_order.duplicate()
	mons.shuffle()
	for i in lines.size():
		lbl.text = lines[i]
		pic.texture = Mon.front_tex(mons[i])
		await UI.wait(3.0)
	await UI.fade_out(1.0)
	Sound.stop_music()
	await UI.fade_in(0.1)
