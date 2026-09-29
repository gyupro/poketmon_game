class_name StoryB
extends RefCounted
## 스토리 2구간: 무지개시티(게임코너/로켓단 아지트/백화점), 포켓몬타워와 후지 노인, 노랑시티(관문, 실프주식회사, 격투도장),
## 연분홍시티(사파리존, 원장), 사이클링로드, 엘리베이터, 각종 선물 NPC.

const TOWER_MAPS := ["POKEMON_TOWER_3F", "POKEMON_TOWER_4F", "POKEMON_TOWER_5F", "POKEMON_TOWER_6F", "POKEMON_TOWER_7F"]
const SAFARI_MAPS := ["SAFARI_ZONE_CENTER", "SAFARI_ZONE_EAST", "SAFARI_ZONE_NORTH", "SAFARI_ZONE_WEST",
	"SAFARI_ZONE_CENTER_REST_HOUSE", "SAFARI_ZONE_EAST_REST_HOUSE", "SAFARI_ZONE_NORTH_REST_HOUSE",
	"SAFARI_ZONE_WEST_REST_HOUSE", "SAFARI_ZONE_SECRET_HOUSE"]
const DRINKS := ["FRESH_WATER", "SODA_POP", "LEMONADE"]
# 관문 경비원: 맵 -> 막히는 좌표
const SAFFRON_GATES := {
	"ROUTE_5_GATE": [Vector2i(3, 3), Vector2i(4, 3)], "ROUTE_6_GATE": [Vector2i(3, 2), Vector2i(4, 2)],
	"ROUTE_7_GATE": [Vector2i(3, 3), Vector2i(3, 4)], "ROUTE_8_GATE": [Vector2i(2, 3), Vector2i(2, 4)],
}
const ELEVATORS := {
	"CELADON_MART_ELEVATOR": [["1F", 5, "CELADON_MART_1F"], ["2F", 2, "CELADON_MART_2F"], ["3F", 2, "CELADON_MART_3F"],
		["4F", 2, "CELADON_MART_4F"], ["5F", 2, "CELADON_MART_5F"]],
	"ROCKET_HIDEOUT_ELEVATOR": [["B1F", 4, "ROCKET_HIDEOUT_B1F"], ["B2F", 4, "ROCKET_HIDEOUT_B2F"], ["B4F", 2, "ROCKET_HIDEOUT_B4F"]],
	"SILPH_CO_ELEVATOR": [["1F", 3, "SILPH_CO_1F"], ["2F", 2, "SILPH_CO_2F"], ["3F", 2, "SILPH_CO_3F"], ["4F", 2, "SILPH_CO_4F"],
		["5F", 2, "SILPH_CO_5F"], ["6F", 2, "SILPH_CO_6F"], ["7F", 2, "SILPH_CO_7F"], ["8F", 2, "SILPH_CO_8F"],
		["9F", 2, "SILPH_CO_9F"], ["10F", 2, "SILPH_CO_10F"], ["11F", 1, "SILPH_CO_11F"]],
}
# 실프 카드키 문: [블록x, 블록y, 잠긴 블록]
const SILPH_GATES := {
	"SILPH_CO_2F": [[2, 2, 0x54], [2, 5, 0x54]], "SILPH_CO_3F": [[4, 4, 0x5F], [8, 4, 0x5F]],
	"SILPH_CO_4F": [[2, 6, 0x54], [6, 4, 0x54]], "SILPH_CO_5F": [[3, 2, 0x5F], [3, 6, 0x5F], [7, 5, 0x5F]],
	"SILPH_CO_6F": [[2, 6, 0x5F]], "SILPH_CO_7F": [[5, 3, 0x54], [10, 2, 0x54], [10, 6, 0x54]],
	"SILPH_CO_8F": [[3, 4, 0x5F]], "SILPH_CO_9F": [[1, 4, 0x5F], [9, 2, 0x54], [9, 5, 0x54], [5, 6, 0x5F]],
	"SILPH_CO_10F": [[5, 4, 0x54]], "SILPH_CO_11F": [[3, 6, 0x20]],
}
const SAFFRON_ROCKETS := ["SAFFRONCITY_ROCKET1", "SAFFRONCITY_ROCKET2", "SAFFRONCITY_ROCKET3", "SAFFRONCITY_ROCKET4",
	"SAFFRONCITY_ROCKET5", "SAFFRONCITY_ROCKET6", "SAFFRONCITY_ROCKET7", "SAFFRONCITY_ROCKET8", "SAFFRONCITY_ROCKET9"]
const SAFFRON_CIVILIANS := ["SAFFRONCITY_SCIENTIST", "SAFFRONCITY_SILPH_WORKER_M", "SAFFRONCITY_SILPH_WORKER_F",
	"SAFFRONCITY_GENTLEMAN", "SAFFRONCITY_PIDGEOT", "SAFFRONCITY_ROCKER"]
