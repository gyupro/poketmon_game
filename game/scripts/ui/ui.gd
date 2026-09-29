extends CanvasLayer
## 전역 UI: 대화창, 선택 메뉴, 예/아니오, 수량 선택, 화면 전환.
## 모든 함수는 코루틴이므로 `await UI.say("...")` 처럼 사용한다.

const W := 160
const H := 144
const TEXT_COLOR := Color(0.1, 0.1, 0.1)
const CHARS_PER_SEC := 90.0

var busy := 0  # 0보다 크면 필드 입력 차단
var font: Font
var _fade: ColorRect
var _root: Control


func _ready() -> void:
	layer = 50
	font = load("res://assets/font/Galmuri9.ttf")
	_root = Control.new()
	_root.size = Vector2(W, H)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_fade = ColorRect.new()
	_fade.size = Vector2(W, H)
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var fl := CanvasLayer.new()
	fl.layer = 100
	add_child(fl)
	fl.add_child(_fade)
	process_mode = Node.PROCESS_MODE_ALWAYS


func root() -> Control:
	return _root


var _josa_re := RegEx.create_from_string("([^\\s{}]+)\\{(은|이|을|와|으로|아)\\}")


func fmt(t: String) -> String:
	t = t.replace("는(은)", "{은}").replace("은(는)", "{은}").replace("을(를)", "{을}").replace("를(을)", "{을}") \
		.replace("이(가)", "{이}").replace("가(이)", "{이}").replace("와(과)", "{와}").replace("(으)로", "{으로}")
	t = t.replace("{PLAYER}", G.player_name).replace("{RIVAL}", G.RIVAL_NAME) \
		.replace("POKéMON", "포켓몬").replace("POKé", "포켓")
	# "{조사}" 를 앞 단어 받침에 맞게 치환
	var out := ""
	var last := 0
	for m in _josa_re.search_all(t):
		out += t.substr(last, m.get_start() - last) + josa(m.get_string(1), m.get_string(2))
		last = m.get_end()
	out += t.substr(last)
	return out


## 한국어 조사: josa("피카츄", "은") -> "피카츄는"
func josa(word: String, kind: String) -> String:
	if word == "":
		return word
	var c := word.unicode_at(word.length() - 1)
	var has_final := false
	var rieul := false
	if c >= 0xAC00 and c <= 0xD7A3:
		var jong := (c - 0xAC00) % 28
		has_final = jong != 0
		rieul = jong == 8
	elif "013678".contains(char(c)):
		has_final = true
		rieul = "178".contains(char(c))
	var pairs := {"은": ["은", "는"], "이": ["이", "가"], "을": ["을", "를"], "와": ["과", "와"], "으로": ["으로", "로"], "아": ["아", "야"]}
	if not pairs.has(kind):
		return word + kind
	if kind == "으로" and rieul:
		return word + "로"
	return word + (pairs[kind][0] if has_final else pairs[kind][1])


var _injected := {}  # 테스트용 가상 입력: action -> 만료 프레임


func inject(action: String) -> void:
	_injected[action] = Engine.get_process_frames() + 10


func pressed(action: String) -> bool:
	if _injected.has(action):
		var exp: int = _injected[action]
		_injected.erase(action)
		if Engine.get_process_frames() <= exp:
			return true
	return Input.is_action_just_pressed(action)


func frame() -> void:
	await get_tree().process_frame


