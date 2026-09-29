class_name Gyms
extends RefCounted
## 체육관 관장 8명 공통 처리: 대결 → 배지 → 기술머신, 관장 격파 후 체육관 트레이너 비활성화, 가이드/석상.

const GYMS := {
	"PEWTERGYM_BROCK": {
		"map": "PEWTER_GYM", "class": "BROCK", "index": 1, "badge": "BOULDERBADGE", "tm": "TM_BIDE",
		"pre": "_PewterGymBrockPreBattleText", "win": "_PewterGymBrockReceivedBoulderBadgeText",
		"info": "_PewterGymBrockBoulderBadgeInfoText", "tm_text": "_PewterGymReceivedTM34Text",
		"after": "_PewterGymBrockPostBattleAdviceText", "wait": "_PewterGymBrockWaitTakeThisText",
		"city": "회색시티", "leader": "웅",
	},
	"CERULEANGYM_MISTY": {
		"map": "CERULEAN_GYM", "class": "MISTY", "index": 1, "badge": "CASCADEBADGE", "tm": "TM_BUBBLEBEAM",
		"pre": "_CeruleanGymMistyPreBattleText", "win": "_CeruleanGymMistyReceivedCascadeBadgeText",
		"info": "_CeruleanGymMistyCascadeBadgeInfoText", "tm_text": "_CeruleanGymMistyReceivedTM11Text",
		"after": "_CeruleanGymMistyTM11ExplanationText", "city": "블루시티", "leader": "이슬",
	},
	"VERMILIONGYM_LT_SURGE": {
		"map": "VERMILION_GYM", "class": "LT_SURGE", "index": 1, "badge": "THUNDERBADGE", "tm": "TM_THUNDERBOLT",
		"pre": "_VermilionGymLTSurgePreBattleText", "win": "_VermilionGymLTSurgeReceivedThunderBadgeText",
		"info": "_VermilionGymLTSurgeThunderBadgeInfoText", "tm_text": "_VermilionGymLTSurgeReceivedTM24Text",
		"after": "_VermilionGymLTSurgePostBattleAdviceText", "city": "갈색시티", "leader": "마티스",
	},
	"CELADONGYM_ERIKA": {
		"map": "CELADON_GYM", "class": "ERIKA", "index": 1, "badge": "RAINBOWBADGE", "tm": "TM_MEGA_DRAIN",
		"pre": "_CeladonGymErikaPreBattleText", "win": "_CeladonGymErikaReceivedRainbowBadgeText",
		"info": "_CeladonGymRainbowBadgeInfoText", "tm_text": "_CeladonGymReceivedTM21Text",
		"after": "_CeladonGymErikaPostBattleAdviceText", "city": "무지개시티", "leader": "민화",
	},
	"FUCHSIAGYM_KOGA": {
		"map": "FUCHSIA_GYM", "class": "KOGA", "index": 1, "badge": "SOULBADGE", "tm": "TM_TOXIC",
		"pre": "_FuchsiaGymKogaBeforeBattleText", "win": "_FuchsiaGymKogaReceivedSoulBadgeText",
		"info": "_FuchsiaGymKogaSoulBadgeInfoText", "tm_text": "_FuchsiaGymKogaReceivedTM06Text",
		"after": "_FuchsiaGymKogaTM06ExplanationText", "city": "연분홍시티", "leader": "독수",
	},
	"SAFFRONGYM_SABRINA": {
		"map": "SAFFRON_GYM", "class": "SABRINA", "index": 1, "badge": "MARSHBADGE", "tm": "TM_PSYWAVE",
		"pre": "_SaffronGymSabrinaText", "win": "_SaffronGymSabrinaReceivedMarshBadgeText",
		"info": "_SaffronGymSabrinaMarshBadgeInfoText", "tm_text": "_SaffronGymSabrinaReceivedTM46Text",
		"after": "_SaffronGymSabrinaPostBattleAdviceText", "city": "노랑시티", "leader": "초련",
	},
	"CINNABARGYM_BLAINE": {
		"map": "CINNABAR_GYM", "class": "BLAINE", "index": 1, "badge": "VOLCANOBADGE", "tm": "TM_FIRE_BLAST",
		"pre": "_CinnabarGymBlainePreBattleText", "win": "_CinnabarGymBlaineReceivedVolcanoBadgeText",
		"info": "_CinnabarGymBlaineVolcanoBadgeInfoText", "tm_text": "_CinnabarGymBlaineReceivedTM38Text",
		"after": "_CinnabarGymBlaineTM38ExplanationText", "city": "홍련마을", "leader": "강연",
	},
	"VIRIDIANGYM_GIOVANNI": {
		"map": "VIRIDIAN_GYM", "class": "GIOVANNI", "index": 3, "badge": "EARTHBADGE", "tm": "TM_FISSURE",
		"pre": "_ViridianGymGiovanniPreBattleText", "win": "_ViridianGymGiovanniReceivedEarthBadgeText",
		"info": "_ViridianGymGiovanniEarthBadgeInfoText", "tm_text": "_ViridianGymGiovanniReceivedTM27Text",
		"after": "_ViridianGymGiovanniTM27ExplanationText", "city": "상록시티", "leader": "비주기",
	},
}


