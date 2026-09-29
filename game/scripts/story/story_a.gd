class_name StoryA
extends RefCounted
## 스토리 1구간: 회색시티 → 달맞이산 → 블루시티(라이벌, 로켓단, 골든볼 다리, 이수재) → 갈색시티(상트앤호, 마티스)
## 그리고 여러 곳의 공통 NPC(낚시 할아버지, 오박사 조수, 교환 NPC, 잠만보).

const TRADE_NPCS := {
	"ROUTE11GATE2F_YOUNGSTER": 0, "ROUTE2TRADEHOUSE_GAMEBOY_KID": 1, "CINNABARLABFOSSILROOM_SCIENTIST2": 3,
	"VERMILIONTRADEHOUSE_LITTLE_GIRL": 4, "ROUTE18GATE2F_YOUNGSTER": 5, "CERULEANTRADEHOUSE_GAMBLER": 6,
	"CINNABARLABTRADEROOM_GRAMPS": 7, "CINNABARLABTRADEROOM_BEAUTY": 8, "UNDERGROUNDPATHROUTE5_LITTLE_GIRL": 9,
}
# 오박사 조수: 잡은 수 조건 -> 선물
const AIDES := {
	"ROUTE2GATE_OAKS_AIDE": [10, "HM_FLASH", "_Route2GateOaksAideFlashExplanationText"],
	"ROUTE11GATE2F_OAKS_AIDE": [30, "ITEMFINDER", "_Route11Gate2FOaksAideItemfinderDescriptionText"],
	"ROUTE15GATE2F_OAKS_AIDE": [50, "EXP_ALL", "_Route15Gate2FOaksAideExpAllText"],
}
# 버밀리언 체육관 쓰레기통: 첫 번째 스위치가 i 일 때 두 번째 스위치 후보
const TRASH_NEXT := [[1, 3], [0, 2, 4], [1, 5], [0, 4, 6], [1, 3, 5, 7], [2, 4, 8], [3, 7, 9], [4, 6, 8, 10],
	[5, 7, 11], [6, 10, 12], [7, 9, 11, 13], [8, 10, 14], [9, 13], [10, 12, 14], [11, 13]]


static func on_build(ow: Overworld) -> void:
	if ow.map_id == "VERMILION_GYM" and not G.flag("surge_lock2"):
		ow._apply_block(2 * ow.map.w + 2, 0x24)


static func can_warp(ow: Overworld, dest: String) -> bool:
	if ow.map_id == "VERMILION_DOCK" and dest == "SS_ANNE_1F" and G.flag("ss_anne_left"):
		return false
	return true


static func on_enter(ow: Overworld) -> void:
	match ow.map_id:
		"VERMILION_DOCK":
			if G.flag("got:HM_CUT") and not G.flag("ss_anne_left"):
				await _ss_anne_departs(ow)
		"VERMILION_GYM":
			G.flags["trash1"] = (randi() % 8) * 2
			G.flags.erase("surge_lock1")


