class_name Multi
extends RefCounted
## 친구와의 상호작용: 대전/교환 신청, 통신 메뉴.


static func net_menu(_ow: Overworld) -> void:
	while true:
		var status := "오프라인 (혼자 플레이)"
		if Net.online():
			var names := []
			for id in Net.peers:
				names.append(Net.peers[id].get("name", "?"))
			status = ("호스트" if Net.multiplayer.is_server() else "참가 중") + " / 접속: " + (", ".join(names) if names else "없음")
		UI.say(status, true, false)
		var opts := ["방 만들기", "참가하기", "채팅", "연결 끊기", "닫기"] if not Net.online() else ["채팅", "내 IP 보기", "연결 끊기", "닫기"]
		var c: int = await UI.choose(opts, Rect2(80, 0, 80, opts.size() * 14 + 10))
		if c < 0:
			break
		match opts[c]:
			"방 만들기":
				if Net.host() == OK:
					await UI.say("방을 만들었다! (포트 %d)\f친구에게 이 IP를 알려줘:\n%s" % [Net.PORT, ", ".join(Net.local_ips())], true)
				else:
					await UI.say("방을 만들 수 없었다...\n(포트가 사용 중일 수 있음)", true)
			"참가하기":
				var ip := await UI.text_input("호스트 IP 주소:", "127.0.0.1", 40)
				if ip != "":
					await join_flow(ip)
			"채팅":
				var t := await UI.text_input("보낼 메시지:", "", 40)
				if t != "":
					Net.send_chat(t)
					UI.toast("나: " + t, 2.0)
			"내 IP 보기":
				await UI.say("내 IP: %s\n포트: %d" % [", ".join(Net.local_ips()), Net.PORT], true)
			"연결 끊기":
				Net.leave()
				await UI.say("연결을 끊었다.", true)
			_:
				break
	UI.close_box()


static func join_flow(ip: String) -> bool:
	if Net.join(ip) != OK:
		await UI.say("접속할 수 없었다...", true)
		return false
	UI.say("접속 중...", true, false)
	var t := 0.0
	while t < 8.0:
		await UI.wait(0.1)
		t += 0.1
		if Net.online():
			await UI.say("접속했다!", true)
			return true
	Net.leave()
	await UI.say("접속에 실패했다...\nIP와 방화벽을 확인해 줘.", true)
	return false


## 친구에게 말 걸기 → 대전/교환 신청
static func interact_player(ow: Overworld, id: int) -> void:
	var p: Dictionary = Net.peers.get(id, {})
	var pname: String = p.get("name", "?")
	UI.say("%s{와} 무엇을 할까?" % pname, true, false)
	var c: int = await UI.choose(["대전", "교환", "그만두기"], Rect2(88, 44, 72, 52))
	if c < 0 or c == 2:
		UI.close_box()
		return
	var kind := "battle" if c == 0 else "trade"
	if G.first_alive() < 0 and kind == "battle":
		await UI.say("싸울 수 있는 포켓몬이 없다!")
		return
	if G.party.is_empty():
		await UI.say("포켓몬이 없다!")
		return
	Net.send_request(id, kind)
	UI.say("%s의 대답을 기다리는 중..." % pname, true, false)
	var answer := [null]
	var cb := func(from, k, acc):
		if from == id and k == kind:
			answer[0] = acc
	Net.response_received.connect(cb)
	var t := 0.0
	while answer[0] == null and t < 30.0 and Net.peers.has(id):
		await UI.wait(0.1)
		t += 0.1
	Net.response_received.disconnect(cb)
	if answer[0] != true:
		await UI.say("%s{은} 거절했다..." % pname if answer[0] == false else "대답이 없다...")
		return
	UI.close_box()
	await start_session(ow, id, kind)


static func handle_request(ow: Overworld, id: int, kind: String) -> void:
	var pname: String = Net.peers.get(id, {}).get("name", "?")
	var kname := "대전" if kind == "battle" else "교환"
	if Net.busy_with != 0 or G.party.is_empty() or (kind == "battle" and G.first_alive() < 0):
		Net.send_response(id, kind, false)
		return
	await UI.say("%s{이} %s{을} 신청했다!\n받을까?" % [pname, kname], true, false)
	var ok: bool = await UI.yes_no()
	UI.close_box()
	Net.send_response(id, kind, ok)
	if ok:
		await start_session(ow, id, kind)


