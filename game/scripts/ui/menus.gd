class_name Menus
extends RefCounted
## 메뉴 화면 모음 (시작 메뉴, 포켓몬, 가방, 요약, 도감, 센터, 마트, PC).

const HEAL_ITEMS := {"POTION": 20, "SUPER_POTION": 50, "HYPER_POTION": 200, "MAX_POTION": 9999, "FULL_RESTORE": 9999}
const STATUS_ITEMS := {"ANTIDOTE": ["PSN"], "BURN_HEAL": ["BRN"], "ICE_HEAL": ["FRZ"], "AWAKENING": ["SLP"], "PARLYZ_HEAL": ["PAR"], "FULL_HEAL": ["PSN", "BRN", "FRZ", "SLP", "PAR"]}
const KEY_ITEMS := ["TOWN_MAP", "BICYCLE", "POKEDEX", "OAKS_PARCEL", "S_S_TICKET", "SECRET_KEY", "CARD_KEY", "SILPH_SCOPE", "POKE_FLUTE", "LIFT_KEY", "BIKE_VOUCHER", "GOLD_TEETH", "COIN_CASE", "ITEMFINDER", "EXP_ALL", "OLD_ROD", "GOOD_ROD", "SUPER_ROD"]


static func _screen() -> Control:
	var c := ColorRect.new()
	c.color = Color.WHITE
	c.size = Vector2(160, 144)
	UI.root().add_child(c)
	return c


# ------------------------------------------------------------------ 시작 메뉴
static func start_menu(ow: Overworld) -> void:
	var idx := 0
	while true:
		var opts := []
		var keys := []
		if G.flag("got_pokedex"):
			opts.append("포켓몬 도감"); keys.append("dex")
		if not G.party.is_empty():
			opts.append("포켓몬"); keys.append("party")
		opts.append("가방"); keys.append("bag")
		opts.append(G.player_name); keys.append("card")
		opts.append("레포트"); keys.append("save")
		opts.append("통신"); keys.append("net")
		opts.append("닫기"); keys.append("close")
		var c: int = await UI.choose(opts, Rect2(80, 0, 80, opts.size() * 14 + 10), idx)
		if c < 0 or keys[c] == "close":
			return
		idx = c
		match keys[c]:
			"dex": await pokedex()
			"party":
				if await party_menu("field", -1) == -2:
					return
			"bag":
				if (await bag_menu("field")).get("close", false):
					return
			"card": await trainer_card()
			"save":
				await UI.say("지금까지의 활약을 레포트에 기록할까?", true, false)
				if await UI.yes_no():
					G.pos = ow.player.cell
					G.facing = ow.player.facing
					if G.save_game():
						await UI.say("{PLAYER}{은} 레포트를 작성했다!")
					else:
						await UI.say("저장에 실패했다...")
				else:
					UI.close_box()
				return
			"net":
				await Multi.net_menu(ow)
				return


