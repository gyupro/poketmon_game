class_name Events
extends RefCounted
## 스토리 이벤트 (원작 스크립트를 GDScript 로 옮긴 것). 맵별로 on_enter/on_step/on_talk/on_sign 훅.

const STARTERS := {
	"OAKSLAB_CHARMANDER_POKE_BALL": "CHARMANDER",
	"OAKSLAB_SQUIRTLE_POKE_BALL": "SQUIRTLE",
	"OAKSLAB_BULBASAUR_POKE_BALL": "BULBASAUR",
}
# 내가 고른 것 -> 라이벌이 고르는 볼
const RIVAL_PICK := {
	"CHARMANDER": "OAKSLAB_SQUIRTLE_POKE_BALL",
	"SQUIRTLE": "OAKSLAB_BULBASAUR_POKE_BALL",
	"BULBASAUR": "OAKSLAB_CHARMANDER_POKE_BALL",
}
const STARTER_DESC := {"CHARMANDER": "불꽃", "SQUIRTLE": "물", "BULBASAUR": "풀"}
# 라이벌 파티 인덱스 (Rival1 데이터 순서: 꼬부기, 이상해씨, 파이리)
const RIVAL_PARTY := {"SQUIRTLE": 1, "BULBASAUR": 2, "CHARMANDER": 3}


static func on_npc_spawn(ow: Overworld, a: Actor) -> void:
	StoryB.on_npc_spawn(ow, a)
	StoryC.on_npc_spawn(ow, a)


## 맵 타일을 그린 직후 (NPC 배치 전): 블록 교체
static func on_build(ow: Overworld) -> void:
	StoryA.on_build(ow)
	StoryB.on_build(ow)
	StoryC.on_build(ow)


static func on_trainer_beaten(ow: Overworld, a: Actor) -> void:
	StoryC.on_trainer_beaten(ow, a)


static func on_boulder(ow: Overworld, b: Actor) -> void:
	await StoryC.on_boulder(ow, b)


static func use_poke_flute(ow: Overworld) -> bool:
	return await StoryA.use_poke_flute(ow)


## 맵에 들어온 직후 (호출하는 쪽에서 입력을 잠근 상태)
static func on_enter(ow: Overworld) -> void:
	await StoryA.on_enter(ow)
	await StoryB.on_enter(ow)
	await StoryC.on_enter(ow)
	match ow.map_id:
		"VIRIDIAN_MART":
			if G.flag("got_starter") and not G.flag("got_parcel"):
				await _parcel(ow)


static func can_warp(ow: Overworld, dest: String) -> bool:
	if dest == "VIRIDIAN_GYM" and G.badge_count() < 7:
		await UI.say(DB.text("_ViridianCityGymLockedText"))
		return false
	if not StoryA.can_warp(ow, dest):
		return false
	if not await StoryB.can_warp(ow, dest):
		return false
	if not await StoryC.can_warp(ow, dest):
		return false
	return true


static func on_step(ow: Overworld) -> bool:
	if await StoryA.on_step(ow) or await StoryB.on_step(ow) or await StoryC.on_step(ow):
		return true
	var c := ow.player.cell
	match ow.map_id:
		"PALLET_TOWN":
			if c.y == 1 and not G.flag("oak_intro"):
				await _oak_stops_you(ow)
				return true
		"OAKS_LAB":
			if c.y == 6 and G.flag("oak_intro") and not G.flag("got_starter"):
				await UI.say("오박사: 이봐! 아직 가면 안 된다!")
				await ow.player.step(Vector2i.UP)
				G.pos = ow.player.cell
				return true
			if c.y == 6 and G.flag("got_starter") and not G.flag("rival_battle1"):
				await _rival_battle(ow)
				return true
		"VIRIDIAN_CITY":
			if c == Vector2i(19, 9) and not G.flag("got_pokedex"):
				await UI.say(DB.map_text("VIRIDIAN_CITY", "TEXT_VIRIDIANCITY_OLD_MAN_SLEEPY"))
				await ow.player.step(Vector2i.DOWN)
				G.pos = ow.player.cell
				return true
	return false


static func on_sign(ow: Overworld, s: Dictionary) -> bool:
	return await StoryB.on_sign(ow, s)


