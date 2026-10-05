class_name MapGen
extends RefCounted
## Random archipelago map generator (square grid, land + ocean + cities).

const W := GameData.MAP_W
const H := GameData.MAP_H

static func generate(seed_val: int = 0) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	if seed_val == 0:
		rng.randomize()
	else:
		rng.seed = seed_val

	var terrain: Array = []
	terrain.resize(W * H)
	for i in W * H:
		terrain[i] = GameData.Terrain.OCEAN

	# Seed several island blobs
	var island_count := rng.randi_range(7, 11)
	var centers: Array[Vector2i] = []
	for _i in island_count:
		var c := Vector2i(rng.randi_range(3, W - 4), rng.randi_range(3, H - 4))
		centers.append(c)
		var radius := rng.randi_range(3, 7)
		for y in range(maxi(0, c.y - radius), mini(H, c.y + radius + 1)):
			for x in range(maxi(0, c.x - radius), mini(W, c.x + radius + 1)):
				var d := Vector2(x - c.x, y - c.y).length()
				if d <= radius * (0.55 + rng.randf() * 0.55):
					var roll := rng.randf()
					if roll < 0.55:
						terrain[_idx(x, y)] = GameData.Terrain.GRASS
					elif roll < 0.75:
						terrain[_idx(x, y)] = GameData.Terrain.PLAINS
					elif roll < 0.90:
						terrain[_idx(x, y)] = GameData.Terrain.FOREST
					else:
						terrain[_idx(x, y)] = GameData.Terrain.HILLS

	# Smooth once
	for _pass in 2:
		var next := terrain.duplicate()
		for y in H:
			for x in W:
				var land_n := 0
				for d in GameData.DIRS8:
					var nx: int = x + d.x
					var ny: int = y + d.y
					if nx >= 0 and ny >= 0 and nx < W and ny < H and GameData.is_land(terrain[_idx(nx, ny)]):
						land_n += 1
				var i := _idx(x, y)
				if GameData.is_land(terrain[i]):
					if land_n < 2:
						next[i] = GameData.Terrain.OCEAN
				else:
					if land_n >= 5:
						next[i] = GameData.Terrain.GRASS
		terrain = next

	# Place cities on land, spaced out
	var cities: Array = []  # {pos, owner}
	var land_tiles: Array[Vector2i] = []
	for y in H:
		for x in W:
			if GameData.is_land(terrain[_idx(x, y)]):
				land_tiles.append(Vector2i(x, y))
	land_tiles.shuffle()
	var target_cities := mini(18, land_tiles.size() / 12)
	for p in land_tiles:
		if cities.size() >= target_cities:
			break
		var ok := true
		for c in cities:
			if Vector2(c.pos).distance_to(Vector2(p)) < 4.0:
				ok = false
				break
		if ok:
			cities.append({"pos": p, "owner": GameData.Owner.NEUTRAL, "prod": 0, "building": -1, "progress": 0})

	# Assign player & AI starting cities far apart
	if cities.size() >= 2:
		var best_a := 0
		var best_b := 1
		var best_d := -1.0
		for i in cities.size():
			for j in range(i + 1, cities.size()):
				var d: float = Vector2(cities[i].pos).distance_to(Vector2(cities[j].pos))
				if d > best_d:
					best_d = d
					best_a = i
					best_b = j
		cities[best_a].owner = GameData.Owner.PLAYER
		cities[best_b].owner = GameData.Owner.AI
		return {"terrain": terrain, "cities": cities, "player_start": cities[best_a].pos, "ai_start": cities[best_b].pos}

	return {"terrain": terrain, "cities": cities, "player_start": Vector2i(5, 5), "ai_start": Vector2i(W - 6, H - 6)}

static func _idx(x: int, y: int) -> int:
	return y * W + x

static func is_port(terrain: Array, pos: Vector2i) -> bool:
	for d in GameData.DIRS8:
		var n: Vector2i = pos + d
		if n.x >= 0 and n.y >= 0 and n.x < W and n.y < H:
			if terrain[_idx(n.x, n.y)] == GameData.Terrain.OCEAN:
				return true
	return false

static func coast_mask(terrain: Array, x: int, y: int) -> String:
	if terrain[_idx(x, y)] != GameData.Terrain.OCEAN:
		return ""
	var m := ""
	# N=up(y-1), S=down, W=left, E=right in grid
	if y > 0 and GameData.is_land(terrain[_idx(x, y - 1)]):
		m += "N"
	if y < H - 1 and GameData.is_land(terrain[_idx(x, y + 1)]):
		m += "S"
	if x > 0 and GameData.is_land(terrain[_idx(x - 1, y)]):
		m += "W"
	if x < W - 1 and GameData.is_land(terrain[_idx(x + 1, y)]):
		m += "E"
	return m
