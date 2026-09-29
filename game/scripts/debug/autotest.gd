extends Node
## 자동 테스트 (개발용). 실행: Godot --path game -- autotest=<명령파일> shots=<폴더>
## 명령: wait S | tap ACT | hold ACT S | shot NAME | newgame NAME | warp MAP X Y
##       battle SPECIES LV | give SPECIES LV | flag NAME | item NAME N | host | join IP | quit

var cmds: PackedStringArray
var shots_dir := "user://shots"
var _rec_frames: Array = []
var _recording := false


func run(path: String, shots: String) -> void:
	shots_dir = shots
	G.autosave = false
	DirAccess.make_dir_recursive_absolute(shots_dir)
	cmds = FileAccess.get_file_as_string(path).split("\n")
	for raw in cmds:
		var line := raw.strip_edges()
		if line == "" or line.begins_with("#"):
			continue
		var a := line.split(" ", false)
		print("[autotest] ", line)
		match a[0]:
			"wait":
				await get_tree().create_timer(float(a[1])).timeout
			"tap":
				UI.inject(a[1])
				await get_tree().create_timer(0.15).timeout
			"hold":
				Input.action_press(a[1])
				await get_tree().create_timer(float(a[2])).timeout
				Input.action_release(a[1])
				await get_tree().process_frame
			"shot":
				await RenderingServer.frame_post_draw
				var img := get_viewport().get_texture().get_image()
				img.save_png(shots_dir.path_join(a[1] + ".png"))
			"newgame":
				G.new_game(a[1], "red")
				Main.inst.start_overworld()
				await get_tree().create_timer(0.3).timeout
			"warp":
				await Main.inst.ow.teleport_to(a[1], Vector2i(int(a[2]), int(a[3])), Vector2i.DOWN, false)
			"battle":
				Main.inst.ow.run_event(func(): await Main.inst.ow.start_battle({"kind": "wild", "species": a[1], "level": int(a[2])}))
			"trainer":
				Main.inst.ow.run_event(func(): await Main.inst.ow.start_battle({"kind": "trainer", "class": a[1], "index": int(a[2])}))
			"give":
				G.give_mon(Mon.create(a[1], int(a[2]), G.player_name))
			"flag":
				G.set_flag(a[1])
			"item":
				G.add_item(a[1], int(a[2]))
			"host":
				print("host: ", Net.host())
			"join":
				print("join: ", Net.join(a[1]))
			"allmaps":
				var n := 0
				for k in DB.maps:
					Main.inst.ow.build(k, Vector2i(2, 2), Vector2i.DOWN)
					await get_tree().process_frame
					n += 1
				print("allmaps ok: ", n)
			"title":
				Main.inst.add_child(Title.new())
			"inject":
				UI.inject(a[1])
				await get_tree().create_timer(0.15).timeout
			"mart":
				Main.inst.ow.run_event(func(): await Menus.mart(DB.marts[a[1]]))
			"pc":
				Main.inst.ow.run_event(func(): await Menus.pc())
			"walk":
				var d: Vector2i = {"up": Vector2i.UP, "down": Vector2i.DOWN, "left": Vector2i.LEFT, "right": Vector2i.RIGHT}[a[1]]
				for i in (int(a[2]) if a.size() > 2 else 1):
					var ow: Overworld = Main.inst.ow
					while ow.locked or ow.walking or UI.busy > 0 or ow.player.moving:
						await get_tree().process_frame
					if ow.player.facing != d:
						ow.player.set_facing(d)
						G.facing = d
					ow._walk(d)
					await get_tree().process_frame
					while ow.walking and UI.busy == 0:
						await get_tree().process_frame
			"face":
				var d2: Vector2i = {"up": Vector2i.UP, "down": Vector2i.DOWN, "left": Vector2i.LEFT, "right": Vector2i.RIGHT}[a[1]]
				Main.inst.ow.player.set_facing(d2)
				G.facing = d2
			"teach":
				Mon.learn_move(G.party[int(a[1])], a[2], int(a[3]) if a.size() > 3 else -1)
			"print":
				var e := Expression.new()
				var src := line.substr(6)
				if e.parse(src, ["ow", "G", "DB", "UI"]) == OK:
					print("[print] ", src, " = ", e.execute([Main.inst.ow, G, DB, UI], self))
				else:
					print("[print] parse error: ", e.get_error_text())
			"idle":
				var ow2: Overworld = Main.inst.ow
				var t := 0.0
				while (ow2.locked or UI.busy > 0) and t < float(a[1]):
					await get_tree().process_frame
					t += get_process_delta_time()
			"talk":
				var ow3: Overworld = Main.inst.ow
				var ac := ow3.find_npc(a[1])
				if ac == null:
					print("[talk] 없음: ", a[1])
					continue
				for d3 in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
					var c3: Vector2i = ac.cell + d3
					if ow3.tile_walkable(c3) and ow3.npc_at(c3) == null or d3 == Vector2i.UP:
						ow3.player.teleport(c3)
						G.pos = c3
						ow3.player.set_facing(-d3)
						break
				ow3.run_event(func(): await ow3.talk(ac))
				await get_tree().process_frame
			"auto":
				# 대화/배틀이 끝날 때까지 A 연타 (최대 N초)
				var limit := float(a[1]) if a.size() > 1 else 30.0
				var t4 := 0.0
				var idle_t := 0.0
				while t4 < limit:
					var ow4: Overworld = Main.inst.ow
					var active: bool = ow4.locked or UI.busy > 0 or ow4.player.moving or not ow4.visible
					for pm in G.party:
						for mv in pm.moves:
							mv.pp = mv.max
					if active:
						UI.inject("a")
						idle_t = 0.0
					else:
						idle_t += 0.2
						if idle_t > 1.0:
							break
					await get_tree().create_timer(0.2).timeout
					t4 += 0.2
				await get_tree().create_timer(0.4).timeout
			"safaritest":
				# 사파리 배틀 한 번 + 걸음 수 소진
				var ow7: Overworld = Main.inst.ow
				G.flags["safari_balls"] = 30
				ow7.run_event(func(): await ow7.start_battle({"kind": "wild", "species": "RHYHORN", "level": 25, "safari": true}))
				await get_tree().process_frame
			"setpos":
				# setpos NPC_ID X Y  (다음 warp 에서 적용)
				G.flags["pos:" + a[1]] = [int(a[2]), int(a[3])]
			"rec":
				# rec start | rec stop NAME  (0.1초마다 화면 캡처)
				if a[1] == "start":
					_rec_frames.clear()
					_recording = true
					_record_loop()
				else:
					_recording = false
					await get_tree().create_timer(0.2).timeout
					for i in _rec_frames.size():
						var im: Image = _rec_frames[i]
						im.resize(320, 288, Image.INTERPOLATE_NEAREST)
						im.save_png(shots_dir.path_join("%s_%04d.png" % [a[2], i]))
					print("[rec] saved ", _rec_frames.size())
			"useitem":
				var ow6: Overworld = Main.inst.ow
				ow6.run_event(func(): await Field.use_key_item(ow6, a[1]))
				await get_tree().process_frame
			"stepto":
				# (x,y) 옆에서 걸어 들어가기: stepto X Y DIR
				var ow5: Overworld = Main.inst.ow
				var dd: Vector2i = {"up": Vector2i.UP, "down": Vector2i.DOWN, "left": Vector2i.LEFT, "right": Vector2i.RIGHT}[a[3]]
				var tgt := Vector2i(int(a[1]), int(a[2]))
				ow5.player.teleport(tgt - dd)
				G.pos = tgt - dd
				ow5.player.set_facing(dd)
				ow5._walk(dd)
				await get_tree().create_timer(0.5).timeout
			"quit":
				get_tree().quit()


func _record_loop() -> void:
	while _recording:
		await RenderingServer.frame_post_draw
		_rec_frames.append(get_viewport().get_texture().get_image())
		await get_tree().create_timer(0.1).timeout