## 양쪽이 파티를 교환한 뒤 대전/교환 시작
static func start_session(ow: Overworld, id: int, kind: String) -> void:
	Net.busy_with = id
	if kind == "battle":
		Net.send_pvp(id, {"type": "hello", "party": G.party, "name": G.player_name})
	else:
		Net.send_trade(id, {"type": "hello", "party": G.party, "name": G.player_name})
	var hello := {}
	var t := 0.0
	while t < 15.0 and Net.peers.has(id):
		if Net.hellos.has(id):
			hello = Net.hellos[id]
			Net.hellos.erase(id)
			break
		await UI.wait(0.05)
		t += 0.05
	if hello.is_empty():
		Net.busy_with = 0
		await UI.say("통신에 실패했다...")
		return
	if kind == "battle":
		var mine: Array = G.party.duplicate(true)
		var theirs: Array = hello.party
		for m in mine:
			Mon.heal(m)
		for m in theirs:
			Mon.heal(m)
		var res: String = await Main.inst.run_battle({
			"kind": "pvp", "peer": id, "authority": Net.my_id() < id,
			"mine": mine, "theirs": theirs, "their_name": hello.name,
		})
		await UI.say("통신 대전 결과: %s!" % {"win": "승리", "lose": "패배"}.get(res, "무효"))
	else:
		await trade(ow, id, hello)
	Net.busy_with = 0


static func trade(ow: Overworld, id: int, hello: Dictionary) -> void:
	var theirs: Array = hello.party
	var inbox := []
	var cb := func(from, m):
		if from == id:
			inbox.append(m)
	Net.trade_message.connect(cb)
	var names := []
	for m in theirs:
		names.append("%s Lv%d" % [Mon.name_of(m), m.level])
	await UI.say("%s의 포켓몬:\n%s" % [hello.name, ", ".join(names)], true)
	await UI.say("교환할 내 포켓몬을 골라 줘.", true, false)
	var mine: int = await Menus.party_menu("select", -1)
	var my_choice := mine
	Net.send_trade(id, {"type": "pick", "idx": my_choice})
	UI.say("상대가 고르는 중...", true, false)
	var their_pick := -2
	while their_pick == -2:
		for m in inbox:
			if m.type == "pick":
				their_pick = m.idx
			elif m.type == "disconnect":
				their_pick = -1
		await UI.wait(0.05)
	if my_choice < 0 or their_pick < 0:
		Net.trade_message.disconnect(cb)
		await UI.say("교환을 취소했다.")
		return
	var give: Dictionary = G.party[my_choice]
	var get_mon: Dictionary = theirs[their_pick]
	await UI.say("%s{을} 주고\n%s{을} 받을까?" % [Mon.name_of(give), Mon.name_of(get_mon)], true, false)
	var ok: bool = await UI.yes_no()
	Net.send_trade(id, {"type": "confirm", "ok": ok})
	UI.say("상대의 확인을 기다리는 중...", true, false)
	var their_ok = null
	while their_ok == null:
		for m in inbox:
			if m.type == "confirm":
				their_ok = m.ok
			elif m.type == "disconnect":
				their_ok = false
		await UI.wait(0.05)
	Net.trade_message.disconnect(cb)
	if not (ok and their_ok):
		await UI.say("교환을 취소했다.")
		return
	var received: Dictionary = G.fix_ints(get_mon.duplicate(true))
	G.party[my_choice] = received
	G.register_caught(received.species)
	await UI.say("%s{을} 보냈다!\f%s{이} 왔다!\f%s{을} 소중히 대해 줘!" % [Mon.name_of(give), Mon.name_of(received), Mon.name_of(received)], true)
	var evo := Mon.trade_evolution(received)
	if evo != "":
		await Battle.evolve_scene(UI, received, evo)
	UI.close_box()
	G.save_game()
