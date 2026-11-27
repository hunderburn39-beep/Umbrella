class_name FluctPanel
extends Control
## FLUCTOMETER: floating symbol (same artwork as the board), energy conduit bar and four reactor pods.

const NAMES := ["ENERGOON", "ENERGOON 2×2", "GARGANTOON", "SOBRECARGA"]
const PC := [Color("1fc5ff"), Color("25d777"), Color("8a3dff"), Color("ff4fc3")]
const TRACES := [
	[Vector2(0.0, 0.2), Vector2(0.17, 0.2), Vector2(0.21, 0.28), Vector2(0.42, 0.28)],
	[Vector2(1.0, 0.2), Vector2(0.84, 0.2), Vector2(0.8, 0.28), Vector2(0.58, 0.28)],
	[Vector2(0.0, 0.82), Vector2(0.11, 0.82), Vector2(0.15, 0.74), Vector2(0.4, 0.74)],
	[Vector2(1.0, 0.82), Vector2(0.89, 0.82), Vector2(0.85, 0.74), Vector2(0.6, 0.74)],
]

var fl := 0
var fl_max := 4
var off := false
var portrait := false
var t := 0.0
var fill := 0.0
var hit := [0, 0, 0, 0]
var icon := Sprite2D.new()
var title: Label
var txt: Label
var pod_labels: Array[Label] = []
var x2: Label
var _box := StyleBoxFlat.new()
var _bar := StyleBoxFlat.new()
var _pod := StyleBoxFlat.new()
var _icon_rect := Rect2()
var _bar_rect := Rect2()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	_box.bg_color = Color("0b1240")
	_box.border_color = Color("6f5be0")
	_box.set_border_width_all(3)
	_box.set_corner_radius_all(18)
	_box.shadow_color = Color(0.7, 0.2, 1.0, 0.35)
	_box.shadow_size = 10
	_bar.bg_color = Color("070b2c")
	_bar.border_color = Color("5b4fbf")
	_bar.set_border_width_all(2)
	_bar.set_corner_radius_all(14)
	_pod.set_border_width_all(2)
	_pod.set_corner_radius_all(12)
	title = _label("FLUCTOMETER", Color("7eeeff"))
	txt = _label("0 / 4", Color("bfeaff"))
	for n in NAMES:
		pod_labels.append(_label(n, Color("8f97d6")))
	x2 = _label("×2", Color("8f97d6"))
	add_child(icon)


func _label(s: String, col: Color) -> Label:
	var l := Label.new()
	l.text = s
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.clip_text = true
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 5)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


func set_area(r: Rect2, is_portrait: bool) -> void:
	position = r.position
	size = r.size
	portrait = is_portrait
	_layout()


func set_symbol(tex: Texture2D) -> void:
	icon.texture = tex
	_layout()


func set_state(f: int, fm: int, garg: bool) -> void:
	fl = f
	fl_max = maxi(1, fm)
	off = garg
	txt.text = "DESLIGADO" if garg else "%d / %d" % [mini(f, fl_max), fl_max]


func set_hits(h: Array) -> void:
	hit = h
	for i in 4:
		var col: Color = Color.WHITE if int(hit[i]) == 1 else Color("8f97d6")
		pod_labels[i].add_theme_color_override("font_color", col)
	x2.add_theme_color_override("font_color", Color.WHITE if int(hit[3]) == 1 else Color("8f97d6"))


func _rows() -> Array:
	var th := size.y * 0.2
	var r1 := size.y * 0.3
	return [th, r1]


func _pod_rect(i: int) -> Rect2:
	var rows := _rows()
	var y0: float = rows[0] + rows[1] + size.y * 0.04
	var h := size.y - y0 - size.y * 0.05
	var gx := size.x * 0.025
	var x0 := size.x * 0.035
	var w := (size.x - 2.0 * x0 - 3.0 * gx) / 4.0
	return Rect2(x0 + i * (w + gx), y0, w, h)