const PRIZES := [
	[["ABRA", 180, 9], ["CLEFAIRY", 500, 8], ["NIDORINA", 1200, 17]],
	[["DRATINI", 2800, 18], ["SCYTHER", 5500, 25], ["PORYGON", 9999, 26]],
	[["TM_DRAGON_RAGE", 3300, 0], ["TM_HYPER_BEAM", 5500, 0], ["TM_SUBSTITUTE", 7700, 0]],
]
const VENDING := [["FRESH_WATER", 200], ["SODA_POP", 300], ["LEMONADE", 350]]
const SIMPLE_TM_GIFTS := {
	# NPC id: [플래그용 아이템, 받기 전 대사, 받음 대사, 설명 대사]
	"MRPSYCHICSHOUSE_MR_PSYCHIC": ["TM_PSYCHIC_M", "_MrPsychicsHouseMrPsychicYouWantedThisText", "_MrPsychicsHouseMrPsychicReceivedTM29Text", "_MrPsychicsHouseMrPsychicTM29ExplanationText"],
	"ROUTE12GATE2F_BRUNETTE_GIRL": ["TM_SWIFT", "_Route12Gate2FBrunetteGirlYouCanHaveThisText", "_Route12Gate2FBrunetteGirlReceivedTM39Text", "_Route12Gate2FBrunetteGirlTM39ExplanationText"],
	"CELADONMART3F_CLERK": ["TM_COUNTER", "_CeladonMart3FClerkTM18PreReceiveText", "_CeladonMart3FClerkReceivedTM18Text", "_CeladonMart3FClerkTM18ExplanationText"],
	"ROUTE16FLYHOUSE_BRUNETTE_GIRL": ["HM_FLY", "_Route16FlyHouseBrunetteGirlText", "_Route16FlyHouseBrunetteGirlReceivedHM02Text", "_Route16FlyHouseBrunetteGirlHM02ExplanationText"],
	"SAFARIZONESECRETHOUSE_FISHING_GURU": ["HM_SURF", "_SafariZoneSecretHouseFishingGuruYouHaveWonText", "_SafariZoneSecretHouseFishingGuruReceivedHM03Text", "_SafariZoneSecretHouseFishingGuruHM03ExplanationText"],
	"SILPHCO2F_SILPH_WORKER_F": ["TM_SELFDESTRUCT", "SilphCo2FSilphWorkerFPleaseTakeThisText", "_SilphCo2FSilphWorkerFReceivedTM36Text", "_SilphCo2FSilphWorkerFTM36ExplanationText"],
}


static func on_npc_spawn(_ow: Overworld, _a: Actor) -> void:
	pass


static func on_build(ow: Overworld) -> void:
	# 게임코너 지하 계단(포스터 스위치 전에는 막힘)
	if ow.map_id == "GAME_CORNER" and not G.flag("found_rocket_hideout"):
		ow._apply_block(2 * ow.map.w + 8, 0x2A)
	# 실프 카드키 문
	if SILPH_GATES.has(ow.map_id):
		var gates: Array = SILPH_GATES[ow.map_id]
		for i in gates.size():
			if not G.flag("silph_door:%s:%d" % [ow.map_id, i]):
				ow._apply_block(gates[i][1] * ow.map.w + gates[i][0], gates[i][2])
	# 엘리베이터 목적지
	if ELEVATORS.has(ow.map_id):
		var from = G.flags.get("warp_from")
		if from != null and from[0] != ow.map_id:
			G.flags["elev:" + ow.map_id] = from
		var dest = G.flags.get("elev:" + ow.map_id)
		if dest != null:
			for w in ow.map.warps:
				w.map = dest[0]
				w.warp = int(dest[1])


## 실프주식회사 카드키 문: 앞 칸이 잠긴 문 블록이면 카드키로 연다
static func try_card_key(ow: Overworld) -> bool:
	if not SILPH_GATES.has(ow.map_id):
		return false
	var front := ow.player.cell + ow.player.facing
	var gates: Array = SILPH_GATES[ow.map_id]
	for i in gates.size():
		var g: Array = gates[i]
		if front.x / 2 != g[0] or front.y / 2 != g[1]:
			continue
		var key := "silph_door:%s:%d" % [ow.map_id, i]
		if G.flag(key):
			return false
		if not G.bag.has("CARD_KEY"):
			await Story.say("_CardKeyFailText")
			return true
		Sound.jingle("Get_Item1")
		await Story.say("_CardKeySuccessText1")
		G.set_flag(key)
		var bi: int = g[1] * ow.map.w + g[0]
		ow._apply_block(bi, DB.maps[ow.map_id].blk[bi])
		Sound.sfx("Go_Inside")
		await Story.say("_CardKeySuccessText2")
		return true
	return false


static func can_warp(ow: Overworld, dest: String) -> bool:
	# 사파리존 게이트에서 존으로 나가는 것은 스크립트가 처리
	return true


static func on_enter(ow: Overworld) -> void:
	if ow.map_id == "SAFARI_ZONE_GATE" and G.flag("safari") and ow.player.cell.y <= 2:
		# 사파리존에서 돌아옴
		G.flags.erase("safari")
		G.flags.erase("safari_balls")
		await Story.say("_SafariZoneGateSafariZoneWorker1GoodHaulComeAgainText")
		await Story.player_walk(ow, [Vector2i.DOWN])
	if ow.map_id == "SAFFRON_CITY":
		_apply_saffron(ow)
	if ow.map_id == "ROCKET_HIDEOUT_B4F":
		_check_lift_key(ow)


static func _apply_saffron(ow: Overworld) -> void:
	if not G.flag("beat_silph_giovanni"):
		return
	for id in SAFFRON_ROCKETS:
		if ow.find_npc(id):
			ow.remove_npc(id)
	for id in SAFFRON_CIVILIANS:
		if not G.object_visible(id):
			ow.show_npc(id)


static func _check_lift_key(ow: Overworld) -> void:
	var r := ow.find_npc("ROCKETHIDEOUTB4F_ROCKET3")
	if r and G.flag(ow.trainer_info(r).get("event", "?")) and not G.flag("got:ROCKETHIDEOUTB4F_LIFT_KEY"):
		if not G.object_visible("ROCKETHIDEOUTB4F_LIFT_KEY"):
			ow.show_npc("ROCKETHIDEOUTB4F_LIFT_KEY")


