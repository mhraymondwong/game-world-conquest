class_name SimpleAI
extends RefCounted
## Expand / produce mixed units / attack nearby. Human vs one AI.

var rng: RandomNumberGenerator

func _init(p_rng: RandomNumberGenerator = null) -> void:
	rng = p_rng if p_rng else RandomNumberGenerator.new()

func choose_production(city: Dictionary, is_port: bool, army_count: int, transport_count: int) -> void:
	if city.owner != GameData.Owner.AI:
		return
	var choice := GameData.UnitType.ARMY
	if is_port:
		var roll := rng.randf()
		if transport_count < 2 and army_count >= 2:
			choice = GameData.UnitType.TRANSPORT
		elif roll < 0.18:
			choice = GameData.UnitType.DESTROYER
		elif roll < 0.28:
			choice = GameData.UnitType.FIGHTER
		elif roll < 0.36:
			choice = GameData.UnitType.SUBMARINE
		elif roll < 0.42:
			choice = GameData.UnitType.CARRIER
		elif roll < 0.48:
			choice = GameData.UnitType.BATTLESHIP
		else:
			choice = GameData.UnitType.ARMY
	else:
		choice = GameData.UnitType.ARMY if rng.randf() < 0.85 else GameData.UnitType.FIGHTER
	Production.set_production(city, choice, is_port)

func plan_moves(game: Node) -> void:
	var units: Array = game.get_units_of(GameData.Owner.AI)
	for u in units:
		if not u.alive or u.moves_left <= 0 or u.aboard >= 0:
			continue
		# Prefer unload armies near enemy/neutral coasts
		if u.cargo.size() > 0 and u.type == GameData.UnitType.TRANSPORT:
			if _try_ai_unload(game, u):
				continue
		var target := _pick_target(game, u)
		if target != Vector2i(-1, -1):
			_step_toward(game, u, target)
		else:
			var dirs: Array = GameData.DIRS8.duplicate()
			dirs.shuffle()
			for d in dirs:
				if game.try_move_unit(u, u.pos + d):
					break

func _try_ai_unload(game: Node, carrier: WCUnit) -> bool:
	var dirs: Array = GameData.DIRS8.duplicate()
	dirs.shuffle()
	for d in dirs:
		if game.try_unload(carrier, carrier.pos + d):
			return true
	return false

func _pick_target(game: Node, u: WCUnit) -> Vector2i:
	if u.can_capture():
		var best := Vector2i(-1, -1)
		var best_d := 999.0
		for c in game.cities:
			if c.owner == GameData.Owner.AI:
				continue
			if not GameData.is_land(game.terrain_at(c.pos)):
				continue
			var d: float = Vector2(u.pos).distance_to(Vector2(c.pos))
			if d < best_d:
				best_d = d
				best = c.pos
		if best != Vector2i(-1, -1):
			return best
	# Sea units: sail toward enemy coastal cities / land armies for bombard
	if u.domain() == "sea":
		var best2 := Vector2i(-1, -1)
		var best_d2 := 999.0
		for c in game.cities:
			if c.owner == GameData.Owner.AI:
				continue
			var d: float = Vector2(u.pos).distance_to(Vector2(c.pos))
			if d < best_d2:
				best_d2 = d
				best2 = c.pos
		if best2 != Vector2i(-1, -1):
			return best2
	var near := Vector2i(-1, -1)
	var nd := 999.0
	for e in game.units:
		if not e.alive or e.owner == u.owner or e.aboard >= 0:
			continue
		if not Combat.can_attack(u, e) and not Combat.can_bombard(u, e):
			continue
		var d: float = Vector2(u.pos).distance_to(Vector2(e.pos))
		if d < nd and d <= u.moves_left + 3:
			nd = d
			near = e.pos
	return near

func _step_toward(game: Node, u: WCUnit, goal: Vector2i) -> void:
	var guard := 12
	while u.moves_left > 0 and u.alive and guard > 0:
		guard -= 1
		if u.pos == goal:
			break
		# If adjacent to goal and can bombard / attack, do so
		var dgoal: Vector2i = goal - u.pos
		if maxi(absi(dgoal.x), absi(dgoal.y)) == 1:
			if game.try_move_unit(u, goal):
				continue
		var best_d := Vector2(u.pos).distance_to(Vector2(goal))
		var best_p := u.pos
		for d in GameData.DIRS8:
			var np: Vector2i = u.pos + d
			var nd: float = Vector2(np).distance_to(Vector2(goal))
			if nd < best_d and game.can_enter(u, np):
				best_d = nd
				best_p = np
		if best_p == u.pos:
			break
		if not game.try_move_unit(u, best_p):
			break