# ------------------------------------------------------------------ 포켓몬 리스트
## mode: field | battle | forced | select
static func party_menu(mode: String, active_idx := -1, party: Array = G.party) -> int:
	var scr := _screen()
	var rows := []
	var result := -1
	var swap_from := -1
	var idx := maxi(active_idx, 0)
	var cursor := GBBox.label("▶", Vector2.ZERO, 8)
	var hint := GBBox.new(Rect2(0, 122, 160, 22))
	var hint_l := GBBox.label("", Vector2(8, 5))
	hint.add_child(hint_l)
	scr.add_child(hint)
	var redraw := func():
		for r in rows:
			r.queue_free()
		rows.clear()
		for i in party.size():
			var m: Dictionary = party[i]
			var row := Control.new()
			row.position = Vector2(0, i * 20 + 1)
			scr.add_child(row)
			rows.append(row)
			var nl := GBBox.label(Mon.name_of(m), Vector2(12, -1))
			row.add_child(nl)
			var st := BattleCore.STATUS_KO.get(m.status, "") if m.hp > 0 else "기절"
			row.add_child(GBBox.label(st if st != "" else "Lv%d" % m.level, Vector2(80, -1)))
			var bar := HPBar.new(Vector2(12, 13), 48)
			bar.ratio = float(m.hp) / m.max_hp
			row.add_child(bar)
			row.add_child(GBBox.label("%3d/%3d" % [m.hp, m.max_hp], Vector2(104, 8)))
			if i == swap_from:
				nl.add_theme_color_override("font_color", Color(0.2, 0.4, 0.9))
	redraw.call()
	scr.add_child(cursor)
	UI.busy += 1
	await UI.frame()
	while true:
		hint_l.text = "포켓몬을 골라 주세요." if swap_from < 0 else "어디로 옮길까요?"
		if party.is_empty():
			break
		cursor.position = Vector2(2, idx * 20 + 3)
		await UI.frame()
		if UI.pressed("down"):
			idx = (idx + 1) % party.size()
		elif UI.pressed("up"):
			idx = (idx - 1 + party.size()) % party.size()
		elif UI.pressed("b") and mode != "forced":
			if swap_from >= 0:
				swap_from = -1
				redraw.call()
				continue
			break
		elif UI.pressed("a"):
			if swap_from >= 0:
				var tmp = party[swap_from]
				party[swap_from] = party[idx]
				party[idx] = tmp
				swap_from = -1
				redraw.call()
				continue
			if mode == "forced" or mode == "select":
				result = idx
				break
			var opts := ["교체", "정보", "취소"] if mode == "battle" else ["정보", "순서 바꾸기", "취소"]
			var fm := []
			if mode == "field":
				fm = Field.mon_field_moves(party[idx])
				for i in fm.size():
					opts.insert(i, DB.move_name(fm[i]))
			var c: int = await UI.choose(opts, Rect2(88, 144 - (opts.size() * 14 + 10), 72, opts.size() * 14 + 10))
			var pick: String = opts[c] if c >= 0 else "취소"
			if c >= 0 and c < fm.size():
				UI.busy -= 1
				scr.visible = false
				var close: bool = await Field.use_move(Main.inst.ow, idx, fm[c])
				scr.visible = true
				UI.busy += 1
				if close:
					result = -2
					break
				redraw.call()
				continue
			if pick == "교체":
				result = idx
				break
			elif pick == "정보":
				await summary(party, idx)
			elif pick == "순서 바꾸기":
				swap_from = idx
				redraw.call()
	UI.busy -= 1
	scr.queue_free()
	return result


static func summary(party: Array, idx: int) -> void:
	var page := 0
	UI.busy += 1
	while true:
		var m: Dictionary = party[idx]
		var scr := _screen()
		var pic := TextureRect.new()
		pic.texture = Mon.front_tex(m.species)
		pic.position = Vector2(4, 4)
		scr.add_child(pic)
		var b: Dictionary = DB.pokemon[m.species]
		scr.add_child(GBBox.label("No.%03d" % b.dex, Vector2(4, 60), 8))
		scr.add_child(GBBox.label(Mon.name_of(m), Vector2(68, 2)))
		scr.add_child(GBBox.label("Lv%d  %s" % [m.level, BattleCore.STATUS_KO.get(m.status, "정상") if m.hp > 0 else "기절"], Vector2(68, 14)))
		var bar := HPBar.new(Vector2(68, 30), 48)
		bar.ratio = float(m.hp) / m.max_hp
		scr.add_child(bar)
		scr.add_child(GBBox.label("HP %d/%d" % [m.hp, m.max_hp], Vector2(68, 36)))
		var types := []
		for t in b.types:
			types.append(DB.type_name(t))
		scr.add_child(GBBox.label("타입: " + "/".join(types), Vector2(68, 48)))
		if page == 0:
			scr.add_child(GBBox.label("공격   %3d\n방어   %3d\n스피드 %3d\n특수   %3d" % [m.atk_stat, m.def_stat, m.spd_stat, m.spc_stat], Vector2(4, 74)))
			scr.add_child(GBBox.label("어버이\n%s\n경험치\n%d\n다음Lv까지\n%d" % [m.ot, m.exp, Mon.exp_to_next(m)], Vector2(84, 62), 8))
		else:
			for i in m.moves.size():
				var mv: Dictionary = m.moves[i]
				scr.add_child(GBBox.label(DB.move_name(mv.id), Vector2(8, 72 + i * 15)))
				scr.add_child(GBBox.label("%s %2d/%2d" % [DB.type_name(DB.moves[mv.id].type), mv.pp, mv.max], Vector2(100, 74 + i * 15), 8))
		scr.add_child(GBBox.label("◀▶ 페이지  ▲▼ 포켓몬", Vector2(44, 134), 7))
		await UI.frame()
		var done := false
		while true:
			await UI.frame()
			if UI.pressed("b") or UI.pressed("a") and page == 1:
				done = true
				break
			if UI.pressed("a") or UI.pressed("right") or UI.pressed("left"):
				page = 1 - page
				break
			if UI.pressed("down") and party.size() > 1:
				idx = (idx + 1) % party.size()
				break
			if UI.pressed("up") and party.size() > 1:
				idx = (idx - 1 + party.size()) % party.size()
				break
		scr.queue_free()
		if done:
			break
	UI.busy -= 1


