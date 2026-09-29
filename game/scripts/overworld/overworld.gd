class_name Overworld
extends Node2D
## 필드 화면: 맵 표시, 이동/충돌, 워프, 맵 연결, 야생 조우, 트레이너 시선, 상호작용, 다른 플레이어 표시.
## 필드 기술(파도타기/자전거/괴력/풀베기/플래시)과 블록 교체(문 열림 등)도 여기서 처리한다.

const LEDGES := [
	[Vector2i.DOWN, 0x2C, 0x37], [Vector2i.DOWN, 0x39, 0x36], [Vector2i.DOWN, 0x39, 0x37],
	[Vector2i.LEFT, 0x2C, 0x27], [Vector2i.LEFT, 0x39, 0x27],
	[Vector2i.RIGHT, 0x2C, 0x0D], [Vector2i.RIGHT, 0x2C, 0x1D], [Vector2i.RIGHT, 0x39, 0x0D],
]
const SLOT_THRESH := [51, 102, 141, 166, 191, 216, 229, 242, 253, 256]
const DARK_MAPS := ["ROCK_TUNNEL_1F", "ROCK_TUNNEL_B1F"]

var map_id := ""
var map: Dictionary
var ts: Dictionary
var world: Node2D
var overlay: Node2D
var player: Actor
var npcs: Array = []
var remotes := {}
var cam: Camera2D
var locked := false
var walking := false
var _turn_delay := 0.0
var _pending_requests: Array = []
var _npc_timer := {}
var _bump_cd := 0.0
var _dark: Sprite2D
var temp_blocks := {}  # 맵을 떠나면 사라지는 블록 교체 (풀베기)
var _temp_map := ""
var _block_tex_cache := {}


func _ready() -> void:
	world = Node2D.new()
	var mat := ShaderMaterial.new()
	mat.shader = load("res://assets/gb_palette.gdshader")
	world.material = mat
	add_child(world)
	build(G.map, G.pos, G.facing)
	Net.peer_state.connect(_on_peer_state)
	Net.peers_changed.connect(_sync_remotes)
	Net.request_received.connect(func(id, kind): _pending_requests.append([id, kind]))
	Net.chat_received.connect(func(id, text): UI.toast("%s: %s" % [Net.peers.get(id, {}).get("name", "?"), text], 3.0))
	Net.send_state(false)
	run_event(func(): await Events.on_enter(self))


