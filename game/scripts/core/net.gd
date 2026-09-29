extends Node
## 멀티플레이 (ENet). 한 명이 호스트, 친구가 IP로 접속.
## 각자 자기 진행(세이브)을 갖고, 같은 월드에서 서로의 위치를 보며 대전/교환한다.

signal peers_changed
signal peer_state(id: int)
signal request_received(from_id: int, kind: String)
signal response_received(from_id: int, kind: String, accepted: bool)
signal pvp_message(from_id: int, msg: Dictionary)
signal trade_message(from_id: int, msg: Dictionary)
signal chat_received(from_id: int, text: String)
signal connection_failed
signal connected

const PORT := 24680

var peers := {}  # id -> {name, sprite, map, x, y, fx, fy}
var busy_with := 0  # 대전/교환 중인 상대 id
var hellos := {}  # 상대 id -> 세션 시작 메시지(파티) — 신호 연결 전에 도착해도 잃지 않도록 보관


func _ready() -> void:
	multiplayer.peer_connected.connect(_on_peer_connected)
	multiplayer.peer_disconnected.connect(_on_peer_disconnected)
	multiplayer.connected_to_server.connect(func(): connected.emit(); _announce_all())
	multiplayer.connection_failed.connect(func(): connection_failed.emit())
	multiplayer.server_disconnected.connect(_on_server_gone)


func online() -> bool:
	return multiplayer.multiplayer_peer != null \
		and not (multiplayer.multiplayer_peer is OfflineMultiplayerPeer) \
		and multiplayer.multiplayer_peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED


func my_id() -> int:
	return multiplayer.get_unique_id() if online() else 1


func host(port := PORT) -> Error:
	var p := ENetMultiplayerPeer.new()
	var err := p.create_server(port, 4)
	if err == OK:
		multiplayer.multiplayer_peer = p
	return err


func join(ip: String, port := PORT) -> Error:
	var p := ENetMultiplayerPeer.new()
	var err := p.create_client(ip, port)
	if err == OK:
		multiplayer.multiplayer_peer = p
	return err


func leave() -> void:
	if multiplayer.multiplayer_peer:
		multiplayer.multiplayer_peer.close()
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	peers.clear()
	peers_changed.emit()


func local_ips() -> Array:
	var out := []
	for ip in IP.get_local_addresses():
		if ip.count(".") == 3 and not ip.begins_with("127.") and not ip.begins_with("169.254"):
			out.append(ip)
	return out


func _on_peer_connected(_id: int) -> void:
	_announce_all()


func _on_peer_disconnected(id: int) -> void:
	peers.erase(id)
	if busy_with == id:
		busy_with = 0
		pvp_message.emit(id, {"type": "disconnect"})
		trade_message.emit(id, {"type": "disconnect"})
	peers_changed.emit()


func _on_server_gone() -> void:
	peers.clear()
	multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	peers_changed.emit()
	UI.toast("호스트와 연결이 끊어졌다.")


func _announce_all() -> void:
	if online():
		_rpc_info.rpc(G.player_name, G.sprite)
		send_state(false)


# ------------------------------------------------------------------ 위치 동기화
func send_state(moving := true) -> void:
	if not online():
		return
	_rpc_state.rpc(G.map, G.pos.x, G.pos.y, G.facing.x, G.facing.y, moving, G.field_sprite())


@rpc("any_peer", "reliable")
func _rpc_info(pname: String, spr: String) -> void:
	var id := multiplayer.get_remote_sender_id()
	var known := peers.has(id)
	var p: Dictionary = peers.get(id, {"map": "", "x": 0, "y": 0, "fx": 0, "fy": 1})
	p.name = pname
	p.sprite = spr
	peers[id] = p
	peers_changed.emit()
	if not known:
		# 새로 알게 된 상대에게 내 정보도 알려줌
		_rpc_info.rpc_id(id, G.player_name, G.sprite)
		_rpc_state.rpc_id(id, G.map, G.pos.x, G.pos.y, G.facing.x, G.facing.y, false, G.field_sprite())
		UI.toast("%s 님이 접속했다!" % pname)


@rpc("any_peer", "unreliable_ordered")
func _rpc_state(m: String, x: int, y: int, fx: int, fy: int, moving: bool, spr := "") -> void:
	var id := multiplayer.get_remote_sender_id()
	if not peers.has(id):
		peers[id] = {"name": "?", "sprite": "red"}
	var p: Dictionary = peers[id]
	p.map = m
	p.x = x
	p.y = y
	p.fx = fx
	p.fy = fy
	p.moving = moving
	if spr != "":
		p.sprite = spr
	peer_state.emit(id)


# ------------------------------------------------------------------ 요청/응답
func send_request(to: int, kind: String) -> void:
	_rpc_request.rpc_id(to, kind)


func send_response(to: int, kind: String, accepted: bool) -> void:
	_rpc_response.rpc_id(to, kind, accepted)


@rpc("any_peer", "reliable")
func _rpc_request(kind: String) -> void:
	request_received.emit(multiplayer.get_remote_sender_id(), kind)


@rpc("any_peer", "reliable")
func _rpc_response(kind: String, accepted: bool) -> void:
	response_received.emit(multiplayer.get_remote_sender_id(), kind, accepted)


func send_pvp(to: int, msg: Dictionary) -> void:
	_rpc_pvp.rpc_id(to, msg)


@rpc("any_peer", "reliable")
func _rpc_pvp(msg: Dictionary) -> void:
	if msg.get("type", "") == "hello":
		hellos[multiplayer.get_remote_sender_id()] = G.fix_ints(msg)
		return
	pvp_message.emit(multiplayer.get_remote_sender_id(), G.fix_ints(msg))


func send_trade(to: int, msg: Dictionary) -> void:
	_rpc_trade.rpc_id(to, msg)


@rpc("any_peer", "reliable")
func _rpc_trade(msg: Dictionary) -> void:
	if msg.get("type", "") == "hello":
		hellos[multiplayer.get_remote_sender_id()] = G.fix_ints(msg)
		return
	trade_message.emit(multiplayer.get_remote_sender_id(), G.fix_ints(msg))


func send_chat(text: String) -> void:
	if online():
		_rpc_chat.rpc(text)


@rpc("any_peer", "reliable")
func _rpc_chat(text: String) -> void:
	chat_received.emit(multiplayer.get_remote_sender_id(), text)
