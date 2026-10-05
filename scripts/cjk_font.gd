class_name CjkFont
extends RefCounted
## Noto Sans CJK TC (face index 3). Disk load avoids Godot .ttc import hang.

const REL := "res://assets/fonts/NotoSansCJK-Regular.ttc"
const FACE_TC := 3

static var _font: Font = null
static var _face_name: String = ""

static func get_font() -> Font:
	if _font != null:
		return _font
	var abs_path := ProjectSettings.globalize_path(REL)
	if not FileAccess.file_exists(abs_path):
		abs_path = "/workspace/agents/Game Designer/world-conquest/assets/fonts/NotoSansCJK-Regular.ttc"
	if FileAccess.file_exists(abs_path):
		var ff := FontFile.new()
		ff.allow_system_fallback = true
		var err := ff.load_dynamic_font(abs_path)
		if err == OK:
			var fv := FontVariation.new()
			fv.base_font = ff
			var faces: int = ff.get_face_count()
			if faces > FACE_TC:
				fv.variation_face_index = FACE_TC
				_face_name = "Noto Sans CJK TC"
			else:
				_face_name = "face0"
			_font = fv
			print("CJK_FONT_FACE=", _face_name, " index=", fv.variation_face_index, " faces=", faces)
			return _font
		print("CJK_FONT_LOAD_ERR=", err)
	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(["Noto Sans CJK TC", "Noto Sans CJK HK", "Noto Sans CJK SC"])
	_face_name = "SystemFont TC"
	_font = sys
	print("CJK_FONT_FACE=", _face_name)
	return _font

static func face_report() -> String:
	get_font()
	return _face_name
