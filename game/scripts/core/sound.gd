extends Node
## 음악/효과음/울음소리 재생. 원작 음원은 tools/audio_render.py 가 렌더링한 WAV.
## 음악: Sound.music("PalletTown")  효과음: Sound.sfx("Press_AB")  울음: await Sound.cry("PIKACHU")

var meta := {}
var _music: AudioStreamPlayer
var _jingle: AudioStreamPlayer
var _sfx: Array[AudioStreamPlayer] = []
var current := ""
var _paused_for_jingle := ""
var music_volume := 0.8
var sfx_volume := 0.9
var muted := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var f := FileAccess.open("res://data/audio.json", FileAccess.READ)
	if f:
		meta = JSON.parse_string(f.get_as_text())
	_music = AudioStreamPlayer.new()
	add_child(_music)
	_jingle = AudioStreamPlayer.new()
	add_child(_jingle)
	for i in 4:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_sfx.append(p)
	_apply_volume()


func _apply_volume() -> void:
	_music.volume_db = linear_to_db(0.0 if muted else music_volume)
	_jingle.volume_db = _music.volume_db
	for p in _sfx:
		p.volume_db = linear_to_db(0.0 if muted else sfx_volume)


func toggle_mute() -> void:
	muted = not muted
	_apply_volume()


func _load(kind: String, name: String) -> AudioStreamWAV:
	var path := "res://assets/audio/%s/%s.wav" % [kind, name]
	if not ResourceLoader.exists(path):
		return null
	return load(path)


## 배경음악. 같은 곡이면 이어서 재생.
func music(name: String, restart := false) -> void:
	if name == "" or (name == current and _music.playing and not restart):
		return
	var s := _load("music", name)
	if s == null:
		return
	var info: Dictionary = meta.get("music", {}).get(name, {})
	var loop = info.get("loop")
	if loop != null:
		s.loop_mode = AudioStreamWAV.LOOP_FORWARD
		s.loop_begin = int(loop[0])
		s.loop_end = int(loop[1])
	else:
		s.loop_mode = AudioStreamWAV.LOOP_DISABLED
	current = name
	_jingle.stop()
	_music.stream = s
	_music.play()


func stop_music() -> void:
	current = ""
	_music.stop()


func fade_out_music(t := 0.5) -> void:
	var tw := create_tween()
	tw.tween_property(_music, "volume_db", -40.0, t)
	await tw.finished
	stop_music()
	_apply_volume()


## 짧은 팡파레(회복, 아이템 획득 등): 배경음악을 잠시 멈추고 끝나면 이어서.
func jingle(name: String) -> void:
	var s := _load("music", name)
	if s == null:
		s = _load("sfx", name)
	if s == null:
		return
	s.loop_mode = AudioStreamWAV.LOOP_DISABLED
	var pos := _music.get_playback_position()
	var was := _music.playing
	_music.stop()
	_jingle.stream = s
	_jingle.play()
	await _jingle.finished
	if was and current != "":
		_music.play(pos)


func sfx(name: String) -> void:
	var s := _load("sfx", name)
	if s == null:
		return
	for p in _sfx:
		if not p.playing:
			p.stream = s
			p.play()
			return
	_sfx[0].stream = s
	_sfx[0].play()


## 효과음 재생 후 끝날 때까지 대기
func sfx_wait(name: String) -> void:
	var s := _load("sfx", name)
	if s == null:
		return
	var p := _sfx[3]
	p.stream = s
	p.play()
	await p.finished


func cry(species: String) -> void:
	var s := _load("cries", species.to_lower())
	if s == null:
		return
	var p := _sfx[3]
	p.stream = s
	p.play()
	await p.finished


## 현재 맵의 기본 음악 (자전거/파도타기 우선)
func map_music(map_id: String) -> void:
	if G.flags.get("surfing", false):
		music("Surfing")
		return
	if G.flags.get("biking", false):
		music("BikeRiding")
		return
	var m: Dictionary = DB.maps.get(map_id, {})
	music(m.get("music", ""))
