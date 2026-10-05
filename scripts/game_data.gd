class_name GameData
extends RefCounted
## Unit definitions and shared constants for World Conquest.

const MAP_W := 40
const MAP_H := 40
const TILE_W := 64
const TILE_H := 32

enum Terrain { OCEAN, GRASS, PLAINS, FOREST, HILLS }
enum Owner { NEUTRAL, PLAYER, AI }
enum UnitType { ARMY, FIGHTER, DESTROYER, SUBMARINE, TRANSPORT, CARRIER, BATTLESHIP }

const UNIT_DEFS := {
	UnitType.ARMY: {
		"id": "army", "name_zh": "陸軍", "domain": "land",
		"cost": 5, "move": 1, "attack": 4, "defense": 4, "hp": 1,
		"los": 1, "fuel": 0, "capacity": 0, "cargo_of": "transport",
	},
	UnitType.FIGHTER: {
		"id": "fighter", "name_zh": "戰鬥機", "domain": "air",
		"cost": 6, "move": 8, "attack": 5, "defense": 3, "hp": 1,
		"los": 2, "fuel": 20, "capacity": 0, "cargo_of": "carrier",
	},
	UnitType.DESTROYER: {
		"id": "destroyer", "name_zh": "驅逐艦", "domain": "sea",
		"cost": 8, "move": 4, "attack": 5, "defense": 4, "hp": 2,
		"los": 1, "fuel": 0, "capacity": 0, "cargo_of": "",
	},
	UnitType.SUBMARINE: {
		"id": "submarine", "name_zh": "潛艦", "domain": "sea",
		"cost": 10, "move": 3, "attack": 7, "defense": 2, "hp": 1,
		"los": 1, "fuel": 0, "capacity": 0, "cargo_of": "",
	},
	UnitType.TRANSPORT: {
		"id": "transport", "name_zh": "運輸艦", "domain": "sea",
		"cost": 12, "move": 3, "attack": 0, "defense": 2, "hp": 2,
		"los": 1, "fuel": 0, "capacity": 4, "cargo_of": "",
	},
	UnitType.CARRIER: {
		"id": "carrier", "name_zh": "航空母艦", "domain": "sea",
		"cost": 15, "move": 3, "attack": 2, "defense": 4, "hp": 3,
		"los": 1, "fuel": 0, "capacity": 4, "cargo_of": "",
	},
	UnitType.BATTLESHIP: {
		"id": "battleship", "name_zh": "戰艦", "domain": "sea",
		"cost": 20, "move": 2, "attack": 8, "defense": 7, "hp": 4,
		"los": 1, "fuel": 0, "capacity": 0, "cargo_of": "",
	},
}

const DIRS8 := [
	Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
	Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1),
]

static func is_land(t: int) -> bool:
	return t != Terrain.OCEAN

static func unit_name(t: int) -> String:
	return UNIT_DEFS[t]["name_zh"]

static func grid_to_iso(g: Vector2i) -> Vector2:
	var x := (g.x - g.y) * (TILE_W / 2.0)
	var y := (g.x + g.y) * (TILE_H / 2.0)
	return Vector2(x, y)

static func iso_to_grid(p: Vector2) -> Vector2i:
	var gx := (p.x / (TILE_W / 2.0) + p.y / (TILE_H / 2.0)) / 2.0
	var gy := (p.y / (TILE_H / 2.0) - p.x / (TILE_W / 2.0)) / 2.0
	return Vector2i(roundi(gx), roundi(gy))