# ------------------------------------------------------------------ 가방
## field: 사용/버리기. battle: {"item", "target"} 반환
static func bag_menu(mode: String) -> Dictionary:
	var idx := 0
	while true:
		var keys := G.bag.keys().filter(func(k): return not G.BADGES.has(k))
		var opts := []
		for k in keys:
			opts.append("%s ×%d" % [DB.item_name(k), G.bag[k]] if not k in KEY_ITEMS else DB.item_name(k))
		opts.append("닫기")
		var c: int = await UI.choose(opts, Rect2(24, 0, 136, mini(opts.size() * 14 + 10, 96)), idx)
		if c < 0 or c == keys.size():
			UI.close_box()
			return {}
		idx = c
		var item: String = keys[c]
		var r: Dictionary = await use_item(item, mode)
		if r.get("done", false) or r.get("close", false):
			UI.close_box()
			return r
	return {}


static func use_item(item: String, mode: String) -> Dictionary:
	if mode == "field":
		var c: int = await UI.choose(["사용", "버리기"], Rect2(96, 96, 64, 48))
		if c < 0:
			return {}
		if c == 1:
			if item in KEY_ITEMS:
				await UI.say("그건 중요한 물건이야!")
				return {}
			var n: int = await UI.number(G.bag[item], Rect2(104, 80, 56, 22))
			if n > 0:
				G.remove_item(item, n)
				await UI.say("%s{을} 버렸다." % DB.item_name(item))
			return {}
	if item.ends_with("_BALL"):
		if mode != "battle":
			await UI.say("지금은 쓸 수 없다!")
			return {}
		return {"done": true, "item": item}
	if HEAL_ITEMS.has(item) or STATUS_ITEMS.has(item) or item in ["REVIVE", "MAX_REVIVE", "RARE_CANDY"] or item.ends_with("_STONE") or item in ["HP_UP", "PROTEIN", "IRON", "CARBOS", "CALCIUM"]:
		var t: int = await party_menu("select", -1)
		if t < 0:
			return {}
		var m: Dictionary = G.party[t]
		var ok := false
		if HEAL_ITEMS.has(item):
			ok = m.hp > 0 and (m.hp < m.max_hp or (item == "FULL_RESTORE" and m.status != ""))
		elif STATUS_ITEMS.has(item):
			ok = m.hp > 0 and STATUS_ITEMS[item].has(m.status)
		elif item in ["REVIVE", "MAX_REVIVE"]:
			ok = m.hp <= 0
		elif item == "RARE_CANDY":
			ok = m.level < 100 and mode == "field"
		elif item.ends_with("_STONE"):
			ok = Mon.item_evolution(m, item) != "" and mode == "field"
		else:
			ok = mode == "field"
		if not ok:
			await UI.say("효과가 없을 것 같다.")
			return {}
		if mode == "battle":
			return {"done": true, "item": item, "target": t}
		G.remove_item(item)
		await _apply_field_item(item, m)
		return {}
	if DB.items.has(item) and DB.items[item].has("move"):
		if mode != "field":
			await UI.say("지금은 쓸 수 없다!")
			return {}
		await Field.use_tm(item)
		return {}
	if item in ["ETHER", "MAX_ETHER", "ELIXER", "MAX_ELIXER", "PP_UP"]:
		var t2: int = await party_menu("select", -1)
		if t2 < 0:
			return {}
		var m2: Dictionary = G.party[t2]
		var slot := -1
		if item in ["ETHER", "MAX_ETHER", "PP_UP"]:
			var names := []
			for x in m2.moves:
				names.append("%s %d/%d" % [DB.move_name(x.id), x.pp, x.max])
			slot = await UI.choose(names, Rect2(24, 40, 136, names.size() * 14 + 10))
			if slot < 0:
				return {}
		var ok2 := false
		for i in m2.moves.size():
			if slot >= 0 and i != slot:
				continue
			var x: Dictionary = m2.moves[i]
			if item == "PP_UP":
				var base_pp: int = DB.moves[x.id].pp
				if x.max < base_pp * 8 / 5 and not x.id in ["SKETCH"]:
					x.max = mini(base_pp * 8 / 5, x.max + base_pp / 5)
					x.pp = mini(x.max, x.pp + base_pp / 5)
					ok2 = true
			elif x.pp < x.max:
				x.pp = x.max if item.begins_with("MAX") else mini(x.max, x.pp + 10)
				ok2 = true
		if not ok2:
			await UI.say("효과가 없을 것 같다.")
			return {}
		if mode == "battle":
			G.remove_item(item)
			Sound.sfx("Heal_HP")
			await UI.say("PP가 회복되었다!")
			return {"done": true, "item": "_USED_PP"}
		G.remove_item(item)
		Sound.sfx("Heal_HP")
		await UI.say("PP가 올라갔다!" if item == "PP_UP" else "PP가 회복되었다!")
		return {}
	if mode == "field" and item in ["BICYCLE", "OLD_ROD", "GOOD_ROD", "SUPER_ROD", "ESCAPE_ROPE", "ITEMFINDER", "POKE_FLUTE", "COIN_CASE", "TOWN_MAP"]:
		UI.close_box()
		if await Field.use_key_item(Main.inst.ow, item):
			return {"close": true}
		return {}
	match item:
		"POKE_DOLL":
			if mode == "battle":
				return {"done": true, "item": item}
			await UI.say("귀여운 포켓몬 인형이다.")
		"POKE_FLUTE":
			if mode == "battle":
				return {"done": true, "item": item}
		"REPEL", "SUPER_REPEL", "MAX_REPEL":
			if mode != "field":
				await UI.say("지금은 쓸 수 없다!")
				return {}
			G.remove_item(item)
			G.flags["repel"] = {"REPEL": 100, "SUPER_REPEL": 200, "MAX_REPEL": 250}[item]
			await UI.say("{PLAYER}{은} %s{을} 뿌렸다!" % DB.item_name(item))
		"TOWN_MAP":
			await UI.say("관동 지방의 지도다!\n지금 %s에 있다." % DB.maps[G.last_outdoor].name)
		"X_ATTACK", "X_DEFEND", "X_SPEED", "X_SPECIAL", "X_ACCURACY", "DIRE_HIT", "GUARD_SPEC":
			if mode == "battle":
				return {"done": true, "item": item}
			await UI.say("지금은 쓸 수 없다!")
		_:
			await UI.say("오박사의 말이 떠올랐다...\n지금은 쓸 때가 아니다!")
	return {}