static func on_step(ow: Overworld) -> bool:
	var c := ow.player.cell
	# 사파리존 걸음 수
	if is_safari_battle(ow.map_id):
		G.flags["safari_steps"] = int(G.flags.get("safari_steps", 500)) - 1
		if int(G.flags.safari_steps) <= 0:
			await _safari_over(ow)
			return true
	if SAFFRON_GATES.has(ow.map_id) and c in SAFFRON_GATES[ow.map_id] and not G.flag("gave_guard_drink"):
		await _saffron_guard(ow)
		return true
	match ow.map_id:
		"ROUTE_16_GATE_1F", "ROUTE_18_GATE_1F":
			var xs := [Vector2i(4, 7), Vector2i(4, 8), Vector2i(4, 9), Vector2i(4, 10)] if ow.map_id == "ROUTE_16_GATE_1F" else [Vector2i(4, 3), Vector2i(4, 4), Vector2i(4, 5), Vector2i(4, 6)]
			if c in xs and not G.bag.has("BICYCLE"):
				await Story.say("_Route16Gate1FGuardNoPedestriansAllowedText" if ow.map_id == "ROUTE_16_GATE_1F" else "_Route18Gate1FGuardYouNeedABicycleText")
				await Story.player_walk(ow, [-ow.player.facing])
				return true
		"SAFARI_ZONE_GATE":
			if (c == Vector2i(3, 2) or c == Vector2i(4, 2)) and ow.player.facing == Vector2i.UP and not G.flag("safari"):
				await _safari_enter(ow)
				return true
		"POKEMON_TOWER_2F":
			if not G.flag("beat_tower_rival") and (c == Vector2i(15, 5) or c == Vector2i(14, 6)):
				await _tower_rival(ow)
				return true
		"POKEMON_TOWER_5F":
			if c in [Vector2i(10, 8), Vector2i(11, 8), Vector2i(10, 9), Vector2i(11, 9)]:
				if not G.flag("tower5_healed"):
					G.set_flag("tower5_healed")
					G.heal_party()
					await Story.say("_PokemonTower5FPurifiedZoneText")
				return false
			G.flags.erase("tower5_healed")
		"POKEMON_TOWER_6F":
			if c == Vector2i(10, 16) and not G.flag("beat_ghost_marowak"):
				await _ghost_marowak(ow)
				return true
		"SILPH_CO_7F":
			if not G.flag("beat_silph_rival") and (c == Vector2i(3, 2) or c == Vector2i(3, 3)):
				await _silph_rival(ow)
				return true
		"SILPH_CO_11F":
			if not G.flag("beat_silph_giovanni") and (c == Vector2i(6, 13) or c == Vector2i(7, 12)):
				await _silph_giovanni(ow)
				return true
		"ROCKET_HIDEOUT_B4F":
			_check_lift_key(ow)
	return false


static func on_sign(ow: Overworld, s: Dictionary) -> bool:
	var t: String = s.text
	if ELEVATORS.has(ow.map_id) and (t.contains("ELEVATOR") or t.begins_with("TEXT_CELADONMARTELEVATOR") or t.begins_with("TEXT_ROCKETHIDEOUTELEVATOR")):
		await _elevator(ow)
		return true
	if t == "TEXT_GAMECORNER_POSTER":
		if G.flag("found_rocket_hideout"):
			return false
		await Story.say("_GameCornerPosterSwitchBehindPosterText")
		Sound.sfx("Go_Inside")
		G.set_flag("found_rocket_hideout")
		ow._apply_block(2 * ow.map.w + 8, DB.maps["GAME_CORNER"].blk[2 * ow.map.w + 8])
		return true
	if t.begins_with("TEXT_CELADONMARTROOF_VENDING_MACHINE"):
		await _vending()
		return true
	if t.begins_with("TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_"):
		await _prize_vendor(int(t.substr(t.length() - 1)) - 1)
		return true
	return false


static func on_hidden(ow: Overworld, h: Dictionary) -> bool:
	match h.handler:
		"StartSlotMachine":
			match h.arg:
				"SLOTS_OUTOFORDER":
					await Story.say("_GameCornerOutOfOrderText")
				"SLOTS_OUTTOLUNCH":
					await Story.say("_GameCornerOutToLunchText")
				"SLOTS_SOMEONESKEYS":
					await Story.say("_GameCornerSomeonesKeysText")
				_:
					await _slots()
			return true
		"HiddenCoins":
			var key := "hidden:%s:%d:%d" % [ow.map_id, h.x, h.y]
			if G.flag(key) or not G.bag.has("COIN_CASE"):
				return true
			G.set_flag(key)
			var n := int(h.arg.split("+")[1].strip_edges())
			G.flags["coins"] = mini(9999, int(G.flags.get("coins", 0)) + n)
			Sound.jingle("Get_Item1")
			await UI.say("{PLAYER}{은} 코인 %d개를 찾았다!" % n)
			return true
	return false


