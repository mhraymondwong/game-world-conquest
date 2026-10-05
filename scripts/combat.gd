class_name Combat
extends RefCounted
## Attack/defense RNG combat until one side dies. Coastal bombard for capital ships.

static func fight(attacker: WCUnit, defender: WCUnit, rng: RandomNumberGenerator) -> Dictionary:
	var a_atk: int = int(attacker.def()["attack"])
	var d_def: int = int(defender.def()["defense"])
	a_atk = int(a_atk * _mod(attacker, defender))
	d_def = int(d_def * _mod(defender, attacker) * 0.5 + d_def * 0.5)

	var lines: Array[String] = []
	var guard := 40
	while attacker.alive and defender.alive and attacker.hp > 0 and defender.hp > 0 and guard > 0:
		guard -= 1
		if a_atk > 0:
			var roll := rng.randi_range(1, 10)
			if roll <= a_atk:
				defender.hp -= 1
				lines.append("%s 命中 %s" % [GameData.unit_name(attacker.type), GameData.unit_name(defender.type)])
				if defender.hp <= 0:
					defender.alive = false
					break
		if d_def > 0 and defender.alive:
			var roll2 := rng.randi_range(1, 10)
			if roll2 <= d_def:
				attacker.hp -= 1
				lines.append("%s 反擊 %s" % [GameData.unit_name(defender.type), GameData.unit_name(attacker.type)])
				if attacker.hp <= 0:
					attacker.alive = false
					break
		if a_atk <= 0 and d_def <= 0:
			defender.alive = false
			defender.hp = 0
			break

	var winner: WCUnit = attacker if attacker.alive else defender
	var loser: WCUnit = defender if attacker.alive else attacker
	return {"winner": winner, "loser": loser, "log": lines}

static func fight_bombard(attacker: WCUnit, defender: WCUnit, rng: RandomNumberGenerator) -> Dictionary:
	## One-way coastal shot: attacker does not take counter from land (naval gunfire).
	var a_atk := maxi(1, int(attacker.def()["attack"] * 0.85))
	var lines: Array[String] = []
	var hp_before: int = defender.hp
	var roll := rng.randi_range(1, 10)
	if roll <= a_atk:
		defender.hp -= 1
		lines.append("%s 岸轟命中 %s" % [GameData.unit_name(attacker.type), GameData.unit_name(defender.type)])
		if defender.hp <= 0:
			defender.alive = false
	else:
		lines.append("%s 岸轟未中" % GameData.unit_name(attacker.type))
	var loser: WCUnit = defender if not defender.alive else null
	return {"winner": attacker, "loser": loser, "log": lines, "hit": defender.hp < hp_before}

static func _mod(a: WCUnit, b: WCUnit) -> float:
	if a.type == GameData.UnitType.SUBMARINE and b.type == GameData.UnitType.BATTLESHIP:
		return 1.8
	if a.type == GameData.UnitType.DESTROYER and b.type == GameData.UnitType.SUBMARINE:
		return 1.7
	if a.type == GameData.UnitType.BATTLESHIP and b.domain() == "sea" and b.type != GameData.UnitType.SUBMARINE:
		return 1.3
	if a.type == GameData.UnitType.FIGHTER and b.domain() == "sea":
		return 1.2
	if a.type == GameData.UnitType.ARMY and b.domain() == "sea":
		return 0.35
	if a.type == GameData.UnitType.TRANSPORT:
		return 0.0
	return 1.0

static func can_attack(attacker: WCUnit, defender: WCUnit) -> bool:
	if not attacker.alive or not defender.alive:
		return false
	if attacker.owner == defender.owner:
		return false
	if attacker.type == GameData.UnitType.TRANSPORT:
		return false
	if attacker.type == GameData.UnitType.ARMY and defender.domain() == "sea":
		return false
	return true

static func can_bombard(attacker: WCUnit, defender: WCUnit) -> bool:
	## Battleship (and destroyer light) may shell adjacent land units from ocean.
	if not can_attack(attacker, defender):
		return false
	if attacker.domain() != "sea":
		return false
	if defender.domain() == "sea":
		return false
	if attacker.type != GameData.UnitType.BATTLESHIP and attacker.type != GameData.UnitType.DESTROYER:
		return false
	return true
