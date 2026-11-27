class_name QuantumPanel
extends Control
## QUANTUMETER: four animated containment tubes over an animated reactor chamber (original design).

const THRESH := [55, 85, 110, 135]
const C1 := [Color("1fc5ff"), Color("25d777"), Color("8a3dff"), Color("ff4fc3")]
const C2 := [Color("9ff6ff"), Color("b6ffd3"), Color("e0b7ff"), Color("ffe27a")]

var charge := 0
var level := 0
var off := false
var portrait := false
var t := 0.0
var fills := [0.0, 0.0, 0.0, 0.0]
var flash := 0.0
var title: Label
var count: Label
var lvl_labels: Array[Label] = []
var thr_labels: Array[Label] = []
var _box := StyleBoxFlat.new()
var _glass := StyleBoxFlat.new()
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	_box.bg_color = Color("0b1240")
	_box.border_color = Color("6f5be0")
	_box.set_border_width_all(3)
	_box.set_corner_radius_all(18)
	_box.shadow_color = Color(0.7, 0.2, 1.0, 0.35)
	_box.shadow_size = 10
	_glass.bg_color = Color("060a26")
	_glass.set_border_width_all(2)
	title = _label("QUANTUMETER", Color("7eeeff"))
	count = _label("0 / 55", Color("ffe9a8"))
	for i in 4:
		lvl_labels.append(_label(str(i + 1), Color.WHITE))
		thr_labels.append(_label(str(THRESH[i]), Color("ffe9a8")))


func _label(txt: String, col: Color) -> Label:
	var l := Label.new()
	l.text = txt
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


func set_area(r: Rect2, is_portrait: bool) -> void:
	position = r.position
	size = r.size
	portrait = is_portrait
	_layout()


func _title_h() -> float:
	return size.y * (0.27 if portrait else 0.17)


func _tube_area() -> Rect2:
	var th := _title_h()
	if portrait:
		return Rect2(size.x * 0.04, th + 4, size.x * 0.92, size.y - th - 14)
	return Rect2(size.x * 0.05, th + 2, size.x * 0.9, size.y - th * 2.0 - 4)


func _tube_rect(i: int) -> Rect2:
	var a := _tube_area()
	var gx := a.size.x * 0.05
	var w := (a.size.x - gx * 3.0) / 4.0
	return Rect2(a.position.x + i * (w + gx), a.position.y, w, a.size.y)


func _cap_h(r: Rect2) -> float:
	return 0.0 if portrait else r.size.y * 0.13


func _layout() -> void:
	var th := _title_h()
	var fs := int(th * 0.62)
	if portrait:
		_place(title, Rect2(0, 2, size.x * 0.7, th), fs)
		_place(count, Rect2(size.x * 0.66, 2, size.x * 0.32, th), int(fs * 0.9))
	else:
		_place(title, Rect2(0, 2, size.x, th), fs)
		_place(count, Rect2(0, size.y - th * 0.98, size.x, th * 0.9), int(fs * 0.85))
	for i in 4:
		var r := _tube_rect(i)
		var cap := _cap_h(r)
		lvl_labels[i].visible = not portrait
		if portrait:
			_place(thr_labels[i], r, int(r.size.y * 0.42))
		else:
			_place(lvl_labels[i], Rect2(r.position.x, r.position.y, r.size.x, cap), int(cap * 0.8))
			_place(thr_labels[i], Rect2(r.position.x, r.end.y - cap, r.size.x, cap), int(cap * 0.75))


func _place(l: Label, r: Rect2, fs: int) -> void:
	l.position = r.position
	l.size = r.size
	l.add_theme_font_size_override("font_size", maxi(fs, 8))


func set_state(c: int, lv: int, garg: bool) -> void:
	if lv > level:
		flash = 1.0
	charge = c
	level = lv
	off = garg
	count.text = "QUANTUMETER DESLIGADO" if garg else "%d / %d" % [c, THRESH[mini(lv, 3)]]