static func on_hidden(ow: Overworld, h: Dictionary) -> void:
	if await StoryA.on_hidden(ow, h) or await StoryB.on_hidden(ow, h) or await StoryC.on_hidden(ow, h):
		return
	match h.handler:
		"OpenPokemonCenterPC", "OpenRedsPC", "BillsHousePC":
			await Menus.pc()
		"HiddenItems":
			var key := "hidden:%s:%d:%d" % [ow.map_id, h.x, h.y]
			if G.flag(key):
				return
			G.set_flag(key)
			G.add_item(h.arg)
			await UI.say("{PLAYER}{은} %s{을} 찾았다!" % DB.item_name(h.arg))
		"PrintRedSNESText":
			await UI.say("{PLAYER}{은} 슈퍼패미컴을 하고 있다!\f...좋아!\n이제 슬슬 가 볼까!")
		"PrintBookcaseText":
			await UI.say("포켓몬에 관한 책이 가득 꽂혀 있다!")
		"DisplayOakLabLeftPoster":
			await UI.say("START 버튼(Enter)을 누르면 메뉴가 열린다!")
		"DisplayOakLabRightPoster":
			await UI.say("메뉴의 레포트를 고르면 게임을 저장할 수 있다!")
		"DisplayOakLabEmailText":
			await UI.say("이메일이 와 있다!\f...\f포켓몬 트레이너 여러분께!\f최고의 트레이너들이 포켓몬 리그에서 기다리고 있습니다!\f- 포켓몬 리그 사무국")
		"PrintBenchGuyText":
			await UI.say("포켓몬센터에서 쉬어 가는 것도 좋지!")
		"PrintMagazinesText":
			await UI.say("포켓몬 잡지가 잔뜩 있다!")
		"PrintTrashText":
			await UI.say("아무것도 없다... 쓰레기통이다.")
		"GymStatues":
			await Gyms.statue(ow)
		_:
			pass


# ------------------------------------------------------------------ 대화
static func on_talk(ow: Overworld, a: Actor) -> bool:
	var id: String = a.data.get("id", "")
	if await Gyms.on_talk(ow, a) or await StoryA.on_talk(ow, a) or await StoryB.on_talk(ow, a) or await StoryC.on_talk(ow, a):
		return true
	match id:
		"REDSHOUSE1F_MOM":
			await _mom()
			return true
		"BLUESHOUSE_DAISY1":
			if G.flag("got_pokedex") and not G.flag("got_town_map"):
				await UI.say("할아버지께 심부름을 부탁받았다고?\f그럼 이걸 가져가!\n분명 도움이 될 거야.")
				G.set_flag("got_town_map")
				G.add_item("TOWN_MAP")
				var tm := ow.find_npc("BLUESHOUSE_TOWN_MAP")
				if tm:
					G.set_object_visible("BLUESHOUSE_TOWN_MAP", false)
					ow.npcs.erase(tm)
					tm.queue_free()
				await UI.say("{PLAYER}{은} 타운맵을 받았다!")
				return true
			if G.flag("got_town_map"):
				await UI.say(DB.text("_BluesHouseDaisyWalkingText"))
				return true
		"BLUESHOUSE_TOWN_MAP":
			await UI.say(DB.text("_BluesHouseTownMapText"))
			return true
		"ROUTE1_YOUNGSTER1":
			if not G.flag("got_potion_sample"):
				await UI.say("안녕! 나는 포켓몬마트에서 일해.\f상록시티에 있는 파란 지붕 가게야!\f그래! 샘플을 줄게!\n이거 가져가!")
				G.add_item("POTION")
				G.set_flag("got_potion_sample")
				await UI.say("{PLAYER}{은} 상처약을 받았다!")
			else:
				await UI.say("상록시티의 포켓몬마트에 들러 줘!")
			return true
		"OAKSLAB_RIVAL":
			if not G.flag("oak_intro"):
				await UI.say("{RIVAL}: 여, {PLAYER}!\n할아버지는 안 계셔!")
			elif not G.flag("got_starter"):
				await UI.say("{RIVAL}: 헤헤, 나는 좋은 포켓몬을 고를 거야!")
			else:
				await UI.say("{RIVAL}: 내 포켓몬이 더 강해 보이지?")
			return true
		"OAKSLAB_OAK1", "OAKSLAB_OAK2":
			await _oak_talk(ow)
			return true
		"VIRIDIANMART_CLERK":
			if not G.flag("parcel_delivered"):
				await UI.say("오박사님께 안부 전해 줘!")
				return true
		"VIRIDIANCITY_OLD_MAN_SLEEPY":
			await UI.say(DB.map_text("VIRIDIAN_CITY", "TEXT_VIRIDIANCITY_OLD_MAN_SLEEPY"))
			return true
	if STARTERS.has(id):
		await _starter_ball(ow, a)
		return true
	return false


