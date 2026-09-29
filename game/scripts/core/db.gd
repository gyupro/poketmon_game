extends Node
## 변환된 원작 데이터(JSON) 로더. tools/convert.py 가 생성한 파일을 읽는다.

var maps: Dictionary
var tilesets: Dictionary
var texts_en: Dictionary
var ko: Dictionary
var palettes: Dictionary
var pokemon: Dictionary
var moves: Dictionary
var types: Dictionary
var items: Dictionary
var marts: Dictionary
var trainers: Dictionary
var wild: Dictionary
var growth: Dictionary
var toggles: Dictionary
var extra: Dictionary

var _type_chart := {}
var _tex_cache := {}
var dex_order: Array = []  # 도감번호 순 species 키


func _ready() -> void:
	maps = _load("maps")
	tilesets = _load("tilesets")
	texts_en = _load("texts_en")
	ko = _load("ko")
	palettes = _load("palettes")
	pokemon = _load("pokemon")
	moves = _load("moves")
	types = _load("types")
	items = _load("items")
	marts = _load("marts")
	trainers = _load("trainers")
	wild = _load("wild")
	growth = _load("growth")
	toggles = _load("toggles")
	extra = _load("extra")
	for row in types.chart:
		_type_chart[row[0] + ">" + row[1]] = row[2]
	dex_order = pokemon.keys()
	dex_order.sort_custom(func(a, b): return pokemon[a].dex < pokemon[b].dex)


func _load(name: String) -> Dictionary:
	var f := FileAccess.open("res://data/%s.json" % name, FileAccess.READ)
	if f == null:
		push_error("데이터 없음: " + name)
		return {}
	return _ints(JSON.parse_string(f.get_as_text()))


## JSON 숫자(float) 중 정수값을 int 로 변환 (Array.has 등 타입 비교 문제 방지)
func _ints(v):
	if v is Dictionary:
		for k in v:
			v[k] = _ints(v[k])
		return v
	if v is Array:
		for i in v.size():
			v[i] = _ints(v[i])
		return v
	if v is float and v == floorf(v):
		return int(v)
	return v


func tex(path: String) -> Texture2D:
	if not _tex_cache.has(path):
		_tex_cache[path] = load(path) if ResourceLoader.exists(path) else null
	return _tex_cache[path]


func type_mult(atk_type: String, def_type: String) -> float:
	return _type_chart.get(atk_type + ">" + def_type, 1.0)


func type_name(t: String) -> String:
	return types.names.get(t, t)


func mon_name(species: String) -> String:
	return pokemon[species].name if pokemon.has(species) else species


func move_name(m: String) -> String:
	return moves[m].name if moves.has(m) else m


func item_name(i: String) -> String:
	return items[i].name if items.has(i) else i


## 레벨 n 에 필요한 누적 경험치 (원작 성장 곡선 공식)
func exp_for_level(growth_rate: String, n: int) -> int:
	if n <= 1:
		return 0
	var g: Array = growth[growth_rate]
	var v: float = float(g[0]) / g[1] * pow(n, 3) + g[2] * n * n + g[3] * n - g[4]
	return max(0, int(v))


## 텍스트 조회: 한국어 우선, 없으면 원문(영어)
func text(key: String) -> String:
	if ko.has(key):
		return ko[key]
	if texts_en.has(key):
		return texts_en[key]
	return ""


func map_text(map_const: String, text_id: String) -> String:
	if ko.has(text_id):
		return ko[text_id]
	var info: Dictionary = maps[map_const].texts.get(text_id, {})
	if info.has("text"):
		return text(info.text)
	return ""


func palette(pal_name) -> Array:
	if pal_name == null or not palettes.has(pal_name):
		return palettes["PAL_ROUTE"]
	return palettes[pal_name]
