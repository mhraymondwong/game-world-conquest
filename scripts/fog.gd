class_name FogSystem
extends RefCounted
## Fog of war: 0=unexplored(black), 1=explored, 2=visible.

var w: int
var h: int
var player_fog: PackedByteArray
var ai_fog: PackedByteArray

func _init(p_w: int = GameData.MAP_W, p_h: int = GameData.MAP_H) -> void:
	w = p_w
	h = p_h
	player_fog = PackedByteArray()
	player_fog.resize(w * h)
	ai_fog = PackedByteArray()
	ai_fog.resize(w * h)
	for i in w * h:
		player_fog[i] = 0
		ai_fog[i] = 0

func get_fog(owner: int) -> PackedByteArray:
	return player_fog if owner == GameData.Owner.PLAYER else ai_fog

func visible(owner: int, x: int, y: int) -> bool:
	return get_fog(owner)[y * w + x] >= 2

func explored(owner: int, x: int, y: int) -> bool:
	return get_fog(owner)[y * w + x] >= 1

func recompute(owner: int, units: Array, cities: Array) -> void:
	var fog := get_fog(owner)
	# demote visible → explored
	for i in fog.size():
		if fog[i] >= 2:
			fog[i] = 1
	for u in units:
		if not u.alive or u.owner != owner or u.aboard >= 0:
			continue
		var los: int = u.def()["los"]
		_reveal(fog, u.pos, los)
	for c in cities:
		if c.owner == owner:
			_reveal(fog, c.pos, 1)

func _reveal(fog: PackedByteArray, center: Vector2i, radius: int) -> void:
	for dy in range(-radius, radius + 1):
		for dx in range(-radius, radius + 1):
			# Chebyshev for 3x3 when radius=1; radius=2 → 5x5
			if maxi(absi(dx), absi(dy)) > radius:
				continue
			var x := center.x + dx
			var y := center.y + dy
			if x < 0 or y < 0 or x >= w or y >= h:
				continue
			fog[y * w + x] = 2
