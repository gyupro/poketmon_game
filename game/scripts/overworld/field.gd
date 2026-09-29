class_name Field
extends RefCounted
## 필드 기술(비전머신)과 필드 아이템: 풀베기, 파도타기, 괴력, 플래시, 공중날기, 구멍파기, 순간이동,
## 알까기, 자전거, 낚싯대, 기술머신, 동굴탈출로프, 다우징머신, 포켓몬 피리.

const FIELD_MOVES := ["CUT", "FLY", "SURF", "STRENGTH", "FLASH", "DIG", "TELEPORT", "SOFTBOILED"]
const MOVE_BADGE := {
	"CUT": "CASCADEBADGE", "FLY": "THUNDERBADGE", "SURF": "SOULBADGE",
	"STRENGTH": "RAINBOWBADGE", "FLASH": "BOULDERBADGE",
}
const DIRS := {"UP": Vector2i.UP, "DOWN": Vector2i.DOWN, "LEFT": Vector2i.LEFT, "RIGHT": Vector2i.RIGHT}


static func mon_field_moves(m: Dictionary) -> Array:
	var out := []
	for mv in m.moves:
		if FIELD_MOVES.has(mv.id):
			out.append(mv.id)
	return out


static func party_knows(move: String) -> int:
	for i in G.party.size():
		if Mon.has_move(G.party[i], move):
			return i
	return -1


static func _badge_ok(move: String) -> bool:
	return not MOVE_BADGE.has(move) or G.bag.has(MOVE_BADGE[move])


## 파티 메뉴에서 기술 사용. 반환: 메뉴를 닫아야 하면 true
static func use_move(ow: Overworld, idx: int, move: String) -> bool:
	var m: Dictionary = G.party[idx]
	if not _badge_ok(move):
		await UI.say("새로운 배지를 얻을 때까지\n그 기술은 밖에서 쓸 수 없다!")
		return false
	match move:
		"CUT":
			return await try_cut(ow, m)
		"SURF":
			return await try_surf(ow, m)
		"STRENGTH":
			G.set_flag("strength_on")
			await UI.say("%s{은} 괴력을 썼다!\f바위를 움직일 수 있게 되었다!" % Mon.name_of(m))
			return true
		"FLASH":
			if not Overworld.DARK_MAPS.has(ow.map_id) or G.flag("flash"):
				await UI.say("지금은 쓸 필요가 없다.")
				return false
			G.set_flag("flash")
			ow._update_dark()
			await UI.say("%s{은} 플래시를 썼다!\n주변이 밝아졌다!" % Mon.name_of(m))
			return true
		"FLY":
			return await fly(ow)
		"DIG", "TELEPORT":
			if move == "DIG" and not can_escape(ow):
				await UI.say("여기서는 쓸 수 없다!")
				return false
			if move == "TELEPORT" and not ow.map.outdoor and not can_escape(ow):
				await UI.say("여기서는 쓸 수 없다!")
				return false
			await UI.say("%s{은} %s{을} 썼다!" % [Mon.name_of(m), DB.move_name(move)])
			await escape_to_center(ow)
			return true
		"SOFTBOILED":
			if m.hp <= m.max_hp / 5:
				await UI.say("체력이 부족하다!")
				return false
			await UI.say("누구에게 쓸까?", true, false)
			var t: int = await Menus.party_menu("select", -1)
			UI.close_box()
			if t < 0 or t == idx:
				return false
			var tm: Dictionary = G.party[t]
			if tm.hp <= 0 or tm.hp >= tm.max_hp:
				await UI.say("효과가 없을 것 같다.")
				return false
			var amt := mini(m.max_hp / 5, tm.max_hp - tm.hp)
			m.hp -= m.max_hp / 5
			tm.hp += amt
			Sound.sfx("Heal_HP")
			await UI.say("%s의 체력이 %d 회복되었다!" % [Mon.name_of(tm), amt])
			return false
	return false


# ------------------------------------------------------------------ 풀베기
static func cut_target(ow: Overworld) -> int:
	var front := ow.player.cell + ow.player.facing
	var t := ow.tile_at(front)
	if (ow.map.tileset == "OVERWORLD" and (t == 0x3D or t == 0x52)) or (ow.map.tileset == "GYM" and t == 0x50):
		return ow.block_index(front)
	return -1