static func _mom() -> void:
	if not G.flag("got_starter"):
		await UI.say("엄마: ...그래.\n남자아이는 언젠가 집을 떠나는 법이지.\fTV에서 그러더라.\f오박사님이 옆집에서 너를 찾으시던데?")
		return
	await UI.say("엄마: {PLAYER}!\n포켓몬이랑 같이 있으니 든든하구나!\f좀 쉬었다 가렴.")
	await UI.fade_out(0.3)
	G.heal_party()
	G.heal_map = "REDS_HOUSE_1F"
	G.heal_pos = Vector2i(5, 5)
	G.flags["heal_outdoor"] = "PALLET_TOWN"
	await UI.wait(0.5)
	await UI.fade_in(0.3)
	await UI.say("엄마: 오, {PLAYER}!\n포켓몬들이 아주 건강해 보이는구나!\f조심해서 다녀오렴!")


# ------------------------------------------------------------------ 태초마을: 오박사 등장
static func _oak_stops_you(ow: Overworld) -> void:
	await UI.say("오박사: 잠깐! 기다려!\n나가면 안 된다!")
	await ow.show_emote(ow.player)
	ow.player.set_facing(Vector2i.DOWN)
	# 오박사가 풀숲 앞에서 걸어옴
	var oak := Actor.new()
	ow.world.add_child(oak)
	var start := ow.player.cell + Vector2i(0, 4)
	oak.setup("oak", start, Vector2i.UP)
	while oak.cell.y > ow.player.cell.y + 1:
		await oak.step(Vector2i.UP)
	await UI.say("오박사: 위험하단다!\n풀숲에는 야생 포켓몬이 살고 있어!\f너를 지켜 줄 포켓몬이 필요하겠구나.\f그래! 나를 따라오너라!")
	G.set_flag("oak_intro")
	G.set_object_visible("OAKSLAB_OAK1", true)
	await ow.teleport_to("OAKS_LAB", Vector2i(5, 3), Vector2i.UP)
	await UI.say("{RIVAL}: 할아버지!\n기다리다 지쳤어요!")
	await UI.say("오박사: {RIVAL}? 아, 그렇지!\n내가 불렀었지! 잠깐 기다려라!\f여기 포켓몬이 세 마리 있단다!\f하하! 몬스터볼 안에 들어 있지.\f나도 젊었을 때는 대단한 포켓몬 트레이너였단다!\f이제 나이가 들어서 이 셋만 남았지만\n하나를 너에게 주마!\f자, {PLAYER}! 골라 보렴!")
	await UI.say("{RIVAL}: 에이! 할아버지!\n나는요?")
	await UI.say("오박사: 서두르지 마라, {RIVAL}!\n너도 하나 고를 수 있단다!")