static func _apply_field_item(item: String, m: Dictionary) -> void:
	var nm := Mon.name_of(m)
	Sound.sfx("Heal_HP")
	if HEAL_ITEMS.has(item):
		var before: int = m.hp
		m.hp = mini(m.max_hp, m.hp + HEAL_ITEMS[item])
		if item == "FULL_RESTORE":
			m.status = ""
		await UI.say("%s의 체력이 %d 회복되었다!" % [nm, m.hp - before])
	elif STATUS_ITEMS.has(item):
		m.status = ""
		m.sleep = 0
		await UI.say("%s의 상태가 회복되었다!" % nm)
	elif item in ["REVIVE", "MAX_REVIVE"]:
		m.hp = m.max_hp if item == "MAX_REVIVE" else m.max_hp / 2
		await UI.say("%s의 기력이 돌아왔다!" % nm)
	elif item == "RARE_CANDY":
		var ups := Mon.add_exp(m, maxi(1, DB.exp_for_level(DB.pokemon[m.species].growth, m.level + 1) - m.exp))
		for up in ups:
			await UI.say("%s의 레벨이 %d{으로} 올랐다!" % [nm, up.level], true)
			for mv in up.learn:
				await Battle.learn_move_flow(m, mv)
		UI.close_box()
		var to := Mon.level_evolution(m)
		if to != "":
			await Battle.evolve_scene(UI, m, to)
	elif item.ends_with("_STONE"):
		await Battle.evolve_scene(UI, m, Mon.item_evolution(m, item))
	else:
		var st: String = {"HP_UP": "hp", "PROTEIN": "atk", "IRON": "def", "CARBOS": "spd", "CALCIUM": "spc"}[item]
		m.sexp[st] = mini(65535, m.sexp[st] + 2560)
		Mon.recalc(m)
		await UI.say("%s의 능력이 올라갔다!" % nm)