static func on_step(ow: Overworld) -> bool:
	var c := ow.player.cell
	match ow.map_id:
		"PEWTER_CITY":
			if not G.bag.has("BOULDERBADGE") and c in [Vector2i(35, 17), Vector2i(36, 17), Vector2i(37, 18), Vector2i(37, 19)]:
				await _pewter_youngster_leads(ow)
				return true
		"MUSEUM_1F":
			if c.y == 4 and (c.x == 9 or c.x == 10) and not G.flag("museum_ticket"):
				await _museum_ticket(ow, true)
				return true
		"MT_MOON_B2F":
			if c == Vector2i(13, 8) and not G.flag("beat_mtmoon_nerd"):
				var a := ow.find_npc("MTMOONB2F_SUPER_NERD")
				if a:
					await _mtmoon_nerd(ow, a)
				return true
		"CERULEAN_CITY":
			if not G.flag("beat_cerulean_rocket") and (c == Vector2i(30, 7) or c == Vector2i(30, 9)):
				var r := ow.find_npc("CERULEANCITY_ROCKET")
				if r:
					r.set_facing(Vector2i.DOWN if c.y > 8 else Vector2i.UP)
					ow.player.set_facing(-r.facing)
					await _cerulean_rocket(ow, r)
					return true
			if not G.flag("beat_cerulean_rival") and (c == Vector2i(20, 6) or c == Vector2i(21, 6)):
				await _cerulean_rival(ow)
				return true
		"ROUTE_24":
			if c == Vector2i(10, 15) and not G.flag("got_nugget"):
				var a2 := ow.find_npc("ROUTE24_COOLTRAINER_M1")
				if a2:
					await _nugget_bridge(ow, a2)
					return true
		"VERMILION_CITY":
			if c == Vector2i(18, 30) and ow.player.facing == Vector2i.UP:
				if G.flag("ss_anne_left") or not G.bag.has("S_S_TICKET"):
					await Story.say("_VermilionCitySailor1ShipSetSailText" if G.flag("ss_anne_left") else "_VermilionCitySailor1YouNeedATicketText")
					await Story.player_walk(ow, [Vector2i.DOWN])
					return true
				if not G.flag("showed_ticket"):
					G.set_flag("showed_ticket")
					await Story.say("_VermilionCitySailor1FlashedTicketText")
		"SS_ANNE_2F":
			if not G.flag("beat_ssanne_rival") and (c == Vector2i(36, 8) or c == Vector2i(37, 8)):
				await _ss_anne_rival(ow)
				return true
	return false