func _target(i: int) -> float:
	var lo: int = 0 if i == 0 else THRESH[i - 1]
	var hi: int = THRESH[i]
	return clampf(float(charge - lo) / float(hi - lo), 0.0, 1.0)


func _process(delta: float) -> void:
	t += delta
	flash = maxf(0.0, flash - delta * 1.5)
	for i in 4:
		fills[i] = lerpf(fills[i], _target(i), minf(1.0, delta * 6.0))
	queue_redraw()


func _draw() -> void:
	var w := size.x
	var h := size.y
	draw_style_box(_box, Rect2(Vector2.ZERO, size))
	# hex lattice
	var hs := h * (0.22 if portrait else 0.12)
	var row := 0
	var y := 0.0
	while y < h + hs:
		var x := hs * 0.866 if row % 2 == 1 else 0.0
		while x < w + hs:
			_hex(Vector2(x, y), hs * 0.5, Color(0.36, 0.42, 1.0, 0.1))
			x += hs * 1.732
		y += hs * 1.5
		row += 1
	# containment rings and breathing core
	var c := Vector2(w * 0.5, h * 0.55)
	var R := minf(w, h) * (0.9 if portrait else 0.46)
	var br := 0.5 + 0.5 * sin(t * 2.0)
	_glow(c, R * 0.95, Color(0.4, 0.85, 1.0, 0.06 + 0.04 * br + 0.2 * flash))
	_ring(c, R, 18, t * 0.35, Color(0.44, 0.49, 1.0, 0.35), 3.0)
	_ring(c, R * 0.8, 30, -t * 0.24, Color(0.75, 0.44, 1.0, 0.4), 2.0)
	# conduit with flowing light
	var py := h - h * (0.05 if portrait else 0.035)
	draw_line(Vector2(10, py), Vector2(w - 10, py), Color(0.15, 0.16, 0.42), maxf(4.0, h * 0.025))
	for k in 3:
		var px := fmod(t * w * 0.3 + k * w / 3.0, w)
		_glow(Vector2(px, py), h * 0.03, Color(0.5, 0.95, 1.0, 0.9))
	# status lamps
	for k in 2:
		var on := fmod(t * 0.9 + k * 0.5, 1.0) < 0.5
		draw_circle(Vector2(w * 0.04 + k * 14.0, h * 0.07), 4.0, Color(0.43, 1.0, 0.69, 1.0 if on else 0.3))
		draw_circle(Vector2(w * 0.96 - k * 14.0, h * 0.07), 4.0, Color(1.0, 0.44, 0.85, 0.3 if on else 1.0))
	# light sweep
	var sx := fmod(t * 0.16, 1.5) * w * 1.6 - w * 0.4
	draw_colored_polygon(PackedVector2Array([Vector2(sx, 0), Vector2(sx + w * 0.12, 0), Vector2(sx + w * 0.04, h), Vector2(sx - w * 0.08, h)]), Color(0.6, 0.95, 1.0, 0.05))
	for i in 4:
		_tube(i)