static func _starter_ball(ow: Overworld, a: Actor) -> void:
	var id: String = a.data.id
	var sp: String = STARTERS[id]
	if not G.flag("oak_intro"):
		await UI.say("오박사의 포켓몬이 들어 있는 몬스터볼이다.\n함부로 만지면 안 되겠지.")
		return
	if G.flag("got_starter"):
		await UI.say("마지막 남은 포켓몬이다.\n오박사가 소중히 보관하고 있다.")
		return
	var pic := TextureRect.new()
	pic.texture = Mon.front_tex(sp)
	var box := GBBox.new(Rect2(48, 16, 64, 64))
	pic.position = Vector2(4, 4)
	box.add_child(pic)
	UI.root().add_child(box)
	await UI.say("%s 포켓몬 %s{을} 고를 거니?" % [STARTER_DESC[sp], DB.mon_name(sp)], true, false)
	var ok: bool = await UI.yes_no()
	box.queue_free()
	if not ok:
		UI.close_box()
		return
	await UI.say("이 포켓몬은 정말 기운이 넘친단다!", true)
	var m := Mon.create(sp, 5, G.player_name)
	G.give_mon(m)
	G.set_flag("got_starter")
	G.flags["starter"] = sp
	G.set_object_visible(id, false)
	ow.npcs.erase(a)
	a.queue_free()
	await UI.say("{PLAYER}{은} 오박사에게서\n%s{을} 받았다!" % DB.mon_name(sp), true)
	var nick := await UI.text_input("%s에게 별명을 지어 줄까? (빈칸이면 그대로)" % DB.mon_name(sp), "", 10)
	if nick != "":
		m.nick = nick
	UI.close_box()
	# 라이벌 선택
	var rival_ball_id: String = RIVAL_PICK[sp]
	var rival_sp: String = STARTERS[rival_ball_id]
	G.flags["rival_starter"] = rival_sp
	var rival := ow.find_npc("OAKSLAB_RIVAL")
	var ball := ow.find_npc(rival_ball_id)
	await UI.say("{RIVAL}: 그럼 나는 이걸로 할래!")
	if rival and ball:
		var target: Vector2i = ball.cell + Vector2i.DOWN
		while rival.cell.y < target.y:
			await rival.step(Vector2i.DOWN)
		while rival.cell.x < target.x:
			await rival.step(Vector2i.RIGHT)
		rival.set_facing(Vector2i.UP)
		G.set_object_visible(rival_ball_id, false)
		ow.npcs.erase(ball)
		ball.queue_free()
	await UI.say("{RIVAL}{은} 오박사에게서\n%s{을} 받았다!" % DB.mon_name(rival_sp))


static func _rival_battle(ow: Overworld) -> void:
	var rival := ow.find_npc("OAKSLAB_RIVAL")
	await UI.say("{RIVAL}: 잠깐, {PLAYER}!\n우리 포켓몬 실력 좀 확인해 보자!\f자, 덤벼!")
	if rival:
		while rival.cell.y < ow.player.cell.y - 1:
			await rival.step(Vector2i.DOWN)
		while rival.cell.x != ow.player.cell.x:
			await rival.step(Vector2i.RIGHT if rival.cell.x < ow.player.cell.x else Vector2i.LEFT)
		rival.set_facing(Vector2i.DOWN)
		ow.player.set_facing(Vector2i.UP)
	var res: String = await ow.start_battle({
		"kind": "trainer", "class": "RIVAL1", "index": RIVAL_PARTY[G.flags.get("rival_starter", "SQUIRTLE")],
		"end_text": "{RIVAL}: 뭐야?\n내가 고른 포켓몬이 더 약했나?", "lose_text": "{RIVAL}: 야호!\n역시 내 포켓몬이 최고야!",
		"no_blackout": true,
	})
	G.heal_party()
	G.set_flag("rival_battle1")
	await UI.say("{RIVAL}: 좋아! 포켓몬을 더 싸우게 해서 강하게 만들어야지!\f{PLAYER}! 할아버지!\n안녕!")
	if rival:
		while rival.cell.y < 11:
			var nxt := rival.cell + Vector2i.DOWN
			if nxt == ow.player.cell:
				await rival.step(Vector2i.LEFT if rival.cell.x > 1 else Vector2i.RIGHT)
				continue
			await rival.step(Vector2i.DOWN)
		G.set_object_visible("OAKSLAB_RIVAL", false)
		ow.npcs.erase(rival)
		rival.queue_free()
	if res == "lose":
		await UI.say("오박사: 포켓몬이 지쳤구나.\n회복시켜 주마.")


# ------------------------------------------------------------------ 소포 / 도감
static func _parcel(_ow: Overworld) -> void:
	await UI.say(DB.text("_ViridianMartClerkYouCameFromPalletTownText"))
	await UI.say(DB.text("_ViridianMartClerkParcelQuestText"))
	G.add_item("OAKS_PARCEL")
	G.set_flag("got_parcel")