static func on_talk(ow: Overworld, a: Actor) -> bool:
	var id: String = a.data.get("id", "")
	if TRADE_NPCS.has(id):
		await Story.npc_trade(ow, TRADE_NPCS[id])
		return true
	if AIDES.has(id):
		await _oaks_aide(ow, AIDES[id])
		return true
	match id:
		"PEWTERCITY_SUPER_NERD1":
			if await Story.ask("_PewterCitySuperNerd1DidYouCheckOutMuseumText"):
				await Story.say("_PewterCitySuperNerd1WerentThoseFossilsAmazingText")
			else:
				await Story.say("_PewterCitySuperNerd1YouHaveToGoText")
				await Story.say("_PewterCitySuperNerd1ItsRightHereText")
		"PEWTERCITY_SUPER_NERD2":
			if await Story.ask("_PewterCitySuperNerd2DoYouKnowWhatImDoingText"):
				await Story.say("_PewterCitySuperNerd2ThatsRightText")
			await Story.say("_PewterCitySuperNerd2ImSprayingRepelText")
		"PEWTERCITY_YOUNGSTER":
			await Story.say("_PewterCityYoungsterGoTakeOnBrockText")
		"MUSEUM1F_SCIENTIST1":
			await _museum_ticket(ow, false)
		"MUSEUM1F_SCIENTIST2":
			if G.flag("got_old_amber"):
				await Story.say("_Museum1FScientist2GetTheOldAmberCheckText")
			else:
				await Story.say("_Museum1FScientist2TakeThisToAPokemonLabText")
				G.set_flag("got_old_amber")
				ow.remove_npc("MUSEUM1F_OLD_AMBER")
				await ow.receive("OLD_AMBER")
		"MTMOONPOKECENTER_MAGIKARP_SALESMAN":
			await _magikarp_salesman()
		"MTMOONB2F_SUPER_NERD":
			if not G.flag("beat_mtmoon_nerd"):
				await _mtmoon_nerd(ow, a)
			elif not G.flag("got_fossil"):
				await Story.say("_MtMoonB2fSuperNerdEachTakeOneText")
			else:
				await Story.say("_MtMoonB2FSuperNerdTheresAPokemonLabText")
		"MTMOONB2F_DOME_FOSSIL", "MTMOONB2F_HELIX_FOSSIL":
			await _take_fossil(ow, a)
		"CERULEANCITY_ROCKET":
			await _cerulean_rocket(ow, a)
		"CERULEANCITY_RIVAL":
			await Story.say("_CeruleanCityRivalIWentToBillsText")
		"CERULEANCITY_SLOWBRO":
			await Story.say(["_CeruleanCitySlowbroTookASnoozeText", "_CeruleanCitySlowbroIsLoafingAroundText",
				"_CeruleanCitySlowbroTurnedAwayText", "_CeruleanCitySlowbroIgnoredOrdersText"].pick_random())
		"CERULEANCITY_COOLTRAINER_F1":
			await Story.say(["_CeruleanCityCooltrainerF1SlowbroUseSonicboomText", "_CeruleanCityCooltrainerF1SlowbroPunchText",
				"_CeruleanCityCooltrainerF1SlowbroWithdrawText"].pick_random())
		"ROUTE24_COOLTRAINER_M1":
			if G.flag("got_nugget"):
				await Story.say("_Route24CooltrainerM1YouCouldBecomeATopLeaderText")
			else:
				await _nugget_bridge(ow, a)
		"BILLSHOUSE_BILL_POKEMON":
			await _bill_pokemon(ow, a)
		"BILLSHOUSE_BILL1":
			await _bill_ticket(ow)
		"BILLSHOUSE_BILL2":
			await Story.say("_BillsHouseBillCheckOutMyRarePokemonText")
		"BIKESHOP_CLERK":
			await _bike_shop(ow)
		"BIKESHOP_YOUNGSTER":
			await Story.say("_BikeShopYoungsterCoolBikeText" if G.bag.has("BICYCLE") else "_BikeShopYoungsterTheseBikesAreExpensiveText")
		"POKEMONFANCLUB_CHAIRMAN":
			await _fan_club(ow)
		"POKEMONFANCLUB_PIKACHU_FAN":
			await Story.say("_PokemonFanClubPikachuFanNormalText")
		"POKEMONFANCLUB_SEEL_FAN":
			await Story.say("_PokemonFanClubSeelFanNormalText")
		"POKEMONFANCLUB_PIKACHU":
			await Sound.cry("PIKACHU")
			await Story.say("_PokemonFanClubPikachuText")
		"POKEMONFANCLUB_SEEL":
			await Sound.cry("SEEL")
			await Story.say("_PokemonFanClubSeelText")
		"VERMILIONCITY_SAILOR1":
			if G.flag("ss_anne_left"):
				await Story.say("_VermilionCitySailor1ShipSetSailText")
			elif G.bag.has("S_S_TICKET"):
				await Story.say("_VermilionCitySailor1FlashedTicketText")
			else:
				await Story.say("_VermilionCitySailor1YouNeedATicketText")
		"VERMILIONCITY_GAMBLER1":
			await Story.say("_VermilionCityGambler1SSAnneDepartedText" if G.flag("ss_anne_left") else "_VermilionCityGambler1DidYouSeeText")
		"VERMILIONCITY_MACHOP":
			await Story.say("_VermilionCityMachopText")
			await Sound.cry("MACHOP")
		"SSANNE2F_RIVAL":
			await _ss_anne_rival(ow)
		"SSANNECAPTAINSROOM_CAPTAIN":
			await _captain(ow)
		"VERMILIONOLDRODHOUSE_FISHING_GURU":
			await _rod_guru(ow, "OLD_ROD", "_VermilionOldRodHouseFishingGuru")
		"FUCHSIAGOODRODHOUSE_FISHING_GURU":
			await _rod_guru(ow, "GOOD_ROD", "_FuchsiaGoodRodHouseFishingGuru")
		"ROUTE12SUPERRODHOUSE_FISHING_GURU":
			await _rod_guru(ow, "SUPER_ROD", "_Route12SuperRodHouseFishingGuru")
		"ROUTE12_SNORLAX":
			await Story.say("_Route12SnorlaxText")
		"ROUTE16_SNORLAX":
			await Story.say("_Route12SnorlaxText")
		_:
			return false
	return true


static func on_hidden(ow: Overworld, h: Dictionary) -> bool:
	match h.handler:
		"GymTrashScript":
			await _trash_can(ow, int(h.arg))
			return true
		"BillsHousePC":
			if G.flag("bill_in_machine") and not G.flag("bill_separated"):
				await Story.say("_BillsHouseMonitorText")
				Sound.sfx("Turn_On_PC")
				await Story.say("_BillsHouseInitiatedText")
				Sound.sfx("Shrink")
				await UI.wait(0.6)
				G.set_flag("bill_separated")
				var b := ow.show_npc("BILLSHOUSE_BILL1")
				if b:
					b.teleport(Vector2i(5, 6))
					await Story.step_npc(b, [Vector2i.DOWN, Vector2i.RIGHT])
				return true
	return false