# ------------------------------------------------------------------ 맵 구성
func build(id: String, at: Vector2i, dir: Vector2i) -> void:
	for c in world.get_children():
		c.queue_free()
	npcs.clear()
	remotes.clear()
	_npc_timer.clear()
	if id != _temp_map:
		temp_blocks.clear()
		_temp_map = id
		G.flags.erase("strength_on")
	Field.mark_visited(id)
	map_id = id
	var src: Dictionary = DB.maps[id]
	map = src.duplicate()
	map.cells = src.cells.duplicate(true)
	map.blk = src.blk.duplicate()
	map.warps = src.warps.duplicate(true)
	ts = DB.tilesets[map.tileset]
	if G.flag("surfing") and not is_water(at):
		G.flags.erase("surfing")
	if G.flag("biking") and not DB.extra.bike_tilesets.has(map.tileset):
		G.flags.erase("biking")
	G.map = id
	G.pos = at
	if map.outdoor:
		G.last_outdoor = id
	if not DARK_MAPS.has(id):
		G.flags.erase("flash")
	_apply_palette()

	var w: int = map.w * 32
	var h: int = map.h * 32
	var border := TextureRect.new()
	border.texture = DB.tex("res://assets/maps/%s_border.png" % map.name)
	border.stretch_mode = TextureRect.STRETCH_TILE
	border.position = Vector2(-192, -192)
	border.size = Vector2(w + 384, h + 384)
	border.use_parent_material = true
	border.mouse_filter = Control.MOUSE_FILTER_IGNORE
	world.add_child(border)
	for c in map.connections:
		if not DB.maps.has(c.map):
			continue
		var nm: Dictionary = DB.maps[c.map]
		var s := _map_sprite(nm.name)
		match c.dir:
			"north": s.position = Vector2(c.offset * 32, -nm.h * 32)
			"south": s.position = Vector2(c.offset * 32, h)
			"west": s.position = Vector2(-nm.w * 32, c.offset * 32)
			"east": s.position = Vector2(w, c.offset * 32)
		world.add_child(s)
	world.add_child(_map_sprite(map.name))
	overlay = Node2D.new()
	overlay.use_parent_material = true
	world.add_child(overlay)
	# 저장된 블록 교체(문 열림 등) + 이번 방문 중 교체(풀베기)
	var saved: Dictionary = G.flags.get("blk:" + id, {})
	for k in saved:
		_apply_block(int(k), int(saved[k]))
	for k in temp_blocks:
		_apply_block(int(k), int(temp_blocks[k]))
	Events.on_build(self)

	for n in map.npcs:
		if not _npc_should_show(n):
			continue
		var a := Actor.new()
		world.add_child(a)
		var at_n := Vector2i(n.x, n.y)
		var moved = G.flags.get("pos:" + n.id)
		if moved != null:
			at_n = Vector2i(int(moved[0]), int(moved[1]))
		a.setup(n.sprite_file, at_n, Actor.dir_from_name(n.dir))
		a.data = n
		npcs.append(a)
		_npc_timer[a] = randf_range(0.5, 2.5)
		Events.on_npc_spawn(self, a)

	player = Actor.new()
	world.add_child(player)
	player.setup(player_sprite(), at, dir)
	player.z_index = 1
	cam = Camera2D.new()
	cam.position = Vector2(16, 8)
	player.add_child(cam)
	cam.make_current()
	_update_dark()
	_sync_remotes()
	Sound.map_music(id)


func player_sprite() -> String:
	return G.field_sprite()


func refresh_player_sprite() -> void:
	var t: Texture2D = DB.tex("res://assets/sprites/%s.png" % player_sprite())
	if t:
		player.sprite.texture = t
		player.single_frame = t.get_height() <= 16
		player.set_facing(player.facing)
	Net.send_state(false)


func _map_sprite(name: String) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = DB.tex("res://assets/maps/%s.png" % name)
	s.centered = false
	s.use_parent_material = true
	return s


func _apply_palette() -> void:
	var pal_name = map.palette
	if pal_name == null:
		pal_name = DB.maps.get(G.last_outdoor, {}).get("palette", "PAL_ROUTE")
	var p: Array = DB.palette(pal_name)
	var mat: ShaderMaterial = world.material
	for i in 4:
		mat.set_shader_parameter("c%d" % i, Color8(p[i][0], p[i][1], p[i][2]))


func _npc_should_show(n: Dictionary) -> bool:
	if n.has("item") and G.flag("got:" + n.id):
		return false
	if n.has("pokemon") and G.flag("beat:" + n.id):
		return false
	return G.object_visible(n.id)


## 어두운 동굴(플래시 전): 플레이어 주변만 보이게
func _update_dark() -> void:
	if _dark:
		_dark.queue_free()
		_dark = null
	if not DARK_MAPS.has(map_id) or G.flag("flash"):
		return
	var img := Image.create(480, 432, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 1))
	var c := Vector2(240, 216)
	for y in 432:
		for x in 480:
			var d := Vector2(x, y).distance_to(c)
			if d < 22:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
			elif d < 30:
				img.set_pixel(x, y, Color(0, 0, 0, (d - 22) / 8.0))
	_dark = Sprite2D.new()
	_dark.texture = ImageTexture.create_from_image(img)
	_dark.position = Vector2(8, 8)
	_dark.z_index = 20
	player.add_child(_dark)


# ------------------------------------------------------------------ 블록 교체
func block_index(c: Vector2i) -> int:
	return (c.y / 2) * map.w + (c.x / 2)


func block_at(c: Vector2i) -> int:
	return map.blk[block_index(c)]


