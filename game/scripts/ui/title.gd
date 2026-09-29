class_name Title
extends CanvasLayer
## 타이틀: 새 게임/이어하기 → 접속 방식 선택(혼자/방 만들기/참가)

const TITLE_MONS := ["CHARMANDER", "SQUIRTLE", "BULBASAUR", "PIKACHU", "EEVEE", "MEWTWO", "GENGAR", "SNORLAX", "LAPRAS", "DRAGONITE"]

var root: Control
var mon_pic: TextureRect


func _ready() -> void:
	root = Control.new()
	root.size = Vector2(160, 144)
	add_child(root)
	var bg := ColorRect.new()
	bg.color = Color.WHITE
	bg.size = Vector2(160, 144)
	root.add_child(bg)
	var logo := TextureRect.new()
	logo.texture = DB.tex("res://assets/misc/pokemon_logo.png")
	logo.position = Vector2(16, 6)
	root.add_child(logo)
	var ver := GBBox.label("레드 버전 · 온라인", Vector2(40, 60))
	ver.add_theme_color_override("font_color", Color(0.8, 0.1, 0.1))
	root.add_child(ver)
	mon_pic = TextureRect.new()
	mon_pic.position = Vector2(92, 76)
	root.add_child(mon_pic)
	var red := TextureRect.new()
	red.texture = DB.tex("res://assets/misc/red_front.png")
	red.position = Vector2(24, 80)
	root.add_child(red)
	_cycle_mons()
	_run()


func _cycle_mons() -> void:
	while is_inside_tree():
		mon_pic.texture = Mon.front_tex(TITLE_MONS.pick_random())
		await get_tree().create_timer(2.5).timeout


func _run() -> void:
	await get_tree().process_frame
	while true:
		var saves := G.list_saves()
		var opts := ["새로 시작"]
		if not saves.is_empty():
			opts.insert(0, "이어서 하기")
		var c: int = await UI.choose(opts, Rect2(40, 104, 88, opts.size() * 14 + 10), 0, 1, false)
		var ok := false
		if opts[c] == "이어서 하기":
			ok = await _continue(saves)
		else:
			ok = await _new_game()
		if not ok:
			continue
		if await _network():
			break
	root.visible = false
	Main.inst.start_overworld()
	queue_free()


func _continue(saves: Array) -> bool:
	var opts := []
	for s in saves:
		var t := int(s.get("play_time", 0))
		opts.append("%s  %d:%02d" % [s.player_name, t / 3600, (t / 60) % 60])
	var k: int = await UI.choose(opts, Rect2(8, 40, 144, mini(opts.size() * 14 + 10, 96)))
	if k < 0:
		return false
	G.load_from(saves[k])
	return true


func _new_game() -> bool:
	var pname := await UI.text_input("이름을 알려 주렴! (최대 7자)", "레드", 7)
	if pname == "":
		return false
	# 캐릭터 모습 선택
	var preview := TextureRect.new()
	preview.position = Vector2(20, 30)
	preview.scale = Vector2(3, 3)
	var at := AtlasTexture.new()
	at.region = Rect2(0, 0, 16, 16)
	preview.texture = at
	root.add_child(preview)
	var labels := ["빨강 모자", "파랑 머리", "반바지 꼬마", "소녀", "엘리트♂", "엘리트♀", "등산가", "낚시꾼"]
	var k: int = await UI.choose(labels, Rect2(80, 0, 80, 124), 0, 1, true, func(i):
		at.atlas = DB.tex("res://assets/sprites/%s.png" % G.SPRITES[i]))
	preview.queue_free()
	if k < 0:
		return false
	G.new_game(pname, G.SPRITES[k])
	await UI.say("오박사: 포켓몬스터의 세계에 잘 왔단다!\f이 세계에는 포켓몬이라 불리는 생물들이 살고 있지!\f{PLAYER}! 너만의 포켓몬 이야기가\n지금 시작된다!\f꿈과 모험과! 포켓몬스터의 세계로!\n렛츠 고!")
	return true


func _network() -> bool:
	await UI.say("어떻게 플레이할까?", true, false)
	var c: int = await UI.choose(["혼자 하기", "방 만들기 (호스트)", "친구 방 참가"], Rect2(24, 44, 136, 52))
	match c:
		0:
			UI.close_box()
			return true
		1:
			var err := Net.host()
			if err != OK:
				await UI.say("방을 만들 수 없었다. (포트 %d 사용 중?)" % Net.PORT)
				return false
			await UI.say("방을 만들었다!\f친구에게 이 IP를 알려 줘:\n%s\f(포트 %d · 인터넷이면 포트포워딩\n또는 Radmin VPN/Tailscale 필요)" % [", ".join(Net.local_ips()), Net.PORT])
			return true
		2:
			var ip := await UI.text_input("호스트 IP 주소:", "127.0.0.1", 40)
			if ip == "":
				return false
			var ok: bool = await Multi.join_flow(ip)
			UI.close_box()
			return ok
	UI.close_box()
	return false