## 포켓몬 피리: 앞에 잠만보가 있으면 깨워서 배틀
static func use_poke_flute(ow: Overworld) -> bool:
	var front := ow.player.cell + ow.player.facing
	var a := ow.npc_at(front)
	if a == null or not a.data.get("id", "") in ["ROUTE12_SNORLAX", "ROUTE16_SNORLAX"]:
		return false
	await Sound.sfx_wait("Pokeflute")
	await UI.say("{PLAYER}{은} 포켓몬 피리를 불었다!")
	var r12: bool = a.data.id == "ROUTE12_SNORLAX"
	await Story.say("_Route12SnorlaxWokeUpText" if r12 else "_Route16SnorlaxWokeUpText")
	await Sound.cry("SNORLAX")
	await ow.start_battle({"kind": "wild", "species": "SNORLAX", "level": 30})
	ow.remove_npc(a.data.id)
	await Story.say("_Route12SnorlaxCalmedDownText" if r12 else "_Route16SnorlaxReturnedToMountainsText")
	return true


# ------------------------------------------------------------------ 회색시티 / 박물관
static func _pewter_youngster_leads(ow: Overworld) -> void:
	var y := ow.find_npc("PEWTERCITY_YOUNGSTER")
	if y:
		Story.face_each_other(ow, y)
	await Story.say("_PewterCityYoungsterYoureATrainerFollowMeText")
	await ow.teleport_to("PEWTER_CITY", Vector2i(16, 18), Vector2i.UP)
	await Story.say("_PewterCityYoungsterGoTakeOnBrockText")


static func _museum_ticket(ow: Overworld, at_entrance: bool) -> void:
	var c := ow.player.cell
	if not at_entrance and (c == Vector2i(13, 4) or c == Vector2i(12, 3)):
		if await Story.ask("_Museum1FScientist1DoYouKnowWhatAmberIsText"):
			await Story.say("_Museum1FScientist1TheresALabSomewhereText")
		else:
			await Story.say("_Museum1FScientist1AmberIsFossilizedTreeSapText")
		return
	if G.flag("museum_ticket"):
		await Story.say("_Museum1FScientist1TakePlentyOfTimeText")
		return
	if not at_entrance:
		await Story.say("_Museum1FScientist1GoToOtherSideText")
		return
	if await Story.ask("_Museum1FScientist1WouldYouLikeToComeInText"):
		if Story.pay(50):
			G.set_flag("museum_ticket")
			await Story.say("_Museum1FScientist1ThankYouText")
			return
		await Story.say("_Museum1FScientist1DontHaveEnoughMoneyText")
	await Story.say("_Museum1FScientist1ComeAgainText")
	await Story.player_walk(ow, [Vector2i.DOWN])


# ------------------------------------------------------------------ 달맞이산
static func _magikarp_salesman() -> void:
	if G.flag("bought_magikarp"):
		await Story.say("_MtMoonPokecenterMagikarpSalesmanNoRefundsText")
		return
	if not await Story.ask("_MtMoonPokecenterMagikarpSalesmanIGotADealText"):
		await Story.say("_MtMoonPokecenterMagikarpSalesmanNoText")
		return
	if not Story.pay(500):
		await Story.say("_MtMoonPokecenterMagikarpSalesmanNoMoneyText")
		return
	G.set_flag("bought_magikarp")
	await Story.give_mon("MAGIKARP", 5)


static func _mtmoon_nerd(ow: Overworld, a: Actor) -> void:
	Story.face_each_other(ow, a)
	await Story.say("_MtMoonB2FSuperNerdTheyreBothMineText")
	var res := await Story.battle(ow, "SUPER_NERD", 2, "_MtMoonB2FSuperNerdOkIllShareText")
	if res == "win":
		G.set_flag("beat_mtmoon_nerd")
		await Story.say("_MtMoonB2fSuperNerdEachTakeOneText")