## 블록 교체. persistent=true 면 세이브에 남음(문 열림), false 면 맵을 떠날 때까지(풀베기)
func set_block(bidx: int, block: int, persistent := true) -> void:
	if persistent:
		var d: Dictionary = G.flags.get("blk:" + map_id, {})
		d[str(bidx)] = block
		G.flags["blk:" + map_id] = d
	else:
		temp_blocks[str(bidx)] = block
	_apply_block(bidx, block)


func set_block_xy(bx: int, by: int, block: int, persistent := true) -> void:
	set_block(by * map.w + bx, block, persistent)


func _apply_block(bidx: int, block: int) -> void:
	if bidx < 0 or bidx >= map.blk.size():
		return
	map.blk[bidx] = block
	var bx := bidx % int(map.w)
	var by := bidx / int(map.w)
	var tiles: Array = ts.blocks[block]
	for sy in 2:
		for sx in 2:
			map.cells[by * 2 + sy][bx * 2 + sx] = tiles[(sy * 2 + 1) * 4 + sx * 2]
	var s := Sprite2D.new()
	s.texture = _block_tex(map.tileset, block)
	s.centered = false
	s.position = Vector2(bx * 32, by * 32)
	s.use_parent_material = true
	s.name = "blk%d" % bidx
	var old := overlay.get_node_or_null(NodePath(s.name))
	if old:
		old.name = "old"
		old.queue_free()
	overlay.add_child(s)


func _block_tex(tileset: String, block: int) -> Texture2D:
	var key := "%s:%d" % [tileset, block]
	if _block_tex_cache.has(key):
		return _block_tex_cache[key]
	var src_tex: Texture2D = DB.tex("res://assets/tilesets/%s.png" % tileset)
	var src := src_tex.get_image()
	if src.is_compressed():
		src.decompress()
	src.convert(Image.FORMAT_RGBA8)
	var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
	var tiles: Array = DB.tilesets[tileset].blocks[block]
	var per_row := src.get_width() / 8
	for ty in 4:
		for tx in 4:
			var t: int = tiles[ty * 4 + tx]
			img.blit_rect(src, Rect2i((t % per_row) * 8, (t / per_row) * 8, 8, 8), Vector2i(tx * 8, ty * 8))
	var tex := ImageTexture.create_from_image(img)
	_block_tex_cache[key] = tex
	return tex