static func on_talk(ow: Overworld, a: Actor) -> bool:
	var id: String = a.data.get("id", "")
	if SIMPLE_TM_GIFTS.has(id):
		await _simple_gift(ow, SIMPLE_TM_GIFTS[id])
		return true
	if id.begins_with("SAFFRON_GATE") or (SAFFRON_GATES.has(ow.map_id) and id.ends_with("GUARD")):
		if G.flag("gave_guard_drink"):
			await Story.say("_SaffronGateGuardThanksForTheDrinkText")
		else:
			await _saffron_guard(ow)
		return true
	match id:
		"GAMECORNER_CLERK1":
			await _buy_coins()
		"GAMECORNER_FISHING_GURU":
			await _coin_gift("coins10", 10, "_GameCornerFishingGuruWantToPlayText", "_GameCornerFishingGuruReceived10CoinsText", "_GameCornerFishingGuruWinsComeAndGoText")
		"GAMECORNER_CLERK2":
			await _coin_gift("coins20a", 20, "_GameCornerClerk2WantSomeCoinsText", "_GameCornerClerk2Received20CoinsText", "_GameCornerClerk2INeedMoreCoinsText")
		"GAMECORNER_GENTLEMAN":
			await _coin_gift("coins20b", 20, "_GameCornerGentlemanThrowingMeOffText", "_GameCornerGentlemanReceived20CoinsText", "_GameCornerGentlemanCloselyWatchTheReelsText")
		"GAMECORNER_GYM_GUIDE":
			await Story.say("_GameCornerGymGuideTheyOfferRarePokemonText" if G.bag.has("RAINBOWBADGE") else "_GameCornerGymGuideChampInMakingText")
		"GAMECORNER_ROCKET":
			await Story.say("_GameCornerRocketImGuardingThisPosterText")
			var res := await Story.battle(ow, "ROCKET", 7, "_GameCornerRocketBattleEndText")
			if res == "win":
				await Story.say("_GameCornerRocketAfterBattleText")
				ow.remove_npc("GAMECORNER_ROCKET")
		"CELADONDINER_GYM_GUIDE":
			if G.bag.has("COIN_CASE"):
				await Story.say("_CeladonDinerGymGuideWinItBackText")
			else:
				await Story.say("_CeladonDinerGymGuideImFlatOutBustedText")
				G.add_item("COIN_CASE")
				Sound.jingle("Get_Key_Item")
				await UI.say(Story.fill("_CeladonDinerGymGuideReceivedCoinCaseText", [DB.item_name("COIN_CASE")]))
		"CELADONMANSION_ROOF_HOUSE_EEVEE_POKEBALL":
			ow.remove_npc(id)
			await Story.give_mon("EEVEE", 25)
		"CELADONMARTROOF_LITTLE_GIRL":
			await _roof_girl(ow)
		"ROCKETHIDEOUTB4F_GIOVANNI":
			await _hideout_giovanni(ow, a)
		"POKEMONTOWER2F_RIVAL":
			await _tower_rival(ow)
		"POKEMONTOWER7F_MR_FUJI":
			await Story.say("_PokemonTower7FMrFujiRescueText")
			G.set_flag("rescued_fuji")
			G.set_object_visible("POKEMONTOWER7F_MR_FUJI", false)
			G.set_object_visible("MRFUJISHOUSE_MR_FUJI", true)
			await ow.teleport_to("MR_FUJIS_HOUSE", Vector2i(3, 3), Vector2i.UP)
		"MRFUJISHOUSE_MR_FUJI":
			if G.bag.has("POKE_FLUTE"):
				await Story.say("_MrFujisHouseMrFujiHasMyFluteHelpedYouText")
			else:
				await Story.say("_MrFujisHouseMrFujiIThinkThisMayHelpYourQuestText")
				G.add_item("POKE_FLUTE")
				Sound.jingle("Get_Key_Item")
				await UI.say(Story.fill("_MrFujisHouseMrFujiReceivedPokeFluteText", [DB.item_name("POKE_FLUTE")]))
				await Story.say("_MrFujisHouseMrFujiPokeFluteExplanationText")
		"MRFUJISHOUSE_SUPER_NERD":
			await Story.say("_MrFujisHouseSuperNerdMrFujiHadBeenPrayingText" if G.flag("rescued_fuji") else "_MrFujisHouseSuperNerdMrFujiIsntHereText")
		"LAVENDERCUBONEHOUSE_BRUNETTE_GIRL":
			await Story.say("_LavenderCuboneHouseBrunetteGirlGhostIsGoneText" if G.flag("beat_ghost_marowak") else "_LavenderCuboneHouseBrunetteGirlPoorCubonesMotherText")
		"LAVENDERTOWN_LITTLE_GIRL":
			if await Story.ask("_LavenderTownLittleGirlDoYouBelieveInGhostsText"):
				await Story.say("_LavenderTownLittleGirlSoThereAreBelieversText")
			else:
				await Story.say("_LavenderTownLittleGirlHaHaGuessNotText")
		"NAMERATERSHOUSE_NAME_RATER":
			await _name_rater()
		"DAYCARE_GENTLEMAN":
			await _daycare()
		"FIGHTINGDOJO_KARATE_MASTER":
			await _karate_master(ow, a)
		"FIGHTINGDOJO_HITMONLEE_POKE_BALL", "FIGHTINGDOJO_HITMONCHAN_POKE_BALL":
			await _dojo_gift(ow, a)
		"SAFARIZONEGATE_SAFARI_ZONE_WORKER1":
			await Story.say("_SafariZoneGateSafariZoneWorker1Text")
		"SAFARIZONEGATE_SAFARI_ZONE_WORKER2":
			if await Story.ask("_SafariZoneGateSafariZoneWorker2FirstTimeHereText"):
				await Story.say("_SafariZoneGateSafariZoneWorker2SafariZoneExplanationText")
			else:
				await Story.say("_SafariZoneGateSafariZoneWorker2YoureARegularHereText")
		"WARDENSHOUSE_WARDEN":
			await _warden()
		"COPYCATSHOUSE2F_COPYCAT":
			await _copycat()
		"SILPHCO7F_SILPH_WORKER_M1":
			if G.flag("beat_silph_giovanni"):
				await Story.say("_SilphCo7FSilphWorkerM1SavedText")
			elif G.flag("got_lapras"):
				await Story.say("_SilphCo7FSilphWorkerM1IsOurPresidentOkText")
			else:
				await Story.say("_SilphCo7FSilphWorkerM1HaveThisPokemonText")
				G.set_flag("got_lapras")
				await Story.give_mon("LAPRAS", 15)
				await Story.say("_SilphCo7FSilphWorkerM1LaprasDescriptionText")
		"SILPHCO7F_RIVAL":
			await _silph_rival(ow)
		"SILPHCO11F_GIOVANNI":
			await _silph_giovanni(ow)
		"SILPHCO11F_SILPH_PRESIDENT":
			if G.bag.has("MASTER_BALL") or G.flag("got_master_ball"):
				await Story.say("_SilphCo11FSilphPresidentMasterBallDescriptionText")
			else:
				await Story.say("_SilphCo11FSilphPresidentText")
				G.set_flag("got_master_ball")
				G.add_item("MASTER_BALL")
				Sound.jingle("Get_Key_Item")
				await UI.say(Story.fill("_SilphCo11FSilphPresidentReceivedMasterBallText", [DB.item_name("MASTER_BALL")]))
				await Story.say("_SilphCo11FSilphPresidentMasterBallDescriptionText")
		_:
			# 실프 직원들: 해결 전/후 대사
			if id.begins_with("SILPHCO") and id.contains("SILPH_WORKER"):
				return await _silph_worker(ow, a)
			return false
	return true