# ------------------------------------------------------------------ 기타 화면
static func trainer_card() -> void:
	var scr := _screen()
	var box := GBBox.new(Rect2(0, 0, 160, 144))
	scr.add_child(box)
	var t := int(G.play_time)
	box.add_child(GBBox.label("이름: %s\n소지금: %d원\n플레이 시간: %d:%02d\n\n도감: 발견 %d / 포획 %d\n배지: %d개" % [
		G.player_name, G.money, t / 3600, (t / 60) % 60, G.seen.size(), G.caught.size(),
		G.badge_count()], Vector2(10, 10)))
	var bnames := ["회색", "블루", "오렌지", "무지개", "핑크", "골드", "진홍", "그린"]
	for i in 8:
		var got: bool = G.bag.has(G.BADGES[i])
		var bl := GBBox.label(bnames[i] if got else "----", Vector2(10 + (i % 4) * 36, 104 + (i / 4) * 14), 8)
		box.add_child(bl)
	var pic := TextureRect.new()
	pic.texture = DB.tex("res://assets/misc/red_front.png")
	pic.position = Vector2(100, 80)
	box.add_child(pic)
	UI.busy += 1
	await UI.frame()
	while not (UI.pressed("a") or UI.pressed("b")):
		await UI.frame()
	UI.busy -= 1
	scr.queue_free()


static func pokedex() -> void:
	var scr := _screen()
	var lbl := GBBox.label("", Vector2(12, 2))
	scr.add_child(lbl)
	var cnt := GBBox.label("발견 %d\n포획 %d" % [G.seen.size(), G.caught.size()], Vector2(116, 2), 8)
	scr.add_child(cnt)
	var pic := TextureRect.new()
	pic.position = Vector2(104, 80)
	scr.add_child(pic)
	var cursor := GBBox.label("▶", Vector2(2, 0), 8)
	scr.add_child(cursor)
	var top := 0
	var idx := 0
	var per := 10
	UI.busy += 1
	await UI.frame()
	while true:
		var lines := []
		for i in range(top, mini(top + per, 151)):
			var sp: String = DB.dex_order[i]
			var mark := "●" if G.caught.has(sp) else " "
			lines.append("%03d%s%s" % [i + 1, mark, DB.mon_name(sp) if G.seen.has(sp) else "-----"])
		lbl.text = "\n".join(lines)
		lbl.add_theme_constant_override("line_spacing", 1)
		cursor.position = Vector2(2, 3 + (idx - top) * 14)
		var cur_sp: String = DB.dex_order[idx]
		pic.texture = Mon.front_tex(cur_sp) if G.seen.has(cur_sp) else null
		await UI.frame()
		if UI.pressed("down") and idx < 150:
			idx += 1
		elif UI.pressed("up") and idx > 0:
			idx -= 1
		elif UI.pressed("right"):
			idx = mini(150, idx + per)
		elif UI.pressed("left"):
			idx = maxi(0, idx - per)
		elif UI.pressed("b"):
			break
		if idx < top:
			top = idx
		elif idx >= top + per:
			top = idx - per + 1
	UI.busy -= 1
	scr.queue_free()


static func pokecenter(ow: Overworld) -> void:
	await UI.say("어서 오세요!\n포켓몬센터입니다.\f여기서는 포켓몬의 체력을 회복시켜 드립니다.\f포켓몬을 쉬게 할까요?", true, false)
	if not await UI.yes_no():
		await UI.say("또 오세요!")
		return
	await UI.say("그럼 포켓몬을 맡아 두겠습니다.", true, false)
	await UI.wait(0.4)
	Sound.sfx("Healing_Machine")
	await UI.fade_out(0.3, Color.WHITE)
	G.heal_party()
	await UI.wait(0.6)
	await UI.fade_in(0.3)
	await Sound.jingle("PkmnHealed")
	G.heal_map = ow.map_id
	G.heal_pos = ow.player.cell
	G.flags["heal_outdoor"] = G.last_outdoor
	await UI.say("오래 기다리셨습니다!\f맡기신 포켓몬은 모두 건강해졌습니다!\f또 오세요!")


