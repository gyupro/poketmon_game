class_name GBBox
extends Control
## 게임보이 스타일 테두리 상자.

var fill := Color.WHITE
var line := Color(0.1, 0.1, 0.1)


func _init(r := Rect2()) -> void:
	position = r.position
	size = r.size
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	draw_rect(r, fill)
	draw_rect(r.grow(-1.5), line, false, 2.0)
	draw_rect(r.grow(-4.5), line, false, 1.0)


static func label(text: String, pos: Vector2, font_size := 10, color := Color(0.1, 0.1, 0.1)) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