static func try_cut(ow: Overworld, m: Dictionary) -> bool:
	var bidx := cut_target(ow)
	if bidx < 0:
		await UI.say("여기에는 벨 것이 없다!")
		return false
	var cur: int = ow.map.blk[bidx]
	var nb := -1
	for pair in DB.extra.cut_trees:
		if pair[0] == cur:
			nb = pair[1]
	await UI.say("%s{은} 풀베기를 썼다!" % Mon.name_of(m))
	Sound.sfx("Cut")
	if nb >= 0:
		ow.set_block(bidx, nb, false)
	return true


# ------------------------------------------------------------------ 파도타기
static func try_surf(ow: Overworld, m: Dictionary) -> bool:
	if G.flag("surfing"):
		await UI.say("이미 파도타기 중이다!")
		return false
	if G.flag("forced_bike"):
		await UI.say("사이클링로드에서는 자전거를 타야 한다!")
		return false
	var front := ow.player.cell + ow.player.facing
	if not ow.is_water(front) or ow.npc_at(front) != null:
		await UI.say("여기서는 파도타기를 할 수 없다!")
		return false
	if ow.map_id == "SEAFOAM_ISLANDS_B4F" and not (G.flag("seafoam_b4f_boulder1") and G.flag("seafoam_b4f_boulder2")) and ow.player.cell == Vector2i(7, 11):
		await UI.say("물살이 너무 빠르다!")
		return false
	await UI.say("%s{을} 타고 파도를 건넌다!" % Mon.name_of(m))
	G.flags.erase("biking")
	G.set_flag("surfing")
	ow.refresh_player_sprite()
	Sound.music("Surfing")
	await ow.player.step(ow.player.facing)
	G.pos = ow.player.cell
	Net.send_state()
	return true


## A 버튼으로 앞의 나무/물에 바로 필드 기술 쓰기
static func interact_front(ow: Overworld) -> void:
	if await StoryB.try_card_key(ow):
		return
	if cut_target(ow) >= 0 and ow.tile_at(ow.player.cell + ow.player.facing) != 0x52:
		var i := party_knows("CUT")
		if i < 0 or not _badge_ok("CUT"):
			await UI.say("이 나무는 벨 수 있을 것 같다!")
			return
		await UI.say("이 나무는 벨 수 있을 것 같다!\n풀베기를 쓸까?", true, false)
		if await UI.yes_no():
			UI.close_box()
			await try_cut(ow, G.party[i])
		else:
			UI.close_box()
		return
	var front := ow.player.cell + ow.player.facing
	if not G.flag("surfing") and ow.is_water(front) and ow.npc_at(front) == null:
		var j := party_knows("SURF")
		if j < 0 or not _badge_ok("SURF"):
			await UI.say("물이 푸르고 깊다...")
			return
		await UI.say("물이 푸르고 깊다...\n파도타기를 쓸까?", true, false)
		if await UI.yes_no():
			UI.close_box()
			await try_surf(ow, G.party[j])
		else:
			UI.close_box()


# ------------------------------------------------------------------ 자전거
static func toggle_bike(ow: Overworld) -> void:
	if G.flag("biking"):
		if G.flag("forced_bike"):
			await UI.say("사이클링로드에서는 내릴 수 없다!")
			return
		G.flags.erase("biking")
		ow.refresh_player_sprite()
		Sound.map_music(ow.map_id)
		await UI.say("{PLAYER}{은} 자전거에서 내렸다.")
		return
	if G.flag("surfing"):
		await UI.say("지금은 자전거를 탈 수 없다!")
		return
	if not DB.extra.bike_tilesets.has(ow.map.tileset):
		await UI.say("여기서는 자전거를 탈 수 없다!")
		return
	G.set_flag("biking")
	ow.refresh_player_sprite()
	Sound.music("BikeRiding")
	await UI.say("{PLAYER}{은} 자전거에 올라탔다!")