static func _take_fossil(ow: Overworld, a: Actor) -> void:
	var dome: bool = a.data.id == "MTMOONB2F_DOME_FOSSIL"
	if not await Story.ask("_MtMoonB2FDomeFossilYouWantText" if dome else "_MtMoonB2FHelixFossilYouWantText"):
		return
	var item := "DOME_FOSSIL" if dome else "HELIX_FOSSIL"
	G.add_item(item)
	G.set_flag("got_fossil")
	ow.remove_npc(a.data.id)
	Sound.jingle("Get_Key_Item")
	await UI.say(Story.fill("_MtMoonB2FReceivedFossilText", [DB.item_name(item)]))
	var nerd := ow.find_npc("MTMOONB2F_SUPER_NERD")
	await Story.say("_MtMoonB2FSuperNerdThenThisIsMineText")
	ow.remove_npc("MTMOONB2F_HELIX_FOSSIL" if dome else "MTMOONB2F_DOME_FOSSIL")
	if nerd:
		nerd.set_facing(Vector2i.UP)


# ------------------------------------------------------------------ 블루시티
static func _cerulean_rival(ow: Overworld) -> void:
	Sound.music("MeetRival")
	var r := ow.show_npc("CERULEANCITY_RIVAL")
	if r == null:
		return
	r.teleport(Vector2i(ow.player.cell.x, 2))
	while r.cell.y < ow.player.cell.y - 1:
		await r.step(Vector2i.DOWN)
	Story.face_each_other(ow, r)
	await Story.say("_CeruleanCityRivalPreBattleText")
	var res := await Story.battle(ow, "RIVAL1", Story.rival_idx(7), "_CeruleanCityRivalDefeatedText", "_CeruleanCityRivalVictoryText")
	if res != "win":
		ow.remove_npc("CERULEANCITY_RIVAL")
		return
	G.set_flag("beat_cerulean_rival")
	Sound.music("MeetRival")
	await Story.say("_CeruleanCityRivalIWentToBillsText")
	await r.step(Vector2i.LEFT if r.cell.x > 19 else Vector2i.RIGHT)
	for i in 6:
		await r.step(Vector2i.DOWN)
	ow.remove_npc("CERULEANCITY_RIVAL")
	Sound.map_music(ow.map_id)


static func _cerulean_rocket(ow: Overworld, r: Actor) -> void:
	if G.flag("beat_cerulean_rocket"):
		return
	await Story.say("_CeruleanCityRocketText")
	var res := await Story.battle(ow, "ROCKET", 5, "_CeruleanCityRocketIGiveUpText")
	if res != "win":
		return
	G.set_flag("beat_cerulean_rocket")
	await Story.say("_CeruleanCityRocketIllReturnTheTMText")
	G.add_item("TM_DIG")
	Sound.jingle("Get_Item1")
	await UI.say(Story.fill("_CeruleanCityRocketReceivedTM28Text", []))
	await Story.say("_CeruleanCityRocketIBetterGetMovingText")
	await UI.fade_out(0.3)
	ow.remove_npc("CERULEANCITY_ROCKET")
	await UI.fade_in(0.3)


static func _nugget_bridge(ow: Overworld, a: Actor) -> void:
	Story.face_each_other(ow, a)
	await Story.say("_Route24CooltrainerM1YouBeatOurContestText")
	await Story.say("_Route24CooltrainerM1YouJustEarnedAPrizeText")
	G.set_flag("got_nugget")
	await ow.receive("NUGGET")
	await Story.say("_Route24CooltrainerM1JoinTeamRocketText")
	await Story.battle(ow, "ROCKET", 6, "_Route24CooltrainerM1DefeatedText")


static func _bill_pokemon(ow: Overworld, a: Actor) -> void:
	if not await Story.ask("_BillsHouseBillImNotAPokemonText"):
		await Story.say("_BillsHouseBillNoYouGottaHelpText")
	await Story.say("_BillsHouseBillUseSeparationSystemText")
	await Story.step_npc(a, [Vector2i.UP, Vector2i.UP, Vector2i.UP] if ow.player.cell.x != a.cell.x else [Vector2i.RIGHT, Vector2i.UP, Vector2i.UP, Vector2i.LEFT, Vector2i.UP])
	ow.remove_npc("BILLSHOUSE_BILL_POKEMON")
	G.set_flag("bill_in_machine")


