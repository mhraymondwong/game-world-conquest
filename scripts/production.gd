class_name Production
extends RefCounted
## City production: +1/turn, spawn when cost met.

static func tick_city(city: Dictionary, is_port: bool) -> Dictionary:
	## Returns {spawn_type: int} or empty if nothing ready.
	if city.owner == GameData.Owner.NEUTRAL:
		return {}
	if city.building < 0:
		return {}
	city.progress += 1
	var cost: int = GameData.UNIT_DEFS[city.building]["cost"]
	if city.progress >= cost:
		var t: int = city.building
		# Port check for navy
		var domain: String = GameData.UNIT_DEFS[t]["domain"]
		if domain == "sea" and not is_port:
			city.progress = cost  # wait
			return {}
		city.progress = 0
		return {"spawn_type": t}
	return {}

static func set_production(city: Dictionary, unit_type: int, is_port: bool) -> bool:
	var domain: String = GameData.UNIT_DEFS[unit_type]["domain"]
	if domain == "sea" and not is_port:
		return false
	if city.building != unit_type:
		city.building = unit_type
		city.progress = 0
	return true

static func available_types(is_port: bool) -> Array[int]:
	var out: Array[int] = []
	for t in GameData.UNIT_DEFS.keys():
		var domain: String = GameData.UNIT_DEFS[t]["domain"]
		if domain == "sea" and not is_port:
			continue
		out.append(t)
	return out