# ------------------------------------------------------------------ 엘리베이터
static func _elevator(ow: Overworld) -> void:
	if ow.map_id == "ROCKET_HIDEOUT_ELEVATOR" and not G.bag.has("LIFT_KEY"):
		await Story.say("_RocketHideoutElevatorAppearsToNeedKeyText")
		return
	var floors: Array = ELEVATORS[ow.map_id]
	var names := []
	for f in floors:
		names.append(f[0])
	UI.say("몇 층으로 갈까요?", true, false)
	var c: int = await UI.choose(names, Rect2(96, 0, 64, mini(names.size() * 14 + 10, 96)))
	UI.close_box()
	if c < 0:
		return
	var f: Array = floors[c]
	G.flags["elev:" + ow.map_id] = [f[2], f[1]]
	for w in ow.map.warps:
		w.map = f[2]
		w.warp = f[1]
	# 흔들림 연출
	Sound.sfx("Push_Boulder")
	var cam := ow.cam
	for i in 6:
		cam.offset = Vector2(0, 2 if i % 2 == 0 else -2)
		await UI.wait(0.06)
	cam.offset = Vector2.ZERO
	Sound.sfx("Safari_Zone_PA")


# ------------------------------------------------------------------ 게임코너
static func _buy_coins() -> void:
	if not await Story.ask("_GameCornerClerk1DoYouNeedSomeGameCoinsText"):
		await Story.say("_GameCornerClerk1PleaseComePlaySometimeText")
		return
	if not G.bag.has("COIN_CASE"):
		await Story.say("_GameCornerClerk1DontHaveCoinCaseText")
		return
	if int(G.flags.get("coins", 0)) > 9949:
		await Story.say("_GameCornerClerk1CoinCaseIsFullText")
		return
	if not Story.pay(1000):
		await Story.say("_GameCornerClerk1CantAffordTheCoinsText")
		return
	G.flags["coins"] = int(G.flags.get("coins", 0)) + 50
	await Story.say("_GameCornerClerk1ThanksHereAre50CoinsText")


static func _coin_gift(flag: String, n: int, intro: String, got: String, after: String) -> void:
	if G.flag(flag):
		await Story.say(after)
		return
	await Story.say(intro)
	if not G.bag.has("COIN_CASE"):
		await Story.say("_GameCornerOopsForgotCoinCaseText")
		return
	G.set_flag(flag)
	G.flags["coins"] = mini(9999, int(G.flags.get("coins", 0)) + n)
	Sound.jingle("Get_Item1")
	await Story.say(got)


## 슬롯머신 (간단 버전: 3릴, 7/BAR/체리 등)
static func _slots() -> void:
	if not G.bag.has("COIN_CASE"):
		await Story.say("_GameCornerCoinCaseText")
		return
	if int(G.flags.get("coins", 0)) <= 0:
		await Story.say("_GameCornerNoCoinsText")
		return
	const SYM := ["7", "BAR", "체리", "피카", "슈륙", "잉어"]
	const PAY := {"7": 300, "BAR": 100, "체리": 8, "피카": 15, "슈륙": 15, "잉어": 15}
	while true:
		var coins := int(G.flags.get("coins", 0))
		if coins <= 0:
			await Story.say("_GameCornerNoCoinsText")
			return
		UI.say("코인 %d개\n몇 개를 걸까요?" % coins, true, false)
		var opts := []
		for i in mini(3, coins):
			opts.append("%d개" % (i + 1))
		var c: int = await UI.choose(opts, Rect2(104, 40, 56, opts.size() * 14 + 10))
		if c < 0:
			UI.close_box()
			return
		var bet := c + 1
		G.flags["coins"] = coins - bet
		var reels := []
		for i in 3:
			var r := randi() % 100
			reels.append("7" if r < 6 else ("BAR" if r < 16 else ("체리" if r < 40 else SYM[3 + randi() % 3])))
		# 가끔 확정 당첨
		if randi() % 8 == 0:
			reels[1] = reels[0]
			reels[2] = reels[0]
		Sound.sfx("Slots_New_Spin")
		await UI.say("[ %s | %s | %s ]" % reels, true)
		var win := 0
		if reels[0] == reels[1] and reels[1] == reels[2]:
			win = PAY[reels[0]] * bet
		elif reels[0] == "체리" and reels[1] == "체리":
			win = 4 * bet
		elif reels[0] == "체리":
			win = 2 * bet
		if win > 0:
			G.flags["coins"] = mini(9999, int(G.flags.coins) + win)
			Sound.jingle("Slots_Reward")
			await UI.say("당첨! 코인 %d개를 얻었다!" % win, true)
		else:
			await UI.say("꽝이다...", true)
		UI.say("한 번 더 할까요?", true, false)
		if not await UI.yes_no():
			UI.close_box()
			return


static func _prize_vendor(idx: int) -> void:
	if not G.bag.has("COIN_CASE"):
		await Story.say("_GameCornerCoinCaseText")
		return
	var list: Array = PRIZES[clampi(idx, 0, 2)]
	var opts := []
	for p in list:
		opts.append("%s %d" % [DB.item_name(p[0]) if p[2] == 0 else DB.mon_name(p[0]), p[1]])
	opts.append("그만두기")
	UI.say("코인 %d개\n어떤 경품으로 바꿀까요?" % int(G.flags.get("coins", 0)), true, false)
	var c: int = await UI.choose(opts, Rect2(24, 0, 136, opts.size() * 14 + 10))
	UI.close_box()
	if c < 0 or c >= list.size():
		return
	var p: Array = list[c]
	if int(G.flags.get("coins", 0)) < p[1]:
		await UI.say("코인이 부족합니다.")
		return
	G.flags["coins"] = int(G.flags.coins) - p[1]
	if p[2] == 0:
		G.add_item(p[0])
		Sound.jingle("Get_Item1")
		await UI.say("{PLAYER}{은} %s{을} 받았다!" % DB.item_name(p[0]))
	else:
		await Story.give_mon(p[0], p[2])