static func _bill_ticket(ow: Overworld) -> void:
	if not G.flag("got_ss_ticket"):
		await Story.say("_BillsHouseBillThankYouText")
		G.set_flag("got_ss_ticket")
		G.add_item("S_S_TICKET")
		Sound.jingle("Get_Key_Item")
		await UI.say(Story.fill("_SSTicketReceivedText", [DB.item_name("S_S_TICKET")]))
		G.set_object_visible("CERULEANCITY_GUARD1", true)
		G.set_object_visible("CERULEANCITY_GUARD2", false)
	await Story.say("_BillsHouseBillWhyDontYouGoInsteadOfMeText")


static func _bike_shop(ow: Overworld) -> void:
	if G.bag.has("BICYCLE"):
		await Story.say("_BikeShopClerkHowDoYouLikeYourBicycleText")
		return
	if G.bag.has("BIKE_VOUCHER"):
		await Story.say("_BikeShopClerkOhThatsAVoucherText")
		G.remove_item("BIKE_VOUCHER")
		G.add_item("BICYCLE")
		Sound.jingle("Get_Key_Item")
		await Story.say("_BikeShopExchangedVoucherText")
		return
	await Story.say("_BikeShopClerkWelcomeText", true)
	var c: int = await UI.choose(["자전거 1000000원", "그만두다"], Rect2(0, 0, 150, 38))
	UI.close_box()
	if c == 0:
		await Story.say("_BikeShopCantAffordText")
	await Story.say("_BikeShopComeAgainText")


static func _fan_club(ow: Overworld) -> void:
	if G.flag("got_bike_voucher"):
		await Story.say("_PokemonFanClubChairFinalText")
		return
	if not await Story.ask("_PokemonFanClubChairmanIntroText"):
		await Story.say("_PokemonFanClubNoStoryText")
		return
	await Story.say("_PokemonFanClubChairmanStoryText")
	G.set_flag("got_bike_voucher")
	G.add_item("BIKE_VOUCHER")
	Sound.jingle("Get_Key_Item")
	await UI.say(Story.fill("_PokemonFanClubReceivedBikeVoucherText", [DB.item_name("BIKE_VOUCHER")]))
	await Story.say("_PokemonFanClubExplainBikeVoucherText")


# ------------------------------------------------------------------ 갈색시티 / 상트앤호
static func _ss_anne_rival(ow: Overworld) -> void:
	Sound.music("MeetRival")
	var r := ow.show_npc("SSANNE2F_RIVAL")
	if r == null:
		return
	r.teleport(Vector2i(ow.player.cell.x, 4))
	while r.cell.y < ow.player.cell.y - 1:
		await r.step(Vector2i.DOWN)
	Story.face_each_other(ow, r)
	await Story.say("_SSAnne2FRivalText")
	var res := await Story.battle(ow, "RIVAL2", Story.rival_idx(1), "_SSAnne2FRivalDefeatedText", "_SSAnne2FRivalVictoryText")
	if res != "win":
		ow.remove_npc("SSANNE2F_RIVAL")
		return
	G.set_flag("beat_ssanne_rival")
	Sound.music("MeetRival")
	await Story.say("_SSAnne2FRivalCutMasterText")
	await r.step(Vector2i.LEFT if r.cell.x > 36 else Vector2i.RIGHT)
	for i in 4:
		await r.step(Vector2i.DOWN)
	ow.remove_npc("SSANNE2F_RIVAL")
	Sound.map_music(ow.map_id)