static func mart(stock: Array) -> void:
	await UI.say("어서 오세요!\n무엇을 도와드릴까요?", true, false)
	while true:
		var money_box := GBBox.new(Rect2(88, 0, 72, 22))
		money_box.add_child(GBBox.label("%d원" % G.money, Vector2(8, 4)))
		UI.root().add_child(money_box)
		var c: int = await UI.choose(["사다", "팔다", "그만두다"], Rect2(0, 0, 72, 52))
		if c == 0:
			while true:
				var opts := []
				for it in stock:
					opts.append("%s %d원" % [DB.item_name(it), DB.items[it].price])
				UI.say("무엇을 사시겠어요?", true, false)
				var k: int = await UI.choose(opts, Rect2(8, 24, 152, mini(opts.size() * 14 + 10, 72)))
				if k < 0:
					break
				var it: String = stock[k]
				var price: int = DB.items[it].price
				var max_n := mini(99, G.money / maxi(1, price))
				if max_n <= 0:
					await UI.say("돈이 부족합니다.", true, false)
					continue
				var n: int = await UI.number(max_n, Rect2(80, 80, 80, 22), price)
				if n <= 0:
					continue
				await UI.say("%s %d개에\n%d원입니다. 괜찮으세요?" % [DB.item_name(it), n, n * price], true, false)
				if await UI.yes_no():
					G.add_money(-n * price)
					G.add_item(it, n)
					Sound.sfx("Purchase")
					money_box.get_child(0).text = "%d원" % G.money
					await UI.say("여기 있습니다!\n감사합니다!", true, false)
		elif c == 1:
			while true:
				var keys := G.bag.keys().filter(func(k): return not k in KEY_ITEMS and DB.items.has(k) and DB.items[k].price > 0)
				if keys.is_empty():
					await UI.say("팔 수 있는 물건이 없습니다.", true, false)
					break
				var opts2 := []
				for k in keys:
					opts2.append("%s ×%d" % [DB.item_name(k), G.bag[k]])
				UI.say("무엇을 파시겠어요?", true, false)
				var k2: int = await UI.choose(opts2, Rect2(8, 24, 152, mini(opts2.size() * 14 + 10, 72)))
				if k2 < 0:
					break
				var it2: String = keys[k2]
				var sp: int = DB.items[it2].price / 2
				var n2: int = await UI.number(G.bag[it2], Rect2(80, 80, 80, 22), sp)
				if n2 <= 0:
					continue
				await UI.say("%d원에 사 드릴게요.\n괜찮으세요?" % (n2 * sp), true, false)
				if await UI.yes_no():
					G.remove_item(it2, n2)
					G.add_money(n2 * sp)
					money_box.get_child(0).text = "%d원" % G.money
		money_box.queue_free()
		if c < 0 or c == 2:
			break
		UI.say("다른 볼일은 있으세요?", true, false)
	await UI.say("또 오세요!")


static func pc() -> void:
	await UI.say("{PLAYER}{은} PC의 전원을 켰다!", true)
	var cur := 0
	while true:
		UI.say("무엇을 할까?", true, false)
		var c: int = await UI.choose(["포켓몬 맡기기", "포켓몬 꺼내기", "도구 정리", "끄기"], Rect2(0, 0, 100, 66), cur)
		cur = maxi(c, 0)
		match c:
			0:
				if G.party.size() <= 1:
					await UI.say("파티에 포켓몬이 1마리뿐이라 맡길 수 없다!포켓몬을 더 잡은 다음에 맡기자.", true)
					cur = 3
					continue
				var i: int = await party_menu("select", -1)
				if i >= 0:
					var m: Dictionary = G.party[i]
					G.party.remove_at(i)
					G.box.append(m)
					await UI.say("%s{을} 박스에 맡겼다." % Mon.name_of(m), true)
			1:
				if G.box.is_empty():
					await UI.say("박스에 포켓몬이 없다!", true)
					continue
				if G.party.size() >= 6:
					await UI.say("파티가 가득 찼다!", true)
					continue
				var opts := []
				for m in G.box:
					opts.append("%s Lv%d" % [Mon.name_of(m), m.level])
				var k: int = await UI.choose(opts, Rect2(24, 0, 136, mini(opts.size() * 14 + 10, 96)))
				if k >= 0:
					var m2: Dictionary = G.box[k]
					G.box.remove_at(k)
					G.party.append(m2)
					await UI.say("%s{을} 꺼냈다." % Mon.name_of(m2), true)
			2:
				await bag_menu("field")
			_:
				break
	UI.close_box()