# ------------------------------------------------------------------ 무지개 백화점 옥상
static func _vending() -> void:
	await Story.say("_VendingMachineText1", true)
	var opts := []
	for v in VENDING:
		opts.append("%s %d원" % [DB.item_name(v[0]), v[1]])
	var c: int = await UI.choose(opts, Rect2(40, 0, 120, opts.size() * 14 + 10))
	UI.close_box()
	if c < 0:
		return
	if not Story.pay(VENDING[c][1]):
		await Story.say("_VendingMachineText4")
		return
	G.add_item(VENDING[c][0])
	await UI.say(Story.fill("_VendingMachineText5", [DB.item_name(VENDING[c][0])]))


static func _roof_girl(ow: Overworld) -> void:
	var have := []
	for d in DRINKS:
		if G.bag.has(d) and not G.flag("roof_gave:" + d):
			have.append(d)
	if have.is_empty():
		await Story.say("_CeladonMartRoofLittleGirlImThirstyText")
		return
	if not await Story.ask("_CeladonMartRoofLittleGirlGiveHerADrinkText"):
		return
	var names := []
	for d in have:
		names.append(DB.item_name(d))
	await Story.say("_CeladonMartRoofLittleGirlGiveHerWhichDrinkText", true)
	var c: int = await UI.choose(names, Rect2(64, 40, 96, names.size() * 14 + 10))
	UI.close_box()
	if c < 0:
		await Story.say("_CeladonMartRoofLittleGirlImNotThirstyText")
		return
	var d: String = have[c]
	G.remove_item(d)
	G.set_flag("roof_gave:" + d)
	var info: Array = {
		"FRESH_WATER": ["_CeladonMartRoofLittleGirlYayFreshWaterText", "TM_ICE_BEAM", "_CeladonMartRoofLittleGirlReceivedTM13Text", "_CeladonMartRoofLittleGirlTM13ExplanationText"],
		"SODA_POP": ["_CeladonMartRoofLittleGirlYaySodaPopText", "TM_ROCK_SLIDE", "_CeladonMartRoofLittleGirlReceivedTM48Text", "_CeladonMartRoofLittleGirlTM48ExplanationText"],
		"LEMONADE": ["_CeladonMartRoofLittleGirlYayLemonadeText", "TM_TRI_ATTACK", "_CeladonMartRoofLittleGirlReceivedTM49Text", "_CeladonMartRoofLittleGirlTM49ExplanationText"],
	}[d]
	await Story.say(info[0])
	G.add_item(info[1])
	Sound.jingle("Get_Item1")
	await UI.say(Story.fill(info[2], [DB.item_name(info[1])]))
	await UI.say(Story.fill(info[3], [DB.item_name(info[1])]))


static func _simple_gift(ow: Overworld, g: Array) -> void:
	var item: String = g[0]
	if G.flag("gift:" + item):
		await Story.say(g[3])
		return
	await Story.say(g[1])
	G.set_flag("gift:" + item)
	G.add_item(item)
	Sound.jingle("Get_Key_Item" if item.begins_with("HM") else "Get_Item1")
	await UI.say(Story.fill(g[2], [DB.item_name(item)]))
	await Story.say(g[3])


# ------------------------------------------------------------------ 로켓단 아지트
static func _hideout_giovanni(ow: Overworld, a: Actor) -> void:
	Story.face_each_other(ow, a)
	await Story.say("_RocketHideoutB4FGiovanniImpressedYouGotHereText")
	var res := await Story.battle(ow, "GIOVANNI", 1, "_RocketHideoutB4FGiovanniWhatCannotBeText")
	if res != "win":
		return
	await Story.say("_RocketHideoutB4FGiovanniHopeWeMeetAgainText")
	await UI.fade_out(0.3)
	ow.remove_npc("ROCKETHIDEOUTB4F_GIOVANNI")
	ow.show_npc("ROCKETHIDEOUTB4F_SILPH_SCOPE")
	G.set_flag("beat_hideout_giovanni")
	await UI.fade_in(0.3)


# ------------------------------------------------------------------ 포켓몬타워
static func _tower_rival(ow: Overworld) -> void:
	var r := ow.find_npc("POKEMONTOWER2F_RIVAL")
	if r == null:
		return
	Sound.music("MeetRival")
	Story.face_each_other(ow, r)
	if (ow.player.cell - r.cell).length_squared() > 1:
		await Story.approach(ow, r)
	await Story.say("_PokemonTower2FRivalWhatBringsYouHereText")
	var res := await Story.battle(ow, "RIVAL2", Story.rival_idx(4), "_PokemonTower2FRivalDefeatedText", "_PokemonTower2FRivalVictoryText")
	if res != "win":
		return
	G.set_flag("beat_tower_rival")
	Sound.music("MeetRival")
	await Story.say("_PokemonTower2FRivalHowsYourDexText")
	await UI.fade_out(0.3)
	ow.remove_npc("POKEMONTOWER2F_RIVAL")
	await UI.fade_in(0.3)
	Sound.map_music(ow.map_id)


static func _ghost_marowak(ow: Overworld) -> void:
	if not G.bag.has("SILPH_SCOPE"):
		await Story.say("_PokemonTower6FBeGoneText")
		await ow.start_battle({"kind": "wild", "species": "MAROWAK", "level": 30, "ghost": true})
		await Story.player_walk(ow, [Vector2i.DOWN])
		return
	await Story.say("_PokemonTower6FBeGoneText")
	var res := await ow.start_battle({"kind": "wild", "species": "MAROWAK", "level": 30, "no_catch": true})
	if res == "win":
		G.set_flag("beat_ghost_marowak")
		await Story.say("_PokemonTower6FGhostWasCubonesMotherText")
		await Story.say("_PokemonTower6FSoulWasCalmedText")
	else:
		await Story.player_walk(ow, [Vector2i.DOWN])


# ------------------------------------------------------------------ 노랑시티
static func _saffron_guard(ow: Overworld) -> void:
	var drink := ""
	for d in DRINKS:
		if G.bag.has(d):
			drink = d
	if drink == "":
		await Story.say("_SaffronGateGuardGeeImThirstyText")
		await Story.player_walk(ow, [-ow.player.facing if ow.player.facing != Vector2i.ZERO else Vector2i.DOWN])
		return
	await Story.say("_SaffronGateGuardImParchedText")
	G.remove_item(drink)
	G.set_flag("gave_guard_drink")
	await Story.say("_SaffronGateGuardYouCanGoOnThroughText")