static func _oak_talk(ow: Overworld) -> void:
	if not G.flag("got_starter"):
		await UI.say("오박사: 자, {PLAYER}!\n마음에 드는 포켓몬을 골라 보렴!")
		return
	if G.bag.has("OAKS_PARCEL"):
		await _deliver_parcel(ow)
		return
	if not G.flag("got_pokedex"):
		await UI.say("오박사: {PLAYER}, 야생 포켓몬이 나타나면\n네 포켓몬으로 싸울 수 있단다!\f상록시티에 한번 가 보렴.")
		return
	await UI.say("오박사: 포켓몬 도감은 어떠냐?\f지금까지 발견한 포켓몬이 %d마리,\n잡은 포켓몬이 %d마리로구나!\f%s" % [G.seen.size(), G.caught.size(), _dex_comment(G.caught.size())])
	if G.bag.get("POKE_BALL", 0) == 0 and not G.flag("oak_extra_balls"):
		G.set_flag("oak_extra_balls")
		G.add_item("POKE_BALL", 5)
		await UI.say("몬스터볼이 떨어졌니?\n자, 이걸 가져가거라!\f{PLAYER}{은} 몬스터볼 5개를 받았다!")


static func _dex_comment(n: int) -> String:
	if n < 10:
		return "아직 멀었구나! 풀숲을 잘 찾아보렴!"
	if n < 30:
		return "좋아! 그 기세로 계속하렴!"
	if n < 60:
		return "훌륭하구나! 나도 기쁘다!"
	return "대단하구나! 너라면 도감을 완성할 수 있을 게다!"


static func _deliver_parcel(ow: Overworld) -> void:
	await UI.say("오박사: 오, {PLAYER}!\n내 포켓몬은 어떠냐?\f응? 나에게 줄 물건이 있다고?\f{PLAYER}{은} 오박사의 소포를 전해 주었다.\f오! 주문해 둔 특제 몬스터볼이구나!\n고맙다!")
	G.remove_item("OAKS_PARCEL")
	G.set_flag("parcel_delivered")
	await UI.say("{RIVAL}: 할아버지!")
	await UI.say("{RIVAL}: 불러서 왔는데, 무슨 일이에요?")
	await UI.say("오박사: 아, 그렇지! 너희 둘에게 부탁이 있단다.\f책상 위에 있는 것이 내 발명품인 포켓몬 도감이다!\f발견하거나 잡은 포켓몬의 데이터를 자동으로 기록해 주는\n최첨단 백과사전이지!")
	await UI.say("오박사: {PLAYER}, {RIVAL}!\n이걸 가져가거라!\f{PLAYER}{은} 오박사에게서\n포켓몬 도감을 받았다!")
	G.set_flag("got_pokedex")
	G.add_item("POKE_BALL", 5)
	for obj in ["OAKSLAB_POKEDEX1", "OAKSLAB_POKEDEX2"]:
		G.set_object_visible(obj, false)
		var a := ow.find_npc(obj)
		if a:
			ow.npcs.erase(a)
			a.queue_free()
	await UI.say("{PLAYER}{은} 몬스터볼 5개도 받았다!")
	await UI.say("오박사: 세상의 모든 포켓몬을 기록한 완벽한 도감을 만드는 것...\f그게 나의 꿈이었단다!\f하지만 나는 너무 늙었어.\f그래서 너희가 내 꿈을 이뤄 줬으면 한다!\f자, 떠나거라!\f이것은 포켓몬 역사에 남을 위대한 일이란다!")
	await UI.say("{RIVAL}: 알았어요, 할아버지!\n다 맡겨 두세요!\f{PLAYER}, 이런 말 하긴 그렇지만\n너는 필요 없어!\f그래! 누나한테 타운맵을 빌려야지!\f너한텐 빌려주지 말라고 해 둘게!\n하하하!")
	# 상록시티 할아버지가 길을 비킴
	G.set_object_visible("VIRIDIANCITY_OLD_MAN_SLEEPY", false)
	G.set_object_visible("VIRIDIANCITY_OLD_MAN", true)
