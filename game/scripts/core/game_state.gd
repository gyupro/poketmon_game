extends Node
## 플레이어 진행 상태 + 세이브/로드 + 입력 설정.

signal money_changed

const RIVAL_NAME := "그린"
const BADGES := ["BOULDERBADGE", "CASCADEBADGE", "THUNDERBADGE", "RAINBOWBADGE", "SOULBADGE", "MARSHBADGE", "VOLCANOBADGE", "EARTHBADGE"]
const SPRITES := ["red", "blue", "youngster", "girl", "cooltrainer_m", "cooltrainer_f", "hiker", "fisher"]

var player_name := "레드"
var sprite := "red"
var money := 3000
var party: Array = []
var box: Array = []
var bag := {}  # item -> count
var flags := {}  # 이벤트 플래그/오브젝트 토글 등
var seen := {}
var caught := {}
var map := "REDS_HOUSE_2F"
var pos := Vector2i(3, 6)
var facing := Vector2i.DOWN
var last_outdoor := "PALLET_TOWN"
var heal_map := "PALLET_TOWN"  # 전멸 시 돌아갈 곳 (마지막 포켓몬센터 도시)
var heal_pos := Vector2i(5, 6)
var play_time := 0.0
var loaded := false


func _ready() -> void:
	_setup_input()


func _notification(what: int) -> void:
	# 창을 닫으면 자동 저장 (필드에 있을 때만)
	if what == NOTIFICATION_WM_CLOSE_REQUEST and loaded and autosave:
		if Main.inst and is_instance_valid(Main.inst.ow) and Main.inst.ow.visible:
			save_game()


var autosave := true


func _process(delta: float) -> void:
	if loaded:
		play_time += delta


func _setup_input() -> void:
	var binds := {
		"up": [KEY_UP, KEY_W], "down": [KEY_DOWN, KEY_S],
		"left": [KEY_LEFT, KEY_A], "right": [KEY_RIGHT, KEY_D],
		"a": [KEY_Z, KEY_SPACE, KEY_J], "b": [KEY_X, KEY_BACKSPACE, KEY_K, KEY_ESCAPE],
		"start": [KEY_ENTER, KEY_KP_ENTER], "select": [KEY_SHIFT],
	}
	for action in binds:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for k in binds[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)


func new_game(pname: String, spr: String) -> void:
	player_name = pname
	sprite = spr
	money = 3000
	party = []
	box = []
	bag = {"POTION": 1}
	flags = {}
	seen = {}
	caught = {}
	map = "REDS_HOUSE_2F"
	pos = Vector2i(3, 6)
	facing = Vector2i.UP
	last_outdoor = "PALLET_TOWN"
	heal_map = "PALLET_TOWN"
	heal_pos = Vector2i(5, 6)
	play_time = 0.0
	loaded = true


## 필드에서 보이는 스프라이트 (파도타기/자전거 반영)
func field_sprite() -> String:
	if flag("surfing"):
		return "seel"
	if flag("biking"):
		return "red_bike" if sprite == "red" else sprite
	return sprite


func badge_count() -> int:
	var n := 0
	for b in BADGES:
		if bag.has(b):
			n += 1
	return n


func flag(name: String) -> bool:
	return flags.get(name, false)


func set_flag(name: String, v := true) -> void:
	flags[name] = v


## 오브젝트 표시 여부 (원작 toggleable object 초기값 + 스토리 플래그로 덮어씀)
func object_visible(obj_id: String) -> bool:
	var key := "show:" + obj_id
	if flags.has(key):
		return flags[key]
	return DB.toggles.get(obj_id, true)


func set_object_visible(obj_id: String, v: bool) -> void:
	flags["show:" + obj_id] = v


func add_item(item: String, n := 1) -> void:
	bag[item] = bag.get(item, 0) + n


func remove_item(item: String, n := 1) -> bool:
	if bag.get(item, 0) < n:
		return false
	bag[item] -= n
	if bag[item] <= 0:
		bag.erase(item)
	return true


func add_money(n: int) -> void:
	money = clampi(money + n, 0, 999999)
	money_changed.emit()


func register_seen(species: String) -> void:
	seen[species] = true


func register_caught(species: String) -> void:
	seen[species] = true
	caught[species] = true


## 포켓몬 추가: 파티가 가득 차면 박스로. 반환: "party" | "box"
func give_mon(m: Dictionary) -> String:
	register_caught(m.species)
	if party.size() < 6:
		party.append(m)
		return "party"
	box.append(m)
	return "box"


func first_alive() -> int:
	for i in party.size():
		if party[i].hp > 0:
			return i
	return -1


func heal_party() -> void:
	for m in party:
		Mon.heal(m)


# ------------------------------------------------------------------ save
func save_path() -> String:
	return "user://save_%s.json" % player_name.md5_text().substr(0, 10)


func to_dict() -> Dictionary:
	return {
		"player_name": player_name, "sprite": sprite, "money": money, "party": party, "box": box,
		"bag": bag, "flags": flags, "seen": seen, "caught": caught, "map": map,
		"pos": [pos.x, pos.y], "facing": [facing.x, facing.y], "last_outdoor": last_outdoor,
		"heal_map": heal_map, "heal_pos": [heal_pos.x, heal_pos.y], "play_time": play_time,
	}


func save_game() -> bool:
	var f := FileAccess.open(save_path(), FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(to_dict()))
	var idx := FileAccess.open("user://last_save.txt", FileAccess.WRITE)
	idx.store_string(save_path())
	return true


func list_saves() -> Array:
	var out := []
	var dir := DirAccess.open("user://")
	if dir == null:
		return out
	for f in dir.get_files():
		if f.begins_with("save_") and f.ends_with(".json"):
			var d = _read_json("user://" + f)
			if d is Dictionary:
				d["_path"] = "user://" + f
				out.append(d)
	return out


func _read_json(path: String):
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	return JSON.parse_string(f.get_as_text())


func load_from(d: Dictionary) -> void:
	player_name = d.player_name
	sprite = d.get("sprite", "red")
	money = int(d.money)
	party = _fix_ints(d.party)
	box = _fix_ints(d.box)
	bag = {}
	for k in d.bag:
		bag[k] = int(d.bag[k])
	flags = d.flags
	seen = d.seen
	caught = d.caught
	map = d.map
	pos = Vector2i(int(d.pos[0]), int(d.pos[1]))
	facing = Vector2i(int(d.facing[0]), int(d.facing[1]))
	last_outdoor = d.last_outdoor
	heal_map = d.heal_map
	heal_pos = Vector2i(int(d.heal_pos[0]), int(d.heal_pos[1]))
	play_time = float(d.get("play_time", 0))
	loaded = true


## JSON 은 숫자를 float 로 읽으므로 정수로 되돌린다.
func _fix_ints(v):
	if v is Dictionary:
		var o := {}
		for k in v:
			o[k] = _fix_ints(v[k])
		return o
	if v is Array:
		var a := []
		for x in v:
			a.append(_fix_ints(x))
		return a
	if v is float and v == floor(v):
		return int(v)
	return v


func fix_ints(v):
	return _fix_ints(v)