static func _silph_rival(ow: Overworld) -> void:
	var r := ow.find_npc("SILPHCO7F_RIVAL")
	if r == null:
		return
	Sound.music("MeetRival")
	await Story.approach(ow, r)
	await Story.say("_SilphCo7FRivalWaitedHereText")
	var res := await Story.battle(ow, "RIVAL2", Story.rival_idx(7), "_SilphCo7FRivalDefeatedText", "_SilphCo7FRivalVictoryText")
	if res != "win":
		return
	G.set_flag("beat_silph_rival")
	Sound.music("MeetRival")
	await Story.say("_SilphCo7FRivalGoodLuckToYouText")
	await UI.fade_out(0.3)
	ow.remove_npc("SILPHCO7F_RIVAL")
	await UI.fade_in(0.3)
	Sound.map_music(ow.map_id)


static func _silph_giovanni(ow: Overworld) -> void:
	var gi := ow.find_npc("SILPHCO11F_GIOVANNI")
	if gi == null:
		return
	await Story.approach(ow, gi)
	await Story.say("_SilphCo11FGiovanniText")
	var res := await Story.battle(ow, "GIOVANNI", 2, "_SilphCo11FGiovanniILostAgainText")
	if res != "win":
		return
	await Story.say("_SilphCo11FGiovanniYouRuinedOurPlansText")
	G.set_flag("beat_silph_giovanni")
	await UI.fade_out(0.4)
	ow.remove_npc("SILPHCO11F_GIOVANNI")
	# 실프 건물과 노랑시티의 로켓단 철수
	for mid in DB.maps:
		if mid.begins_with("SILPH_CO_"):
			for n in DB.maps[mid].npcs:
				if n.id.contains("ROCKET"):
					G.set_object_visible(n.id, false)
	for id in SAFFRON_ROCKETS:
		G.set_object_visible(id, false)
	for id in SAFFRON_CIVILIANS:
		G.set_object_visible(id, true)
	G.set_object_visible("SILPHCO1F_LINK_RECEPTIONIST", true)
	for n in ow.npcs.duplicate():
		if n.data.id.contains("ROCKET"):
			ow.remove_npc(n.data.id)
	await UI.fade_in(0.4)


static func _silph_worker(ow: Overworld, a: Actor) -> bool:
	var who := ""
	for part in a.data.id.split("_", true, 1)[1].split("_"):
		who += part.capitalize()
	var prefix: String = "_" + ow.map.name + who
	var cands := []
	for k in DB.texts_en:
		var s: String = k
		if s.begins_with(prefix) and not s.contains("Received") and not s.contains("NoRoom") and not s.contains("Explanation"):
			cands.append(s)
	if cands.size() < 2:
		return false
	await Story.say(cands[1] if G.flag("beat_silph_giovanni") else cands[0])
	return true


static func _karate_master(ow: Overworld, a: Actor) -> void:
	if G.flag("beat_karate_master"):
		if G.flag("got_dojo_gift"):
			await Story.say("_FightingDojoKarateMasterStayAndTrainWithUsText")
		else:
			await Story.say("_FightingDojoKarateMasterIWillGiveYouAPokemonText")
		return
	await Story.say("_FightingDojoKarateMasterText")
	var res := await Story.battle(ow, "BLACKBELT", 1, "_FightingDojoKarateMasterDefeatedText")
	if res != "win":
		return
	G.set_flag("beat_karate_master")
	Story.beat_map_trainers(ow)
	await Story.say("_FightingDojoKarateMasterIWillGiveYouAPokemonText")


static func _dojo_gift(ow: Overworld, a: Actor) -> void:
	if G.flag("got_dojo_gift"):
		await Story.say("_FightingDojoBetterNotGetGreedyText")
		return
	if not G.flag("beat_karate_master"):
		await UI.say("몬스터볼이 놓여 있다.")
		return
	var lee: bool = a.data.id == "FIGHTINGDOJO_HITMONLEE_POKE_BALL"
	var sp := "HITMONLEE" if lee else "HITMONCHAN"
	await Sound.cry(sp)
	if not await Story.ask("_FightingDojoHitmonleePokeBallText" if lee else "_FightingDojoHitmonchanPokeBallText"):
		return
	G.set_flag("got_dojo_gift")
	ow.remove_npc(a.data.id)
	await Story.give_mon(sp, 30)


# ------------------------------------------------------------------ 사파리존
static func _safari_enter(ow: Overworld) -> void:
	if not await Story.ask("_SafariZoneGateSafariZoneWorker1WouldYouLikeToJoinText"):
		await Story.say("_SafariZoneGateSafariZoneWorker1PleaseComeAgainText")
		await Story.player_walk(ow, [Vector2i.DOWN])
		return
	if not Story.pay(500):
		await Story.say("_SafariZoneGateSafariZoneWorker1NotEnoughMoneyText")
		await Story.player_walk(ow, [Vector2i.DOWN])
		return
	await Story.say("_SafariZoneGateSafariZoneWorker1ThatllBe500PleaseText")
	await Story.say("_SafariZoneGateSafariZoneWorker1CallYouOnThePAText")
	G.set_flag("safari")
	G.flags["safari_balls"] = 30
	G.flags["safari_steps"] = 502
	await Story.player_walk(ow, [Vector2i.UP])


static func _safari_over(ow: Overworld) -> void:
	Sound.sfx("Safari_Zone_PA")
	await UI.say("딩동!\f사파리 게임 시간이 끝났습니다!")
	G.flags.erase("safari")
	G.flags.erase("safari_balls")
	await ow.teleport_to("SAFARI_ZONE_GATE", Vector2i(3, 3), Vector2i.DOWN)
	await Story.say("_SafariZoneGateSafariZoneWorker1GoodHaulComeAgainText")