## 사이클링로드 입구·바다 물살 지점: 강제로 자전거/파도타기
static func check_forced_bike_surf(ow: Overworld) -> void:
	for f in DB.extra.force_bike_surf:
		if f[0] == ow.map_id and ow.player.cell == Vector2i(f[1], f[2]):
			if ow.map_id.begins_with("ROUTE_1"):
				# 게이트에서 나오면 자전거
				if G.bag.has("BICYCLE") and not G.flag("biking"):
					G.set_flag("biking")
					ow.refresh_player_sprite()
					Sound.music("BikeRiding")
			elif not G.flag("surfing"):
				G.set_flag("surfing")
				ow.refresh_player_sprite()
				Sound.music("Surfing")
	# 사이클링로드(16~18번도로)에서는 내릴 수 없음
	var on_road: bool = ow.map_id in ["ROUTE_17"] or (ow.map_id in ["ROUTE_16", "ROUTE_18"] and G.flag("biking") and ow.player.cell.x < 20)
	if on_road:
		G.set_flag("forced_bike")
	else:
		G.flags.erase("forced_bike")


# ------------------------------------------------------------------ 회전 타일
static func check_spinner(ow: Overworld) -> bool:
	var sp: Dictionary = DB.extra.spinners.get(ow.map.name, {})
	var key := "%d,%d" % [ow.player.cell.x, ow.player.cell.y]
	if not sp.has(key):
		return false
	var seq: Array = sp[key].duplicate()
	seq.reverse()
	Sound.sfx("Arrow_Tiles")
	for step in seq:
		var d: Vector2i = DIRS[step[0]]
		for i in int(step[1]):
			await ow.player.step(d, 2.0)
			_spin_face(ow)
	G.pos = ow.player.cell
	Net.send_state()
	return true


static func _spin_face(ow: Overworld) -> void:
	var order := [Vector2i.DOWN, Vector2i.LEFT, Vector2i.UP, Vector2i.RIGHT]
	var i := order.find(ow.player.facing)
	ow.player.set_facing(order[(i + 1) % 4])


# ------------------------------------------------------------------ 공중날기 / 탈출
static func fly(ow: Overworld) -> bool:
	if not ow.map.outdoor:
		await UI.say("여기서는 쓸 수 없다!")
		return false
	var visited: Array = G.flags.get("visited", [])
	var opts := []
	var keys := []
	for k in DB.extra.fly:
		if visited.has(k):
			opts.append(town_name(k))
			keys.append(k)
	if keys.is_empty():
		await UI.say("날아갈 수 있는 곳이 없다!")
		return false
	await UI.say("어디로 날아갈까?", true, false)
	var c: int = await UI.choose(opts, Rect2(40, 0, 120, mini(opts.size() * 14 + 10, 96)))
	UI.close_box()
	if c < 0:
		return false
	G.flags.erase("surfing")
	G.flags.erase("biking")
	Sound.sfx("Fly")
	var pos: Array = DB.extra.fly[keys[c]]
	await ow.teleport_to(keys[c], Vector2i(pos[0], pos[1]), Vector2i.DOWN)
	await Events.on_enter(ow)
	return true


const TOWN_NAMES := {
	"PALLET_TOWN": "태초마을", "VIRIDIAN_CITY": "상록시티", "PEWTER_CITY": "회색시티",
	"CERULEAN_CITY": "블루시티", "LAVENDER_TOWN": "보라타운", "VERMILION_CITY": "갈색시티",
	"CELADON_CITY": "무지개시티", "FUCHSIA_CITY": "연분홍시티", "CINNABAR_ISLAND": "홍련마을",
	"INDIGO_PLATEAU": "석영고원", "SAFFRON_CITY": "노랑시티", "ROUTE_4": "4번도로", "ROUTE_10": "10번도로",
}


static func town_name(k: String) -> String:
	return TOWN_NAMES.get(k, k)


static func mark_visited(map_id: String) -> void:
	if DB.extra.fly.has(map_id):
		var v: Array = G.flags.get("visited", [])
		if not v.has(map_id):
			v.append(map_id)
			G.flags["visited"] = v


static func can_escape(ow: Overworld) -> bool:
	return not ow.map.outdoor and DB.extra.escape_rope_tilesets.has(ow.map.tileset)


static func escape_to_center(ow: Overworld) -> void:
	var town: String = G.flags.get("heal_outdoor", "PALLET_TOWN")
	if not DB.extra.fly.has(town):
		town = "PALLET_TOWN"
	var pos: Array = DB.extra.fly[town]
	G.flags.erase("surfing")
	G.flags.erase("biking")
	Sound.sfx("Teleport_Exit1")
	await ow.teleport_to(town, Vector2i(pos[0], pos[1]), Vector2i.DOWN)
	await Events.on_enter(ow)