func _tube(i: int) -> void:
	var r := _tube_rect(i)
	var on := charge >= int(THRESH[i])
	var cap := _cap_h(r)
	_glass.border_color = C2[i] if on else Color("6a5bd6")
	_glass.set_corner_radius_all(int(minf(r.size.x, r.size.y) * 0.18))
	if on:
		_glow(r.get_center(), maxf(r.size.x, r.size.y) * 0.55, Color(C1[i], 0.12 + 0.06 * sin(t * 6.0)))
	draw_style_box(_glass, r)
	var inner := Rect2(r.position.x + 4, r.position.y + cap, r.size.x - 8, r.size.y - 2.0 * cap)
	var f: float = fills[i]
	if f > 0.003:
		var fh := inner.size.y * f
		var top := inner.end.y - fh
		draw_polygon(PackedVector2Array([Vector2(inner.position.x, inner.end.y), Vector2(inner.end.x, inner.end.y), Vector2(inner.end.x, top), Vector2(inner.position.x, top)]),
			PackedColorArray([C1[i], C1[i], C2[i], C2[i]]))
		var wv := inner.size.x / 4.0
		for k in 5:
			var wx := inner.position.x + fmod(k * wv + t * wv * 1.3, inner.size.x)
			draw_circle(Vector2(clampf(wx, inner.position.x + wv * 0.3, inner.end.x - wv * 0.3), top), wv * 0.3, C2[i])
		for k in 7:
			var bx := inner.position.x + inner.size.x * (0.15 + 0.7 * fmod(k * 0.37, 1.0))
			var by := inner.end.y - fmod(t * inner.size.y * 0.25 * (0.6 + 0.1 * k) + k * 23.0, fh)
			draw_circle(Vector2(bx, by), maxf(1.5, inner.size.x * 0.035), Color(1, 1, 1, 0.45))
	# reactor core: grows and brightens with the charge
	var cc := inner.get_center()
	var cr := minf(inner.size.x, inner.size.y) * (0.16 + 0.22 * f)
	var pulse := 0.85 + 0.15 * sin(t * 4.5 + i)
	_glow(cc, cr * 1.5 * pulse, Color(C2[i], 0.15 + 0.5 * f))
	draw_circle(cc, cr * 0.32 * pulse, Color(1, 1, 1, 0.2 + 0.65 * f))
	_ring(cc, cr * 0.95, 8, t * 1.3 + i, Color(C2[i], 0.25 + 0.5 * f), 1.5)
	# electric arcs once the level is reached
	if on and int(t * 12.0) % 2 == 0:
		_rng.seed = int(t * 12.0) * 31 + i
		var pts := PackedVector2Array()
		var n := 8
		for k in n + 1:
			var yy := inner.position.y + inner.size.y * float(k) / n
			pts.append(Vector2(inner.get_center().x + _rng.randf_range(-0.4, 0.4) * inner.size.x, yy))
		draw_polyline(pts, Color(1, 1, 1, 0.9), 2.0, true)
	# glass highlight
	draw_rect(Rect2(inner.position.x + inner.size.x * 0.12, inner.position.y, inner.size.x * 0.08, inner.size.y), Color(1, 1, 1, 0.1))
	if cap > 0.0:
		for top_cap in [true, false]:
			var cy := r.position.y if top_cap else r.end.y - cap
			var cr2 := Rect2(r.position.x, cy, r.size.x, cap)
			draw_polygon(PackedVector2Array([cr2.position, Vector2(cr2.end.x, cr2.position.y), cr2.end, Vector2(cr2.position.x, cr2.end.y)]),
				PackedColorArray([Color("9aa6e8"), Color("9aa6e8"), Color("262a63"), Color("262a63")]))
			draw_rect(Rect2(cr2.position.x + cr2.size.x * 0.3, cr2.position.y + cap * 0.42, cr2.size.x * 0.4, cap * 0.16), Color(C1[i], 0.3 + 0.7 * f))


func _hex(c: Vector2, r: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for k in 7:
		var a := PI / 6.0 + k * PI / 3.0
		pts.append(c + Vector2(cos(a), sin(a)) * r)
	draw_polyline(pts, col, 1.0)


func _glow(c: Vector2, radius: float, col: Color) -> void:
	for k in 6:
		draw_circle(c, radius * (1.0 - k * 0.15), Color(col.r, col.g, col.b, col.a * 0.35))


func _ring(c: Vector2, radius: float, segments: int, rot: float, col: Color, width: float) -> void:
	var step := TAU / segments
	for k in segments:
		if k % 2 == 0:
			var a0 := rot + k * step
			draw_arc(c, radius, a0, a0 + step * 0.9, 6, col, width, true)