static func on_talk(ow: Overworld, a: Actor) -> bool:
	var id: String = a.data.get("id", "")
	if GYMS.has(id):
		await leader(ow, a, GYMS[id])
		return true
	if id.ends_with("GYM_GUIDE") or id.ends_with("_GUIDE"):
		for k in GYMS:
			var g: Dictionary = GYMS[k]
			if g.map == ow.map_id and G.bag.has(g.badge):
				var lab := _guide_beat_label(ow.map.name)
				if lab != "":
					await Story.say(lab)
					return true
	return false


static func _guide_beat_label(map_name: String) -> String:
	for k in DB.texts_en:
		var s: String = k
		if s.begins_with("_" + map_name) and s.contains("Guide") and s.contains("Beat"):
			return s
	return ""


static func leader(ow: Overworld, a: Actor, g: Dictionary) -> void:
	if G.bag.has(g.badge):
		if not G.flag("got:" + g.tm):
			await _give_tm(ow, g)
			return
		await Story.say(g.after)
		if g.class == "GIOVANNI":
			await _giovanni_leaves(ow, a)
		return
	await Story.say(g.pre)
	var res: String = await Story.battle(ow, g.class, g.index, g.win, "", {"no_blackout": false})
	if res != "win":
		return
	Sound.jingle("Get_Key_Item")
	G.add_item(g.badge)
	Story.beat_map_trainers(ow)
	G.set_flag("beat_" + g.class)
	await Story.say(g.info)
	await _give_tm(ow, g)


static func _give_tm(ow: Overworld, g: Dictionary) -> void:
	if g.has("wait"):
		await Story.say(g.wait)
	G.add_item(g.tm)
	G.set_flag("got:" + g.tm)
	Sound.jingle("Get_Item1")
	await UI.say(Story.fill(g.tm_text, [DB.item_name(g.tm)]))


## 비주기는 배지를 준 뒤 사라짐
static func _giovanni_leaves(ow: Overworld, a: Actor) -> void:
	await UI.fade_out(0.4)
	ow.remove_npc(a.data.id)
	await UI.fade_in(0.4)


static func statue(ow: Overworld) -> void:
	for k in GYMS:
		var g: Dictionary = GYMS[k]
		if g.map == ow.map_id:
			var winners := "{RIVAL}" + (", {PLAYER}" if G.bag.has(g.badge) else "")
			await UI.say("%s 포켓몬 체육관\n관장: %s\f승리한 트레이너:\n%s" % [g.city, g.leader, winners])
			return
	await UI.say("포켓몬 체육관")