# ------------------------------------------------------------------ 텍스트
func wrap_text(text: String, width: float, size := 10) -> PackedStringArray:
	var out := PackedStringArray()
	for para in text.split("\n"):
		var line := ""
		for word in para.split(" "):
			var cand := word if line == "" else line + " " + word
			if font.get_string_size(cand, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x <= width:
				line = cand
				continue
			if line != "":
				out.append(line)
			line = ""
			# 한 단어가 너무 길면 글자 단위로 자름
			for ch in word:
				if font.get_string_size(line + ch, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width:
					out.append(line)
					line = ""
				line += ch
		out.append(line)
	return out


## 대화창에 텍스트 출력. 페이지(\f)마다, 2줄씩 A 버튼 대기.
## keep_open=true 면 마지막 페이지 후 창을 닫지 않고 반환(선택지 표시용) — close_box()로 닫는다.
var _box: GBBox
var _lbl: Label
var _arrow: Label


func say(text: String, keep_open := false, wait_last := true) -> void:
	busy += 1
	text = fmt(text)
	_ensure_box()
	var pages := text.split("\f")
	for pi in pages.size():
		var lines := wrap_text(pages[pi], W - 18)
		var i := 0
		while i < lines.size():
			var chunk := lines[i]
			if i + 1 < lines.size():
				chunk += "\n" + lines[i + 1]
			await _type(chunk)
			i += 2
			var last := pi == pages.size() - 1 and i >= lines.size()
			if last and not wait_last:
				break
			await _wait_a(not (last and keep_open))
	if not keep_open:
		close_box()
	busy -= 1


func _ensure_box() -> void:
	if _box != null:
		return
	_box = GBBox.new(Rect2(0, 96, W, 48))
	_root.add_child(_box)
	_lbl = GBBox.label("", Vector2(8, 5))
	_lbl.add_theme_constant_override("line_spacing", 3)
	_box.add_child(_lbl)
	_arrow = GBBox.label("▼", Vector2(146, 35), 8)
	_arrow.visible = false
	_box.add_child(_arrow)


func close_box() -> void:
	if _box:
		_box.queue_free()
		_box = null


func _type(chunk: String) -> void:
	_lbl.text = chunk
	_lbl.visible_characters = 0
	var t := 0.0
	while _lbl.visible_characters < chunk.length():
		await frame()
		t += get_process_delta_time() * CHARS_PER_SEC
		if Input.is_action_pressed("a") or Input.is_action_pressed("b"):
			t += 4
		_lbl.visible_characters = int(t)
	_lbl.visible_characters = -1


func _wait_a(show_arrow := true) -> void:
	_arrow.visible = show_arrow
	var blink := 0.0
	await frame()
	while not (pressed("a") or pressed("b")):
		blink += get_process_delta_time()
		_arrow.visible = show_arrow and fmod(blink, 0.8) < 0.5
		await frame()
	_arrow.visible = false


## 자동 진행 메시지(배틀 등): A를 누르거나 delay 초 후 진행
func say_auto(text: String, delay := 1.0) -> void:
	busy += 1
	_ensure_box()
	await _type(fmt(text))
	var t := 0.0
	while t < delay and not pressed("a"):
		t += get_process_delta_time()
		await frame()
	busy -= 1


# ------------------------------------------------------------------ 메뉴
## options: 문자열 배열. 반환: 선택 인덱스, 취소 시 -1
func choose(options: Array, rect: Rect2, start := 0, cols := 1, allow_cancel := true, on_move := Callable()) -> int:
	busy += 1
	var box := GBBox.new(rect)
	_root.add_child(box)
	var rows := int(ceil(options.size() / float(cols)))
	var col_w := (rect.size.x - 16) / cols
	# 줄 간격: 기본 14px, 부족하면 11px 까지 줄이고 그래도 안 되면 스크롤
	var max_rows := maxi(1, int((rect.size.y - 10) / 11.0))
	var scroll := cols == 1 and rows > max_rows
	var vis_rows := max_rows if scroll else rows
	var row_h := minf(14.0, (rect.size.y - 10) / max(vis_rows, 1))
	var labels := []
	for i in (vis_rows if scroll else options.size()):
		var c := i % cols
		var r := i / cols
		var l := GBBox.label("", Vector2(14 + c * col_w, 4 + r * row_h))
		box.add_child(l)
		labels.append(l)
	var more := GBBox.label("▼", Vector2(rect.size.x - 12, rect.size.y - 12), 7)
	box.add_child(more)
	var cursor := GBBox.label("▶", Vector2.ZERO, 8)
	box.add_child(cursor)
	var idx := clampi(start, 0, options.size() - 1)
	var top := 0
	var result := -1
	await frame()
	while true:
		if scroll:
			if idx < top:
				top = idx
			elif idx >= top + vis_rows:
				top = idx - vis_rows + 1
			for i in labels.size():
				labels[i].text = str(options[top + i]) if top + i < options.size() else ""
			more.visible = top + vis_rows < options.size()
			cursor.position = labels[idx - top].position + Vector2(-8, 2)
		else:
			for i in labels.size():
				labels[i].text = str(options[i])
			more.visible = false
			cursor.position = labels[idx].position + Vector2(-8, 2)
		if on_move.is_valid():
			on_move.call(idx)
		await frame()
		if pressed("down") and idx + cols < options.size():
			idx += cols
		elif pressed("up") and idx - cols >= 0:
			idx -= cols
		elif pressed("right") and cols > 1 and idx % cols < cols - 1 and idx + 1 < options.size():
			idx += 1
		elif pressed("left") and cols > 1 and idx % cols > 0:
			idx -= 1
		elif pressed("down") and cols == 1:
			idx = 0
		elif pressed("up") and cols == 1:
			idx = options.size() - 1
		elif pressed("a"):
			Sound.sfx("Press_AB")
			result = idx
			break
		elif pressed("b") and allow_cancel:
			result = -1
			break
	box.queue_free()
	busy -= 1
	return result


func yes_no(rect := Rect2(112, 56, 48, 40)) -> bool:
	return await choose(["예", "아니오"], rect, 0, 1, true) == 0


## 수량 선택 (1..max_n). price>0 이면 가격 표시. 취소 시 0
func number(max_n: int, rect: Rect2, price := 0) -> int:
	busy += 1
	var box := GBBox.new(rect)
	_root.add_child(box)
	var l := GBBox.label("", Vector2(8, 5))
	box.add_child(l)
	var n := 1
	var result := 0
	await frame()
	while true:
		l.text = "×%02d" % n + ("  ₩%d" % (n * price) if price > 0 else "")
		await frame()
		if pressed("up"):
			n = n % max_n + 1
		elif pressed("down"):
			n = (n - 2 + max_n) % max_n + 1
		elif pressed("right"):
			n = mini(n + 10, max_n)
		elif pressed("left"):
			n = maxi(n - 10, 1)
		elif pressed("a"):
			result = n
			break
		elif pressed("b"):
			break
	box.queue_free()
	busy -= 1
	return result


# ------------------------------------------------------------------ 화면 효과
func fade_out(t := 0.25, color := Color.BLACK) -> void:
	_fade.color = Color(color, 0)
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, t)
	await tw.finished


func fade_in(t := 0.25) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 0.0, t)
	await tw.finished


func wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout


## 화면 위에 잠깐 띄우는 알림(네트워크 요청 등)
func toast(text: String, sec := 2.0) -> void:
	var box := GBBox.new(Rect2(0, 0, W, 22))
	box.add_child(GBBox.label(fmt(text), Vector2(8, 4)))
	_root.add_child(box)
	await wait(sec)
	box.queue_free()


## 텍스트 입력 (한글 IME 지원). Enter 로 확정, Esc 로 취소("" 반환)
func text_input(prompt: String, default := "", max_len := 20) -> String:
	busy += 1
	var box := GBBox.new(Rect2(0, 32, W, 64))
	_root.add_child(box)
	var pl := GBBox.label(fmt(prompt), Vector2(8, 5))
	pl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pl.size = Vector2(W - 16, 26)
	box.add_child(pl)
	var le := LineEdit.new()
	le.text = default
	le.max_length = max_len
	le.position = Vector2(8, 32)
	le.size = Vector2(W - 16, 16)
	le.add_theme_font_size_override("font_size", 10)
	le.add_theme_color_override("font_color", TEXT_COLOR)
	le.add_theme_color_override("caret_color", TEXT_COLOR)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.95, 0.95, 0.95)
	sb.border_color = TEXT_COLOR
	sb.set_border_width_all(1)
	sb.content_margin_left = 3
	le.add_theme_stylebox_override("normal", sb)
	le.add_theme_stylebox_override("focus", sb)
	le.select_all_on_focus = true
	box.add_child(le)
	box.add_child(GBBox.label("Enter: 확인  Esc: 취소", Vector2(8, 50), 7))
	le.grab_focus()
	var state := {"done": false, "text": ""}
	le.text_submitted.connect(func(t): state.done = true; state.text = t.strip_edges())
	while not state.done:
		await frame()
		if Input.is_key_pressed(KEY_ESCAPE):
			state.done = true
			state.text = ""
		elif _injected.has("text_submit"):
			_injected.erase("text_submit")
			state.done = true
			state.text = le.text.strip_edges()
	box.queue_free()
	await frame()
	busy -= 1
	return state.text
