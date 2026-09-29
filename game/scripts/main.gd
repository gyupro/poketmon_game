class_name Main
extends Node
## 화면 전환 관리 (타이틀 → 필드 ↔ 배틀)

static var inst: Main

var ow: Overworld


func _ready() -> void:
	inst = self
	var args := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else ""
	if args.has("autotest"):
		var t: Node = load("res://scripts/debug/autotest.gd").new()
		get_tree().root.add_child.call_deferred(t)
		await get_tree().process_frame
		t.run(args.autotest, args.get("shots", "user://shots"))
		return
	add_child(Title.new())


func start_overworld() -> void:
	for c in get_children():
		c.queue_free()
	ow = Overworld.new()
	add_child(ow)


func run_battle(cfg: Dictionary) -> String:
	# 배틀 진입 연출: 화면 깜빡임
	for i in 3:
		await UI.fade_out(0.06, Color.WHITE)
		await UI.fade_in(0.06)
	await UI.fade_out(0.2)
	ow.visible = false
	ow.process_mode = Node.PROCESS_MODE_DISABLED
	var b := Battle.new()
	add_child(b)
	b.start(cfg)
	await UI.fade_in(0.2)
	var res: String = await b.finished
	await UI.fade_out(0.2)
	b.queue_free()
	ow.visible = true
	ow.process_mode = Node.PROCESS_MODE_INHERIT
	await UI.fade_in(0.2)
	return res