static func is_safari_battle(map_id: String) -> bool:
	return G.flag("safari") and map_id.begins_with("SAFARI_ZONE_") and not map_id.ends_with("HOUSE") and map_id != "SAFARI_ZONE_GATE"


static func is_ghost_area(map_id: String) -> bool:
	return TOWER_MAPS.has(map_id) and not G.bag.has("SILPH_SCOPE")


static func _warden() -> void:
	if G.flag("gift:HM_STRENGTH"):
		await Story.say("_WardensHouseWardenHM04ExplanationText")
		return
	if not G.bag.has("GOLD_TEETH"):
		await Story.say(["_WardensHouseWardenGibberish1Text", "_WardensHouseWardenGibberish2Text", "_WardensHouseWardenGibberish3Text"].pick_random())
		return
	await Story.say("_WardensHouseWardenGibberish1Text")
	G.remove_item("GOLD_TEETH")
	await Story.say("_WardensHouseWardenGaveTheGoldTeethText")
	await Story.say("_WardensHouseWardenTeethPoppedInHisTeethText")
	await Story.say("_WardensHouseWardenThanksText")
	G.set_flag("gift:HM_STRENGTH")
	G.add_item("HM_STRENGTH")
	Sound.jingle("Get_Key_Item")
	await UI.say(Story.fill("_WardensHouseWardenReceivedHM04Text", [DB.item_name("HM_STRENGTH")]))
	await Story.say("_WardensHouseWardenHM04ExplanationText")


static func _copycat() -> void:
	if G.flag("gift:TM_MIMIC"):
		await Story.say("_CopycatsHouse2FCopycatTM31Explanation2Text")
		return
	if not G.bag.has("POKE_DOLL"):
		await Story.say("_CopycatsHouse2FCopycatDoYouLikePokemonText")
		return
	await Story.say("_CopycatsHouse2FCopycatTM31PreReceiveText")
	G.remove_item("POKE_DOLL")
	G.set_flag("gift:TM_MIMIC")
	G.add_item("TM_MIMIC")
	Sound.jingle("Get_Item1")
	await UI.say(Story.fill("_CopycatsHouse2FCopycatReceivedTM31Text", [DB.item_name("TM_MIMIC")]))
	await Story.say("_CopycatsHouse2FCopycatTM31Explanation1Text")


# ------------------------------------------------------------------ 이름 평가인 / 키우미집
static func _name_rater() -> void:
	if not await Story.ask("_NameRatersHouseNameRaterWantMeToRateText"):
		await Story.say("_NameRatersHouseNameRaterComeAnyTimeYouLikeText")
		return
	await Story.say("_NameRatersHouseNameRaterWhichPokemonText")
	var i: int = await Menus.party_menu("select", -1)
	if i < 0:
		await Story.say("_NameRatersHouseNameRaterComeAnyTimeYouLikeText")
		return
	var m: Dictionary = G.party[i]
	if m.ot != G.player_name:
		await UI.say(Story.fill("_NameRatersHouseNameRaterATrulyImpeccableNameText", [Mon.name_of(m)]))
		return
	await UI.say(Story.fill("_NameRatersHouseNameRaterGiveItANiceNameText", [Mon.name_of(m)]), true, false)
	var yes: bool = await UI.yes_no()
	UI.close_box()
	if not yes:
		await Story.say("_NameRatersHouseNameRaterComeAnyTimeYouLikeText")
		return
	await Story.say("_NameRatersHouseNameRaterWhatShouldWeNameItText")
	var nick := await UI.text_input("새 별명", Mon.name_of(m), 10)
	if nick == "":
		await Story.say("_NameRatersHouseNameRaterComeAnyTimeYouLikeText")
		return
	m.nick = nick
	await UI.say(Story.fill("_NameRatersHouseNameRaterPokemonHasBeenRenamedText", [nick]))


static func _daycare() -> void:
	var dc = G.flags.get("daycare")
	if dc != null:
		var m: Dictionary = G.fix_ints(dc.mon)
		var steps := int(G.flags.get("daycare_steps", 0))
		var before: int = m.level
		Mon.add_exp(m, steps)
		var grown: int = m.level - before
		var cost := 100 + grown * 100
		await UI.say(Story.fill("_DaycareGentlemanMonHasGrownText", [Mon.name_of(m), grown]))
		if G.party.size() >= 6:
			await Story.say("_DaycareGentlemanNoRoomForMonText")
			return
		await UI.say(Story.fill("_DaycareGentlemanOweMoneyText", [cost]), true, false)
		if not await UI.yes_no():
			UI.close_box()
			await Story.say("_DaycareGentlemanAllRightThenText")
			return
		UI.close_box()
		if not Story.pay(cost):
			await Story.say("_DaycareGentlemanNotEnoughMoneyText")
			return
		G.party.append(m)
		G.flags.erase("daycare")
		G.flags.erase("daycare_steps")
		await UI.say(Story.fill("_DaycareGentlemanGotMonBackText", [Mon.name_of(m)]))
		return
	if not await Story.ask("_DaycareGentlemanIntroText"):
		await Story.say("_DaycareGentlemanComeAgainText")
		return
	if G.party.size() <= 1:
		await Story.say("_DaycareGentlemanOnlyHaveOneMonText")
		return
	await Story.say("_DaycareGentlemanWhichMonText")
	var i: int = await Menus.party_menu("select", -1)
	if i < 0:
		return
	var mm: Dictionary = G.party[i]
	for mv in mm.moves:
		if mv.id in ["CUT", "FLY", "SURF", "STRENGTH", "FLASH"]:
			await Story.say("_DaycareGentlemanCantAcceptMonWithHMText")
			return
	G.party.remove_at(i)
	G.flags["daycare"] = {"mon": mm}
	G.flags["daycare_steps"] = 0
	await UI.say(Story.fill("_DaycareGentlemanWillLookAfterMonText", [Mon.name_of(mm)]))
	await Story.say("_DaycareGentlemanComeSeeMeInAWhileText")