func _layout() -> void:
	var rows := _rows()
	var th: float = rows[0]
	var r1: float = rows[1]
	_place(title, Rect2(0, 2, size.x, th), int(th * 0.66))
	var isz := r1 * 0.92
	_icon_rect = Rect2(size.x * 0.04, th + (r1 - isz) * 0.5, isz, isz)
	if icon.texture:
		var s := isz / float(icon.texture.get_width())
		icon.scale = Vector2(s, s)
	icon.position = _icon_rect.get_center()
	var bx := _icon_rect.end.x + size.x * 0.035
	_bar_rect = Rect2(bx, th + r1 * 0.3, size.x * 0.78 - bx, r1 * 0.4)
	_place(txt, Rect2(size.x * 0.79, th, size.x * 0.19, r1), int(r1 * 0.42))
	for i in 4:
		var pr := _pod_rect(i)
		var fit := (pr.size.x - 8.0) / (float(NAMES[i].length()) * 0.6)
		_place(pod_labels[i], Rect2(pr.position.x + 2, pr.position.y + pr.size.y * 0.6, pr.size.x - 4, pr.size.y * 0.38), int(minf(pr.size.y * 0.24, fit)))
	var p3 := _pod_rect(3)
	_place(x2, Rect2(p3.position.x, p3.position.y + p3.size.y * 0.05, p3.size.x, p3.size.y * 0.55), int(p3.size.y * 0.42))


func _place(l: Label, r: Rect2, fs: int) -> void:
	l.position = r.position
	l.size = r.size
	l.add_theme_font_size_override("font_size", maxi(fs, 8))


func _process(delta: float) -> void:
	t += delta
	fill = lerpf(fill, clampf(float(fl) / float(fl_max), 0.0, 1.0), minf(1.0, delta * 6.0))
	icon.position = _icon_rect.get_center() + Vector2(0, sin(t * 3.4) * _icon_rect.size.y * 0.05)
	queue_redraw()


func _draw() -> void:
	var w := size.x
	var h := size.y
	draw_style_box(_box, Rect2(Vector2.ZERO, size))
	# circuit traces with travelling pulses
	for k in TRACES.size():
		var pts := PackedVector2Array()
		for p in TRACES[k]:
			pts.append(Vector2(p.x * w, p.y * h))
		draw_polyline(pts, Color(0.29, 0.33, 0.72, 0.55), 2.0)
		_pulse(pts, fmod(t * (0.35 + 0.1 * k) + k * 0.25, 1.0), PC[k])
	# slow turbine
	var c := Vector2(w * 0.5, h * 0.5)
	var R := minf(w, h) * 0.42
	_glow(c, R, Color(1.0, 0.44, 0.85, 0.08))
	for k in 4:
		var a := t * 0.4 + k * PI / 4.0
		draw_line(c - Vector2(cos(a), sin(a)) * R, c + Vector2(cos(a), sin(a)) * R, Color(0.5, 0.42, 1.0, 0.25), 1.5)
	draw_arc(c, R, 0, TAU, 48, Color(0.5, 0.42, 1.0, 0.25), 1.5, true)
	# portal behind the floating symbol
	var ic := _icon_rect.get_center()
	var pr := _icon_rect.size.x * 0.62
	_glow(ic, pr * 1.1, Color(0.5, 0.95, 1.0, 0.18))
	draw_arc(ic, pr, t * 2.6, t * 2.6 + PI * 0.8, 24, Color("7ff3ff"), 3.0, true)
	draw_arc(ic, pr, t * 2.6 + PI, t * 2.6 + PI * 1.8, 24, Color("c070ff"), 3.0, true)
	draw_arc(ic, pr * 0.82, -t * 1.8, -t * 1.8 + PI * 0.7, 24, Color("ffe27a"), 2.0, true)
	draw_arc(ic, pr * 0.82, -t * 1.8 + PI, -t * 1.8 + PI * 1.7, 24, Color("ff6fd8"), 2.0, true)
	# energy conduit bar
	var br := _bar_rect
	draw_style_box(_bar, br)
	var inner := br.grow(-3)
	var fw := inner.size.x * fill
	if fw > 1.0:
		var mid := Color("a78bff").lerp(Color("ff6fd8"), fill)
		draw_polygon(PackedVector2Array([inner.position, Vector2(inner.position.x + fw, inner.position.y), Vector2(inner.position.x + fw, inner.end.y), Vector2(inner.position.x, inner.end.y)]),
			PackedColorArray([Color("27d1ff"), mid, mid, Color("27d1ff")]))
		var sp := inner.size.y * 1.6
		var k := 0
		while k * sp < fw + sp:
			var x0 := inner.position.x + fmod(k * sp + t * sp * 2.5, fw + sp) - sp * 0.5
			var x1 := x0 + sp * 0.35
			var xa := clampf(x0, inner.position.x, inner.position.x + fw)
			var xb := clampf(x1, inner.position.x, inner.position.x + fw)
			var xc := clampf(x1 - inner.size.y * 0.5, inner.position.x, inner.position.x + fw)
			var xd := clampf(x0 - inner.size.y * 0.5, inner.position.x, inner.position.x + fw)
			if xb - xa > 0.5 or xc - xd > 0.5:
				draw_colored_polygon(PackedVector2Array([Vector2(xa, inner.position.y), Vector2(xb, inner.position.y), Vector2(xc, inner.end.y), Vector2(xd, inner.end.y)]), Color(1, 1, 1, 0.22))
			k += 1
		var head := Vector2(inner.position.x + fw, inner.get_center().y)
		_glow(head, inner.size.y * (0.9 if int(t * 14.0) % 2 == 0 else 0.6), Color(0.75, 1.0, 1.0, 0.8))
	for k in range(1, 10):
		var xx := inner.position.x + inner.size.x * k / 10.0
		draw_line(Vector2(xx, inner.position.y), Vector2(xx, inner.end.y), Color(1, 1, 1, 0.12), 1.0)
	draw_line(Vector2(inner.position.x + 6, inner.position.y + 2), Vector2(inner.end.x - 6, inner.position.y + 2), Color(1, 1, 1, 0.22), 2.0)
	# reactor pods
	for i in 4:
		_pod_draw(i)


