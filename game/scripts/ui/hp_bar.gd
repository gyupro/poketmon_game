class_name HPBar
extends Control
## 체력 바

var ratio := 1.0:
	set(v):
		ratio = clampf(v, 0.0, 1.0)
		queue_redraw()


func _init(pos := Vector2.ZERO, w := 48.0) -> void:
	position = pos
	size = Vector2(w + 12, 5)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var dark := Color(0.1, 0.1, 0.1)
	# "HP" 라벨 대신 작은 표시
	draw_rect(Rect2(0, 0, 11, 5), dark)
	draw_string(UI.font, Vector2(1, 5), "HP", HORIZONTAL_ALIGNMENT_LEFT, -1, 6, Color(1, 0.8, 0.2))
	var bw := size.x - 12
	var r := Rect2(11, 0, bw + 1, 5)
	draw_rect(r, dark)
	draw_rect(Rect2(12, 1, bw - 1, 3), Color.WHITE)
	var c := Color(0.2, 0.75, 0.3) if ratio > 0.5 else (Color(0.95, 0.75, 0.1) if ratio > 0.2 else Color(0.9, 0.2, 0.15))
	var fw := ceilf((bw - 1) * ratio) if ratio > 0 else 0.0
	if fw > 0:
		draw_rect(Rect2(12, 1, fw, 3), c)