# ------------------------------------------------------------------ 조회
func in_bounds(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < map.w * 2 and c.y < map.h * 2


func tile_at(c: Vector2i, m := map) -> int:
	if c.x < 0 or c.y < 0 or c.x >= m.w * 2 or c.y >= m.h * 2:
		return -1
	return m.cells[c.y][c.x]


func tile_walkable(c: Vector2i, m := map) -> bool:
	var t := tile_at(c, m)
	return t >= 0 and DB.tilesets[m.tileset].coll.has(t)


func is_water(c: Vector2i, m := map) -> bool:
	if not DB.extra.water_tilesets.has(m.tileset):
		return false
	var t := tile_at(c, m)
	return t == 0x14 or t == 0x48 or (t == 0x32 and m.tileset != "SHIP_PORT")


func npc_at(c: Vector2i) -> Actor:
	for a in npcs:
		if a.cell == c:
			return a
	return null


func remote_at(c: Vector2i) -> int:
	for id in remotes:
		if remotes[id].cell == c:
			return id
	return 0


func passable(c: Vector2i) -> bool:
	return tile_walkable(c) and npc_at(c) == null and c != player.cell


## 높낮이 차이(동굴 단차 등) 때문에 두 타일 사이를 못 지나가는지
func pair_blocked(from_c: Vector2i, to_c: Vector2i, water := false) -> bool:
	var a := tile_at(from_c)
	var b := tile_at(to_c)
	for p in (DB.extra.pair_water if water else DB.extra.pair_land):
		if p[0] == map.tileset and ((p[1] == a and p[2] == b) or (p[1] == b and p[2] == a)):
			return true
	return false


func warp_at(c: Vector2i):
	for w in map.warps:
		if w.x == c.x and w.y == c.y:
			return w
	return null


func find_npc(obj_id: String) -> Actor:
	for a in npcs:
		if a.data.get("id", "") == obj_id:
			return a
	return null


func remove_npc(obj_id: String) -> void:
	G.set_object_visible(obj_id, false)
	var a := find_npc(obj_id)
	if a:
		npcs.erase(a)
		a.queue_free()


func show_npc(obj_id: String) -> Actor:
	G.set_object_visible(obj_id, true)
	var a := find_npc(obj_id)
	if a:
		return a
	for n in map.npcs:
		if n.id == obj_id:
			a = Actor.new()
			world.add_child(a)
			a.setup(n.sprite_file, Vector2i(n.x, n.y), Actor.dir_from_name(n.dir))
			a.data = n
			npcs.append(a)
			return a
	return null


# ------------------------------------------------------------------ 메인 루프
func _process(delta: float) -> void:
	_update_npcs(delta)
	_bump_cd = maxf(0.0, _bump_cd - delta)
	if locked or walking or UI.busy > 0 or player.moving:
		return
	if not _pending_requests.is_empty():
		var r = _pending_requests.pop_front()
		run_event(func(): await Multi.handle_request(self, r[0], r[1]))
		return
	if UI.pressed("start"):
		Sound.sfx("Start_Menu")
		run_event(func(): await Menus.start_menu(self))
		return
	if UI.pressed("select"):
		# SELECT: 자전거 타기/내리기 단축키
		if G.bag.has("BICYCLE"):
			run_event(func(): await Field.toggle_bike(self))
		return
	if UI.pressed("a"):
		run_event(interact)
		return
	var dir := Vector2i.ZERO
	if Input.is_action_pressed("up"):
		dir = Vector2i.UP
	elif Input.is_action_pressed("down"):
		dir = Vector2i.DOWN
	elif Input.is_action_pressed("left"):
		dir = Vector2i.LEFT
	elif Input.is_action_pressed("right"):
		dir = Vector2i.RIGHT
	if dir == Vector2i.ZERO:
		_turn_delay = 0.0
		return
	if dir != player.facing:
		player.set_facing(dir)
		G.facing = dir
		Net.send_state(false)
		_turn_delay = 0.09
		return
	if _turn_delay > 0:
		_turn_delay -= delta
		return
	_walk(dir)


## 이벤트 실행 중에는 입력을 막고, 끝난 다음 프레임에 풀어준다(같은 A 입력 재사용 방지).
func run_event(fn: Callable) -> void:
	if locked:
		return
	locked = true
	await fn.call()
	await get_tree().process_frame
	locked = false


func _walk(dir: Vector2i) -> void:
	walking = true
	await _walk_inner(dir)
	walking = false


func _bump() -> void:
	if _bump_cd <= 0:
		Sound.sfx("Collision")
		_bump_cd = 0.35


func move_speed() -> float:
	if G.flag("biking"):
		return 2.2
	if G.flag("surfing"):
		return 1.0
	return 2.0 if Input.is_action_pressed("b") else 1.0


func _walk_inner(dir: Vector2i) -> void:
	var speed := move_speed()
	var surfing := G.flag("surfing")
	var target := player.cell + dir
	if not in_bounds(target):
		var conn = _connection(dir)
		if conn != null and _conn_target_ok(conn, target):
			await player.step(dir, speed)
			await _cross(conn, target)
			return
		var w = warp_at(player.cell)
		if w != null:
			await do_warp(w)
			return
		_bump()
		return
	# 턱 뛰어내리기
	if not surfing:
		var from_t := tile_at(player.cell)
		var to_t := tile_at(target)
		for l in LEDGES:
			if l[0] == dir and l[1] == from_t and l[2] == to_t:
				var land := target + dir
				if tile_walkable(land) and npc_at(land) == null:
					Sound.sfx("Ledge")
					await player.step(dir, speed, true)
					G.pos = player.cell
					Net.send_state()
					await _after_step()
				return
	# 괴력: 바위 밀기
	var blocker := npc_at(target)
	if blocker and blocker.data.get("sprite", "") == "SPRITE_BOULDER":
		if G.flag("strength_on"):
			await _push_boulder(blocker, dir)
		else:
			_bump()
		return
	if surfing:
		if pair_blocked(player.cell, target, true):
			_bump()
			return
		if is_water(target) and npc_at(target) == null and remote_at(target) == 0:
			await player.step(dir, speed)
		elif tile_walkable(target) and npc_at(target) == null:
			# 뭍으로 올라옴
			G.flags.erase("surfing")
			refresh_player_sprite()
			Sound.map_music(map_id)
			await player.step(dir, 1.0)
		else:
			_bump()
			return
		G.pos = player.cell
		Net.send_state()
		await _after_step()
		return
	if not passable(target) or pair_blocked(player.cell, target):
		var w2 = warp_at(player.cell)
		if w2 != null and not map.outdoor and not tile_walkable(target):
			await do_warp(w2)
			return
		_bump()
		return
	await player.step(dir, speed)
	G.pos = player.cell
	Net.send_state()
	await _after_step()


func _push_boulder(b: Actor, dir: Vector2i) -> void:
	var dest := b.cell + dir
	if not tile_walkable(dest) or npc_at(dest) != null or dest == player.cell or remote_at(dest) != 0 or warp_at(dest) != null:
		_bump()
		return
	Sound.sfx("Push_Boulder")
	await b.step(dir, 1.5)
	G.flags["pos:" + b.data.id] = [b.cell.x, b.cell.y]
	locked = true
	await Events.on_boulder(self, b)
	locked = false


func _after_step() -> void:
	if G.flags.has("daycare"):
		G.flags["daycare_steps"] = int(G.flags.get("daycare_steps", 0)) + 1
	var w = warp_at(player.cell)
	if w != null:
		locked = true
		await do_warp(w)
		locked = false
		return
	locked = true
	var handled: bool = await Field.check_spinner(self)
	if not handled:
		Field.check_forced_bike_surf(self)
		handled = await Events.on_step(self)
	if not handled:
		handled = await _check_trainers()
	if not handled:
		await _check_encounter()
	locked = false


# ------------------------------------------------------------------ 맵 이동
func _connection(dir: Vector2i):
	var dn: String = {Vector2i.UP: "north", Vector2i.DOWN: "south", Vector2i.LEFT: "west", Vector2i.RIGHT: "east"}[dir]
	for c in map.connections:
		if c.dir == dn and DB.maps.has(c.map):
			return c
	return null


func _conn_cell(conn: Dictionary, target: Vector2i) -> Vector2i:
	var nm: Dictionary = DB.maps[conn.map]
	match conn.dir:
		"north": return Vector2i(target.x - conn.offset * 2, nm.h * 2 - 1)
		"south": return Vector2i(target.x - conn.offset * 2, 0)
		"west": return Vector2i(nm.w * 2 - 1, target.y - conn.offset * 2)
		_: return Vector2i(0, target.y - conn.offset * 2)


func _conn_target_ok(conn: Dictionary, target: Vector2i) -> bool:
	var nm: Dictionary = DB.maps[conn.map]
	var c := _conn_cell(conn, target)
	if G.flag("surfing") and is_water(c, nm):
		return true
	return tile_walkable(c, nm)


func _cross(conn: Dictionary, target: Vector2i) -> void:
	var c := _conn_cell(conn, target)
	build(conn.map, c, player.facing)
	Net.send_state()
	locked = true
	await Events.on_enter(self)
	locked = false


func do_warp(w: Dictionary) -> void:
	var dest: String = w.map
	if dest == "LAST_MAP":
		dest = G.last_outdoor
	if not DB.maps.has(dest):
		return
	if not await Events.can_warp(self, dest):
		return
	var dm: Dictionary = DB.maps[dest]
	var idx: int = w.warp - 1
	if idx < 0 or idx >= dm.warps.size():
		return
	var dw: Dictionary = dm.warps[idx]
	G.flags["warp_from"] = [map_id, map.warps.find(w) + 1]
	Sound.sfx("Go_Outside" if dm.outdoor else "Go_Inside")
	if G.flag("biking") and not DB.extra.bike_tilesets.has(dm.tileset):
		G.flags.erase("biking")
	await UI.fade_out(0.2)
	build(dest, Vector2i(dw.x, dw.y), player.facing)
	Net.send_state(false)
	await UI.fade_in(0.2)
	# 문에서 나오면 한 칸 아래로 걸어나옴
	var t := tile_at(player.cell)
	if dm.outdoor and ts.get("doors", []).has(t):
		var below := player.cell + Vector2i.DOWN
		if passable(below):
			await player.step(Vector2i.DOWN)
			G.pos = player.cell
			Net.send_state()
	G.facing = player.facing
	await Events.on_enter(self)


func teleport_to(dest: String, at: Vector2i, dir := Vector2i.DOWN, fade := true) -> void:
	if fade:
		await UI.fade_out(0.2)
	if G.flag("biking") and not DB.extra.bike_tilesets.has(DB.maps[dest].tileset):
		G.flags.erase("biking")
	build(dest, at, dir)
	G.facing = dir
	Net.send_state(false)
	if fade:
		await UI.fade_in(0.2)


# ------------------------------------------------------------------ 야생/트레이너
func _check_encounter() -> void:
	var wd: Dictionary = DB.wild.get(map_id, {})
	if wd.is_empty() or G.party.is_empty() or G.first_alive() < 0:
		return
	var table: Dictionary
	if G.flag("surfing"):
		if not is_water(player.cell):
			return
		table = wd.water
	else:
		var t := tile_at(player.cell)
		var ok: bool = (ts.grass >= 0 and t == ts.grass) or (ts.grass < 0 and not map.outdoor)
		if not ok:
			return
		table = wd.grass
	if table.rate == 0 or table.mons.is_empty():
		return
	if randi() % 256 >= table.rate:
		return
	var r := randi() % 256
	var slot := 0
	while r >= SLOT_THRESH[slot]:
		slot += 1
	var entry: Array = table.mons[mini(slot, table.mons.size() - 1)]
	# 벌레회피스프레이: 선두 포켓몬보다 레벨이 낮은 야생 포켓몬은 나오지 않음
	if G.flags.get("repel", 0) > 0 and entry[0] < G.party[G.first_alive()].level:
		return
	var cfg := {"kind": "wild", "species": entry[1], "level": entry[0]}
	if StoryB.is_ghost_area(map_id):
		cfg["ghost"] = true
	if StoryB.is_safari_battle(map_id):
		cfg["safari"] = true
	await start_battle(cfg)


func tick_repel() -> void:
	if G.flags.get("repel", 0) > 0:
		G.flags.repel -= 1
		if G.flags.repel == 0:
			await UI.say("벌레회피스프레이의 효과가 사라졌다!")


func _check_trainers() -> bool:
	await tick_repel()
	for a in npcs:
		var info := trainer_info(a)
		if info.is_empty() or G.flag(info.event):
			continue
		var sight: int = info.sight
		for d in range(1, sight + 1):
			var c: Vector2i = a.cell + a.facing * d
			if c == player.cell:
				await engage_trainer(a, info)
				return true
			if not tile_walkable(c) or npc_at(c) != null:
				break
	return false


func trainer_info(a: Actor) -> Dictionary:
	var n: Dictionary = a.data
	if not n.has("trainer_class"):
		return {}
	var ti: Dictionary = map.texts.get(n.text, {})
	if ti.has("trainer"):
		return ti.trainer
	return {}


func engage_trainer(a: Actor, info: Dictionary) -> void:
	Sound.music(_meet_music(a.data.trainer_class))
	await show_emote(a)
	# 트레이너가 플레이어 앞까지 걸어옴
	while (player.cell - a.cell).length_squared() > 1:
		await a.step(a.facing)
	player.set_facing(-a.facing)
	G.facing = player.facing
	await UI.say(DB.text(info.battle))
	var res: String = await start_battle({
		"kind": "trainer", "class": a.data.trainer_class, "index": a.data.trainer_index,
		"end_text": DB.text(info.end),
	})
	if res == "win":
		G.set_flag(info.event)
		Events.on_trainer_beaten(self, a)


func _meet_music(cls: String) -> String:
	if cls.begins_with("ROCKET") or cls in ["GIOVANNI"]:
		return "MeetEvilTrainer"
	if cls in ["LASS", "BEAUTY", "JR_TRAINER_F", "COOLTRAINER_F", "CHANNELER"]:
		return "MeetFemaleTrainer"
	return "MeetMaleTrainer"


func talk_trainer(a: Actor, info: Dictionary) -> void:
	if G.flag(info.event):
		await UI.say(DB.text(info.after))
		return
	await UI.say(DB.text(info.battle))
	var res: String = await start_battle({
		"kind": "trainer", "class": a.data.trainer_class, "index": a.data.trainer_index,
		"end_text": DB.text(info.end),
	})
	if res == "win":
		G.set_flag(info.event)
		Events.on_trainer_beaten(self, a)


## 배틀 시작. 결과: "win" | "lose" | "run" | "caught"
func start_battle(cfg: Dictionary) -> String:
	var res: String = await Main.inst.run_battle(cfg)
	if res == "lose" and not cfg.get("no_blackout", false):
		await blackout()
	else:
		Sound.map_music(map_id)
	return res


func blackout() -> void:
	G.money = G.money / 2
	G.flags.erase("surfing")
	G.flags.erase("biking")
	G.flags.erase("safari")
	await UI.fade_out(0.4)
	G.heal_party()
	G.last_outdoor = G.flags.get("heal_outdoor", "PALLET_TOWN")
	build(G.heal_map, G.heal_pos, Vector2i.UP)
	Net.send_state(false)
	await UI.fade_in(0.4)
	await UI.say("{PLAYER}{은} 서둘러 포켓몬을 회복시켰다!")


func show_emote(a: Actor) -> void:
	var s := Sprite2D.new()
	s.texture = DB.tex("res://assets/misc/shock.png")
	s.centered = false
	s.position = Vector2(0, -20)
	s.z_index = 5
	a.add_child(s)
	await UI.wait(0.6)
	s.queue_free()


# ------------------------------------------------------------------ 상호작용
func interact() -> void:
	var front := player.cell + player.facing
	if ts.counters.has(tile_at(front)):
		front += player.facing
	var rid := remote_at(player.cell + player.facing)
	if rid != 0:
		await Multi.interact_player(self, rid)
		return
	var a := npc_at(front)
	if a != null:
		await talk(a)
		return
	for s in map.signs:
		if Vector2i(s.x, s.y) == player.cell + player.facing:
			if not await Events.on_sign(self, s):
				var t := DB.map_text(map_id, s.text)
				if t == "":
					t = _common_sign_text(s.text)
				if t != "":
					await UI.say(t)
			return
	for hdn in map.hidden:
		if Vector2i(hdn.x, hdn.y) == player.cell + player.facing or Vector2i(hdn.x, hdn.y) == front:
			await Events.on_hidden(self, hdn)
			return
	# 필드 기술 바로 쓰기 (나무 앞에서 풀베기, 물가에서 파도타기)
	await Field.interact_front(self)


func _common_sign_text(text_id: String) -> String:
	if text_id.ends_with("MART_SIGN"):
		return "모든 트레이너의 필수품!\n포켓몬마트"
	if text_id.ends_with("POKECENTER_SIGN"):
		return "포켓몬의 체력을 회복!\n포켓몬센터"
	return ""


func talk(a: Actor) -> void:
	if not a.single_frame:
		a.set_facing(-player.facing)
	if await Events.on_talk(self, a):
		return
	var n: Dictionary = a.data
	var ti: Dictionary = map.texts.get(n.text, {})
	if n.has("item"):
		await pick_up(a)
	elif n.has("pokemon"):
		await static_battle(a)
	elif n.sprite == "SPRITE_NURSE":
		await Menus.pokecenter(self)
	elif ti.has("label") and DB.marts.has(ti.label):
		await Menus.mart(DB.marts[ti.label])
	elif ti.has("mart"):
		await Menus.mart(ti.mart)
	elif ti.has("trainer"):
		await talk_trainer(a, ti.trainer)
	elif n.sprite == "SPRITE_LINK_RECEPTIONIST":
		await UI.say("통신 교환·대전은 친구에게 다가가서 A 버튼을 눌러 신청할 수 있어요!")
	elif n.sprite == "SPRITE_BOULDER":
		await UI.say(DB.text("_BoulderText") if DB.text("_BoulderText") != "" else "큰 바위다.\n괴력이 있으면 움직일 수 있을 것 같다.")
	else:
		var t := DB.map_text(map_id, n.text)
		await UI.say(t if t != "" else "...")


## 전설의 포켓몬/발전소 찌리리공 등 필드에 있는 포켓몬
func static_battle(a: Actor) -> void:
	var n: Dictionary = a.data
	var t := DB.map_text(map_id, n.text)
	if t != "":
		await UI.say(t)
	var sp: String = n.pokemon
	if n.sprite != "SPRITE_POKE_BALL":
		await Sound.cry(sp)
	var res: String = await start_battle({"kind": "wild", "species": sp, "level": n.level, "static": true})
	if res == "win" or res == "caught":
		G.set_flag("beat:" + n.id)
		npcs.erase(a)
		a.queue_free()


func pick_up(a: Actor) -> void:
	var item: String = a.data.item
	G.add_item(item)
	G.set_flag("got:" + a.data.id)
	npcs.erase(a)
	a.queue_free()
	Sound.jingle("Get_Item1")
	await UI.say("{PLAYER}{은} %s{을} 찾았다!" % DB.item_name(item))


## 아이템 받기 공통 연출
func receive(item: String, n := 1, from := "") -> void:
	G.add_item(item, n)
	Sound.jingle("Get_Key_Item" if Menus.KEY_ITEMS.has(item) else "Get_Item1")
	var cnt := "" if n == 1 else " %d개" % n
	if from != "":
		await UI.say("{PLAYER}{은} %s에게서\n%s%s{을} 받았다!" % [from, DB.item_name(item), cnt])
	else:
		await UI.say("{PLAYER}{은} %s%s{을} 받았다!" % [DB.item_name(item), cnt])


# ------------------------------------------------------------------ NPC 배회
func _update_npcs(delta: float) -> void:
	if locked or UI.busy > 0:
		return
	for a in npcs:
		if a.data.get("move", "") != "WALK" or a.moving or not is_instance_valid(a):
			continue
		_npc_timer[a] = _npc_timer.get(a, 1.0) - delta
		if _npc_timer[a] > 0:
			continue
		_npc_timer[a] = randf_range(1.0, 3.0)
		var dirs := [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]
		match a.data.dir:
			"UP_DOWN": dirs = [Vector2i.UP, Vector2i.DOWN]
			"LEFT_RIGHT": dirs = [Vector2i.LEFT, Vector2i.RIGHT]
		var d: Vector2i = dirs.pick_random()
		var t: Vector2i = a.cell + d
		if (t - a.origin).length() > 3 or not passable(t) or remote_at(t) != 0 or warp_at(t) != null:
			a.set_facing(d)
			continue
		a.step(d)


# ------------------------------------------------------------------ 원격 플레이어
func _sync_remotes() -> void:
	for id in remotes.keys():
		if not Net.peers.has(id) or Net.peers[id].get("map", "") != map_id:
			remotes[id].queue_free()
			remotes.erase(id)
	for id in Net.peers:
		_on_peer_state(id)


func _on_peer_state(id: int) -> void:
	if not is_instance_valid(world):
		return
	var p: Dictionary = Net.peers.get(id, {})
	if p.get("map", "") != map_id:
		if remotes.has(id):
			remotes[id].queue_free()
			remotes.erase(id)
		return
	var at := Vector2i(p.x, p.y)
	var dir := Vector2i(p.fx, p.fy)
	var spr: String = p.get("sprite", "red")
	if remotes.has(id) and remotes[id].get_meta("spr", "") != spr:
		remotes[id].queue_free()
		remotes.erase(id)
	if not remotes.has(id):
		var a := Actor.new()
		world.add_child(a)
		a.setup(spr, at, dir)
		a.set_meta("spr", spr)
		a.show_name(p.get("name", "?"))
		remotes[id] = a
		return
	remotes[id].glide_to(at, dir)