func _pod_draw(i: int) -> void:
	var r := _pod_rect(i)
	var on := int(hit[i]) == 1
	_pod.bg_color = Color("0e2350") if on else Color("0b1038")
	_pod.border_color = PC[i] if on else Color("4a4296")
	if on:
		_glow(r.get_center(), r.size.x * 0.6, Color(PC[i], 0.18))
	draw_style_box(_pod, r)
	var c := Vector2(r.get_center().x, r.position.y + r.size.y * 0.36)
	var rr := minf(r.size.x, r.size.y) * 0.3
	var sp := 2.2 if on else 9.0
	_glow(c, rr * 0.9, Color(PC[i], (0.55 + 0.2 * sin(t * 7.0)) if on else 0.12))
	_ring(c, rr, 12, t * TAU / sp, Color(PC[i], 1.0 if on else 0.45), 1.6)
	_ring(c, rr * 1.18, 20, -t * TAU / (sp * 1.5), Color(PC[i], 0.9 if on else 0.3), 1.0)
	var col := Color(1, 1, 1, 0.95) if on else Color(0.56, 0.6, 0.84, 0.9)
	var u := rr * 0.32
	if i == 0:
		for k in 4:
			draw_rect(Rect2(c.x - u + (k % 2) * (u + 2), c.y - u + int(k / 2) * (u + 2), u - 1, u - 1), col)
	elif i == 1:
		draw_rect(Rect2(c.x - u, c.y - u, u * 2, u * 2), col)
	elif i == 2:
		var v := u * 0.7
		for k in 9:
			draw_rect(Rect2(c.x - v * 1.5 + (k % 3) * (v + 1), c.y - v * 1.5 + int(k / 3) * (v + 1), v - 1, v - 1), col)


func _pulse(pts: PackedVector2Array, f: float, col: Color) -> void:
	var total := 0.0
	for k in range(1, pts.size()):
		total += pts[k - 1].distance_to(pts[k])
	var d := f * total
	for k in range(1, pts.size()):
		var seg := pts[k - 1].distance_to(pts[k])
		if d <= seg:
			_glow(pts[k - 1].lerp(pts[k], d / maxf(seg, 0.001)), 6.0, Color(col, 0.9))
			return
		d -= seg


func _glow(c: Vector2, radius: float, col: Color) -> void:
	for k in 6:
		draw_circle(c, radius * (1.0 - k * 0.15), Color(col.r, col.g, col.b, col.a * 0.35))


func _ring(c: Vector2, radius: float, segments: int, rot: float, col: Color, width: float) -> void:
	var step := TAU / segments
	for k in segments:
		if k % 2 == 0:
			var a0 := rot + k * step
			draw_arc(c, radius, a0, a0 + step * 0.9, 6, col, width, true)
