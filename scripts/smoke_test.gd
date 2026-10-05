extends SceneTree
## Headless smoke — must exit quickly.
## godot --headless --path . --script res://scripts/smoke_test.gd

var _ok := true
var _msg: Array[String] = []

func _init() -> void:
	call_deferred("_run_tests")

func _run_tests() -> void:
	_check_map()
	_check_combat()
	_check_capture_prod()
	_check_units_bombard()
	for m in _msg:
		print("[smoke] ", m)
	if _ok:
		print("[smoke] ALL PASSED")
		quit(0)
	else:
		print("[smoke] FAILED")
		quit(1)

func _fail(s: String) -> void:
	_ok = false
	_msg.append(s)

func _check_map() -> void:
	var map: Dictionary = MapGen.generate(12345)
	if map.terrain.size() != GameData.MAP_W * GameData.MAP_H:
		_fail("map size fail")
	else:
		_msg.append("map gen ok")
	var land := 0
	for t in map.terrain:
		if GameData.is_land(t):
			land += 1
	if land < 20:
		_fail("too little land: %d" % land)
	else:
		_msg.append("land tiles=%d cities=%d" % [land, map.cities.size()])

func _check_combat() -> void:
	var a := WCUnit.new(1, GameData.UnitType.ARMY, GameData.Owner.PLAYER, Vector2i(1, 1))
	var b := WCUnit.new(2, GameData.UnitType.ARMY, GameData.Owner.AI, Vector2i(1, 2))
	var rng := RandomNumberGenerator.new()
	rng.seed = 99
	var result: Dictionary = Combat.fight(a, b, rng)
	if not result.has("winner"):
		_fail("combat fail")
	else:
		_msg.append("combat winner=%s" % GameData.unit_name(result.winner.type))

func _check_capture_prod() -> void:
	var city := {"pos": Vector2i(5, 5), "owner": GameData.Owner.NEUTRAL, "building": -1, "progress": 0}
	var army := WCUnit.new(3, GameData.UnitType.ARMY, GameData.Owner.PLAYER, Vector2i(5, 5))
	if army.can_capture() and city.owner == GameData.Owner.NEUTRAL:
		city.owner = army.owner
		city.progress = 0
		city.building = -1
		_msg.append("capture ok owner=%d" % city.owner)
	else:
		_fail("capture fail")
	city.owner = GameData.Owner.PLAYER
	city.building = GameData.UnitType.ARMY
	city.progress = 4
	var spawn: Dictionary = Production.tick_city(city, false)
	if spawn.get("spawn_type", -1) != GameData.UnitType.ARMY:
		_fail("production fail prog=%d" % city.progress)
	else:
		_msg.append("production spawn army ok")
	army.moves_left = 1
	army.pos = Vector2i(1, 1)
	army.moves_left -= 1
	if army.moves_left != 0:
		_fail("move fail")
	else:
		_msg.append("diagonal move cost 1 ok")

func _check_units_bombard() -> void:
	for t in GameData.UNIT_DEFS.keys():
		var u := WCUnit.new(10 + int(t), t, GameData.Owner.PLAYER, Vector2i(2, 2))
		if str(u.def().get("id", "")) == "":
			_fail("unit def fail %s" % t)
	_msg.append("7 unit types ok")
	var bb := WCUnit.new(20, GameData.UnitType.BATTLESHIP, GameData.Owner.PLAYER, Vector2i(0, 0))
	var land_army := WCUnit.new(21, GameData.UnitType.ARMY, GameData.Owner.AI, Vector2i(1, 0))
	if not Combat.can_bombard(bb, land_army):
		_fail("bombard rule fail")
	else:
		_msg.append("coastal bombard ok")
