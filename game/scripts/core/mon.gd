class_name Mon
## 포켓몬 개체(Dictionary) 생성/계산 헬퍼. 네트워크·세이브를 위해 순수 Dictionary 로 다룬다.

const STATS := ["hp", "atk", "def", "spd", "spc"]


static func create(species: String, level: int, ot := "") -> Dictionary:
	var d := {
		"atk": randi() % 16, "def": randi() % 16, "spd": randi() % 16, "spc": randi() % 16,
	}
	d["hp"] = ((d.atk & 1) << 3) | ((d.def & 1) << 2) | ((d.spd & 1) << 1) | (d.spc & 1)
	var m := {
		"species": species, "nick": "", "level": level, "ot": ot,
		"exp": DB.exp_for_level(DB.pokemon[species].growth, level),
		"dvs": d, "sexp": {"hp": 0, "atk": 0, "def": 0, "spd": 0, "spc": 0},
		"status": "", "sleep": 0, "moves": [],
	}
	recalc(m)
	m["hp"] = m.max_hp
	# 레벨업 기술: 시작 기술 + 해당 레벨까지 배우는 기술 중 최근 4개
	var ms: Array = DB.pokemon[species].moves.duplicate()
	for pair in DB.pokemon[species].learn:
		if pair[0] <= level and not ms.has(pair[1]):
			ms.append(pair[1])
	while ms.size() > 4:
		ms.pop_front()
	for mv in ms:
		m.moves.append({"id": mv, "pp": DB.moves[mv].pp, "max": DB.moves[mv].pp})
	return m


static func calc_stat(base: int, dv: int, sexp: int, level: int, is_hp: bool) -> int:
	var e := int(ceil(sqrt(float(sexp)))) / 4
	var v := ((base + dv) * 2 + e) * level / 100
	return v + (level + 10 if is_hp else 5)


static func recalc(m: Dictionary) -> void:
	var b: Dictionary = DB.pokemon[m.species]
	var old_max: int = m.get("max_hp", 0)
	m["max_hp"] = calc_stat(b.hp, m.dvs.hp, m.sexp.hp, m.level, true)
	for s in ["atk", "def", "spd", "spc"]:
		m[s + "_stat"] = calc_stat(b[s], m.dvs[s], m.sexp[s], m.level, false)
	if m.has("hp") and old_max > 0:
		m.hp = clampi(m.hp + (m.max_hp - old_max), 0, m.max_hp)


static func name_of(m: Dictionary) -> String:
	return m.nick if m.get("nick", "") != "" else DB.mon_name(m.species)


static func types_of(m: Dictionary) -> Array:
	return DB.pokemon[m.species].types


static func heal(m: Dictionary) -> void:
	m.hp = m.max_hp
	m.status = ""
	m.sleep = 0
	for mv in m.moves:
		mv.pp = mv.max


static func exp_to_next(m: Dictionary) -> int:
	if m.level >= 100:
		return 0
	return DB.exp_for_level(DB.pokemon[m.species].growth, m.level + 1) - m.exp


## 경험치 추가. 레벨업 이벤트 목록 반환: [{level, learn:[move...]}]
static func add_exp(m: Dictionary, amount: int) -> Array:
	var events := []
	m.exp += amount
	var g: String = DB.pokemon[m.species].growth
	while m.level < 100 and m.exp >= DB.exp_for_level(g, m.level + 1):
		m.level += 1
		recalc(m)
		var learned := []
		for pair in DB.pokemon[m.species].learn:
			if pair[0] == m.level:
				learned.append(pair[1])
		events.append({"level": m.level, "learn": learned})
	return events


static func has_move(m: Dictionary, move_id: String) -> bool:
	for mv in m.moves:
		if mv.id == move_id:
			return true
	return false


static func learn_move(m: Dictionary, move_id: String, replace_index := -1) -> void:
	var entry := {"id": move_id, "pp": DB.moves[move_id].pp, "max": DB.moves[move_id].pp}
	if replace_index >= 0:
		m.moves[replace_index] = entry
	elif m.moves.size() < 4:
		m.moves.append(entry)


static func level_evolution(m: Dictionary) -> String:
	for e in DB.pokemon[m.species].evos:
		if e.method == "level" and m.level >= e.level:
			return e.to
	return ""


static func item_evolution(m: Dictionary, item: String) -> String:
	for e in DB.pokemon[m.species].evos:
		if e.method == "item" and e.item == item:
			return e.to
	return ""


static func trade_evolution(m: Dictionary) -> String:
	for e in DB.pokemon[m.species].evos:
		if e.method == "trade":
			return e.to
	return ""


static func evolve(m: Dictionary, to: String) -> void:
	m.species = to
	recalc(m)


static func front_tex(species: String) -> Texture2D:
	return DB.tex("res://assets/pokemon/front/%s.png" % species.to_lower())


static func back_tex(species: String) -> Texture2D:
	return DB.tex("res://assets/pokemon/back/%s.png" % species.to_lower())