static func _captain(ow: Overworld) -> void:
	if G.flag("got:HM_CUT"):
		await Story.say("_SSAnneCaptainsRoomCaptainNotSickAnymoreText")
		return
	await Story.say("_SSAnneCaptainsRoomRubCaptainsBackText")
	await Sound.jingle("PkmnHealed")
	await Story.say("_SSAnneCaptainsRoomCaptainIFeelMuchBetterText")
	G.add_item("HM_CUT")
	G.set_flag("got:HM_CUT")
	Sound.jingle("Get_Key_Item")
	await UI.say(Story.fill("_SSAnneCaptainsRoomCaptainReceivedHM01Text", [DB.item_name("HM_CUT")]))


static func _ss_anne_departs(ow: Overworld) -> void:
	G.set_flag("ss_anne_left")
	Sound.stop_music()
	await UI.wait(0.4)
	await Sound.sfx_wait("SS_Anne_Horn")
	await UI.say("상트앤호가 뱃고동을 울리며\n항구를 떠나간다...")
	Sound.map_music(ow.map_id)


static func _trash_can(ow: Overworld, idx: int) -> void:
	if G.flag("surge_lock2"):
		await Story.say("_VermilionGymTrashText")
		return
	if not G.flag("surge_lock1"):
		if idx == int(G.flags.get("trash1", 0)):
			G.set_flag("surge_lock1")
			G.flags["trash2"] = TRASH_NEXT[idx].pick_random()
			await Story.say("_VermilionGymTrashSuccessText1")
			Sound.sfx("Switch")
		else:
			await Story.say("_VermilionGymTrashText")
		return
	if idx == int(G.flags.get("trash2", -1)):
		G.set_flag("surge_lock2")
		Sound.sfx("Go_Inside")
		await Story.say("_VermilionGymTrashSuccessText3")
		ow._apply_block(2 * ow.map.w + 2, DB.maps["VERMILION_GYM"].blk[2 * ow.map.w + 2])
	else:
		G.flags.erase("surge_lock1")
		G.flags["trash1"] = (randi() % 8) * 2
		await Story.say("_VermilionGymTrashFailText")


# ------------------------------------------------------------------ 공통 NPC
static func _rod_guru(ow: Overworld, rod: String, pre: String) -> void:
	if G.bag.has(rod):
		var lab := pre + ("HowAreTheFishBitingText" if rod == "OLD_ROD" else "HowAreTheFishText" if rod == "GOOD_ROD" else "TryFishingText")
		await Story.say(lab)
		return
	var ask_lab := pre + ("DoYouLikeToFishText" if rod != "GOOD_ROD" else "Text")
	if not await Story.ask(ask_lab):
		await Story.say(pre + ("ThatsSoDisappointingText" if rod != "SUPER_ROD" else "ThatsDisappointingText"))
		return
	G.add_item(rod)
	Sound.jingle("Get_Key_Item")
	match rod:
		"OLD_ROD":
			await UI.say(Story.fill(pre + "TakeThisText", [DB.item_name(rod)]))
			await Story.say(pre + "FishingIsAWayOfLifeText")
		"GOOD_ROD":
			await UI.say(Story.fill(pre + "ReceivedGoodRodText", [DB.item_name(rod)]))
		"SUPER_ROD":
			await UI.say(Story.fill(pre + "ReceivedSuperRodText", [DB.item_name(rod)]))
			await Story.say(pre + "FishingWayOfLifeText")


static func _oaks_aide(ow: Overworld, info: Array) -> void:
	var need: int = info[0]
	var item: String = info[1]
	if G.flag("aide:" + item):
		await Story.say(info[2])
		return
	var n := G.caught.size()
	await UI.say(Story.fill("_OaksAideHiText", [need, DB.item_name(item)]), true, false)
	var yes: bool = await UI.yes_no()
	UI.close_box()
	if not yes:
		await UI.say(Story.fill("_OaksAideComeBackText", [need, DB.item_name(item)]))
		return
	if n < need:
		await UI.say(Story.fill("_OaksAideUhOhText", [n, need, DB.item_name(item)]))
		return
	await UI.say(Story.fill("_OaksAideHereYouGoText", [n]))
	G.set_flag("aide:" + item)
	G.add_item(item)
	Sound.jingle("Get_Key_Item")
	await UI.say(Story.fill("_OaksAideGotItemText", [DB.item_name(item)]))
	await Story.say(info[2])
