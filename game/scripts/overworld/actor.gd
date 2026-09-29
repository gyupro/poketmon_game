class_name Actor
extends Node2D
## 필드 캐릭터(플레이어/NPC/다른 플레이어). 16x16 칸 단위 이동.
## 스프라이트 시트: 16x96 = [아래, 위, 왼쪽, 아래걷기, 위걷기, 왼쪽걷기]

const STEP_TIME := 0.24

var cell := Vector2i.ZERO
var facing := Vector2i.DOWN
var moving := false
var sprite: Sprite2D
var single_frame := false  # 몬스터볼 등 1프레임 스프라이트
var data := {}  # NPC 원본 데이터
var origin := Vector2i.ZERO
var _step_parity := false
var name_label: Label


func setup(sprite_file: String, at: Vector2i, dir := Vector2i.DOWN) -> Actor:
	sprite = Sprite2D.new()
	sprite.centered = false
	sprite.use_parent_material = true
	sprite.position = Vector2(0, -4)
	var t: Texture2D = DB.tex("res://assets/sprites/%s.png" % sprite_file)
	if t == null:
		t = DB.tex("res://assets/sprites/red.png")
	sprite.texture = t
	single_frame = t.get_height() <= 16
	sprite.region_enabled = true
	add_child(sprite)
	use_parent_material = true
	cell = at
	origin = at
	position = Vector2(at) * 16
	set_facing(dir)
	return self


func set_facing(dir: Vector2i) -> void:
	if dir != Vector2i.ZERO:
		facing = dir
	_update_frame(false)


func _update_frame(walk: bool) -> void:
	if single_frame:
		sprite.region_rect = Rect2(0, 0, 16, 16)
		return
	var f := 0
	var flip := false
	match facing:
		Vector2i.DOWN:
			f = 3 if walk else 0
			flip = walk and _step_parity
		Vector2i.UP:
			f = 4 if walk else 1
			flip = walk and _step_parity
		Vector2i.LEFT:
			f = 5 if walk else 2
		Vector2i.RIGHT:
			f = 5 if walk else 2
			flip = true
	sprite.region_rect = Rect2(0, f * 16, 16, 16)
	sprite.flip_h = flip


## 한 칸 이동(애니메이션). jump=true 면 턱 뛰어넘기(2칸).
func step(dir: Vector2i, speed := 1.0, jump := false) -> void:
	moving = true
	set_facing(dir)
	var dist := 2 if jump else 1
	var target := cell + dir * dist
	cell = target
	var dur := STEP_TIME * dist / speed
	var tw := create_tween()
	tw.tween_property(self, "position", Vector2(target) * 16, dur)
	if jump:
		var tj := create_tween()
		tj.tween_property(sprite, "position:y", -12.0, dur / 2).set_ease(Tween.EASE_OUT)
		tj.tween_property(sprite, "position:y", -4.0, dur / 2).set_ease(Tween.EASE_IN)
	_step_parity = not _step_parity
	_update_frame(true)
	await get_tree().create_timer(dur / 2).timeout
	_update_frame(false)
	await tw.finished
	moving = false


func teleport(at: Vector2i) -> void:
	cell = at
	position = Vector2(at) * 16


## 원격 플레이어용: 목표 칸으로 부드럽게 이동
func glide_to(at: Vector2i, dir: Vector2i) -> void:
	var diff := at - cell
	if abs(diff.x) + abs(diff.y) == 1:
		step(diff)
		set_facing(dir)
	else:
		teleport(at)
		set_facing(dir)


func show_name(text: String) -> void:
	if name_label == null:
		name_label = Label.new()
		name_label.add_theme_font_size_override("font_size", 8)
		name_label.add_theme_color_override("font_color", Color.WHITE)
		name_label.add_theme_color_override("font_outline_color", Color.BLACK)
		name_label.add_theme_constant_override("outline_size", 3)
		name_label.material = CanvasItemMaterial.new()
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name_label.size = Vector2(64, 10)
		name_label.position = Vector2(-24, -16)
		name_label.z_index = 10
		add_child(name_label)
	name_label.text = text


static func dir_from_name(n: String) -> Vector2i:
	match n:
		"UP": return Vector2i.UP
		"LEFT": return Vector2i.LEFT
		"RIGHT": return Vector2i.RIGHT
	return Vector2i.DOWN