# ------------------------------------------------------------------ 낚시
static func fish(ow: Overworld, rod: String) -> void:
	var front := ow.player.cell + ow.player.facing
	if not ow.is_water(front):
		await UI.say("여기서는 낚시를 할 수 없다!")
		return
	await UI.say("{PLAYER}{은} %s{을} 던졌다!" % DB.item_name(rod), true)
	await UI.wait(0.8)
	var mon := []
	match rod:
		"OLD_ROD":
			mon = [5, "MAGIKARP"]
		"GOOD_ROD":
			if randi() % 2 == 0:
				mon = DB.extra.good_rod.pick_random()
		"SUPER_ROD":
			var grp: Array = DB.extra.super_rod.get(ow.map_id, [])
			if not grp.is_empty() and randi() % 4 != 0:
				mon = grp.pick_random()
	if mon.is_empty():
		await UI.say("아무것도 걸리지 않았다...")
		return
	await UI.say("앗!\n무언가 걸렸다!")
	await ow.start_battle({"kind": "wild", "species": mon[1], "level": mon[0]})


# ------------------------------------------------------------------ 기술머신
static func tm_compatible(m: Dictionary, move: String) -> bool:
	return DB.pokemon[m.species].tmhm.has(move)


static func use_tm(item: String) -> void:
	var it: Dictionary = DB.items[item]
	var mv: String = it.move
	Sound.sfx("Turn_On_PC")
	await UI.say("%s{을} 켰다!\f안에는 %s{이} 들어 있다!\f%s{을} 포켓몬에게 가르칠까?" % [DB.item_name(item), DB.move_name(mv), DB.move_name(mv)], true, false)
	if not await UI.yes_no():
		UI.close_box()
		return
	UI.close_box()
	while true:
		var t: int = await Menus.party_menu("select", -1)
		if t < 0:
			return
		var m: Dictionary = G.party[t]
		if not tm_compatible(m, mv):
			await UI.say("%s{은} %s{을} 배울 수 없다!" % [Mon.name_of(m), DB.move_name(mv)])
			continue
		if Mon.has_move(m, mv):
			await UI.say("%s{은} 이미 %s{을} 알고 있다!" % [Mon.name_of(m), DB.move_name(mv)])
			continue
		await Battle.learn_move_flow(m, mv)
		UI.close_box()
		if Mon.has_move(m, mv) and it.has("tm"):
			G.remove_item(item)
		return


# ------------------------------------------------------------------ 기타 필드 아이템
static func use_key_item(ow: Overworld, item: String) -> bool:
	match item:
		"BICYCLE":
			await toggle_bike(ow)
			return true
		"OLD_ROD", "GOOD_ROD", "SUPER_ROD":
			await fish(ow, item)
			return true
		"ESCAPE_ROPE":
			if not can_escape(ow):
				await UI.say("여기서는 쓸 수 없다!")
				return false
			G.remove_item(item)
			await UI.say("{PLAYER}{은} 동굴탈출로프를 썼다!")
			await escape_to_center(ow)
			return true
		"ITEMFINDER":
			var found := false
			for h in ow.map.hidden:
				if h.handler == "HiddenItems" and not G.flag("hidden:%s:%d:%d" % [ow.map_id, h.x, h.y]):
					if absi(h.x - ow.player.cell.x) <= 5 and absi(h.y - ow.player.cell.y) <= 4:
						found = true
			if found:
				Sound.sfx("Tink")
				await UI.say("다우징머신이 반응하고 있다!\n근처에 무언가 숨겨져 있다!")
			else:
				await UI.say("다우징머신이 반응하지 않는다.")
			return false
		"POKE_FLUTE":
			if await Events.use_poke_flute(ow):
				return true
			await Sound.sfx_wait("Pokeflute")
			await UI.say("{PLAYER}{은} 포켓몬 피리를 불었다!\f흥겨운 멜로디가 울려 퍼진다!")
			return false
		"COIN_CASE":
			await UI.say("코인: %d개" % int(G.flags.get("coins", 0)))
			return false
		"TOWN_MAP":
			await UI.say("관동 지방의 지도다!\n지금 %s 근처에 있다." % town_name(G.last_outdoor))
			return false
	return false
