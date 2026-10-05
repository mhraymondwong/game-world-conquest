class_name WCUnit
extends RefCounted
## Combat / cargo unit instance.

var id: int = 0
var type: int = GameData.UnitType.ARMY
var owner: int = GameData.Owner.PLAYER
var pos: Vector2i = Vector2i.ZERO
var hp: int = 1
var moves_left: int = 0
var fuel: int = 0
var cargo: Array = []  # unit ids aboard
var aboard: int = -1   # carrier/transport id if embarked
var alive: bool = true

func _init(p_id: int = 0, p_type: int = 0, p_owner: int = 0, p_pos: Vector2i = Vector2i.ZERO) -> void:
	id = p_id
	type = p_type
	owner = p_owner
	pos = p_pos
	var def: Dictionary = GameData.UNIT_DEFS[type]
	hp = def["hp"]
	moves_left = def["move"]
	fuel = def["fuel"]

func def() -> Dictionary:
	return GameData.UNIT_DEFS[type]

func domain() -> String:
	return def()["domain"]

func reset_moves() -> void:
	moves_left = def()["move"]

func can_capture() -> bool:
	return type == GameData.UnitType.ARMY

func is_sub() -> bool:
	return type == GameData.UnitType.SUBMARINE

func is_destroyer() -> bool:
	return type == GameData.UnitType.DESTROYER

func capacity() -> int:
	return def()["capacity"]

func can_carry(other: WCUnit) -> bool:
	if capacity() <= 0 or cargo.size() >= capacity():
		return false
	if type == GameData.UnitType.TRANSPORT:
		return other.type == GameData.UnitType.ARMY
	if type == GameData.UnitType.CARRIER:
		return other.type == GameData.UnitType.FIGHTER
	return false
