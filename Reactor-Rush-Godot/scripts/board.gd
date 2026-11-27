class_name Board
extends Control
## 7x7 board inside the frame opening. Draws the engine's grids and animates wins and cascades.

const N := 7
const SYMBOLS := ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "wild"]
const BURST := [Color("ef6484"), Color("65e898"), Color("ffb25a"), Color("66d3ff"), Color("be88ff"), Color("ff8570"), Color("a3e077"), Color("ffe377")]

var textures := {}
var tiles: Array[Sprite2D] = []
var cur: Array = []
var cell := Vector2(100, 100)
var turbo := false
var _plate := StyleBoxFlat.new()
var _plate_hi := StyleBoxFlat.new()
var _lit := {}


func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for s in SYMBOLS:
		textures[s] = load("res://assets/symbols/%s.webp" % s)
	_plate.bg_color = Color(0.03, 0.06, 0.17, 0.92)
	_plate.border_color = Color(0.13, 0.24, 0.45, 1.0)
	_plate.set_border_width_all(1)
	_plate.set_corner_radius_all(10)
	_plate_hi.bg_color = Color(0.16, 0.2, 0.45, 0.95)
	_plate_hi.border_color = Color(1.0, 0.95, 0.7, 1.0)
	_plate_hi.set_border_width_all(2)
	_plate_hi.set_corner_radius_all(10)
	for i in N * N:
		var sp := Sprite2D.new()
		add_child(sp)
		tiles.append(sp)
		cur.append("")


func set_area(r: Rect2) -> void:
	position = r.position
	size = r.size
	cell = r.size / N
	var b := base_scale()
	for i in N * N:
		tiles[i].position = center_of(i)
		tiles[i].scale = b
	queue_redraw()


func center_of(i: int) -> Vector2:
	var row := int(i / N)
	var col := i % N
	return Vector2((col + 0.5) * cell.x, (row + 0.5) * cell.y)


func base_scale() -> Vector2:
	var tex: Texture2D = textures["t0"]
	var s := minf(cell.x, cell.y) * 0.96 / float(tex.get_width())
	return Vector2(s, s)


func speed() -> float:
	return 0.4 if turbo else 1.0


func _apply(sp: Sprite2D, sym: String) -> void:
	if sym == "":
		sp.visible = false
		return
	sp.visible = true
	var col := Color(1, 1, 1, 1)
	if sym.begins_with("t"):
		sp.texture = textures.get(sym, textures["t0"])
	else:
		sp.texture = textures["wild"]
		if sym == "u":
			col = Color(0.62, 0.62, 0.72, 1)
		elif sym == "e":
			col = Color(0.8, 1.0, 1.0, 1)
		else:
			col = Color(1.0, 0.82, 1.0, 1)
	sp.modulate = col


func _draw() -> void:
	for i in N * N:
		var row := int(i / N)
		var col := i % N
		var r := Rect2(col * cell.x + 2, row * cell.y + 2, cell.x - 4, cell.y - 4)
		draw_style_box(_plate_hi if _lit.has(i) else _plate, r)


func show_grid(grid: Array, drop: bool) -> void:
	_lit = {}
	queue_redraw()
	var tw: Tween = null
	var b := base_scale()
	for i in N * N:
		var sym := str(grid[i]) if grid[i] != null else ""
		cur[i] = sym
		var sp := tiles[i]
		_apply(sp, sym)
		sp.scale = b
		var target := center_of(i)
		if drop and sym != "":
			var row := int(i / N)
			var col := i % N
			sp.position = target - Vector2(0, (N + 1) * cell.y)
			if tw == null:
				tw = create_tween().set_parallel(true)
			tw.tween_property(sp, "position", target, 0.42 * speed()).set_delay((col * 0.035 + (N - 1 - row) * 0.03) * speed()).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		else:
			sp.position = target
	if tw != null:
		await tw.finished


func highlight(cells: Array) -> void:
	if cells.is_empty():
		return
	_lit = {}
	for c in cells:
		_lit[int(c)] = true
	queue_redraw()
	var b := base_scale()
	var d := 0.15 * speed()
	var tw := create_tween().set_parallel(true)
	for c in cells:
		var sp := tiles[int(c)]
		tw.tween_property(sp, "scale", b * 1.16, d)
		tw.tween_property(sp, "scale", b, d).set_delay(d)
		tw.tween_property(sp, "scale", b * 1.16, d).set_delay(d * 2.0)
		tw.tween_property(sp, "scale", b, d).set_delay(d * 3.0)
	await tw.finished


func remove(cells: Array) -> void:
	if cells.is_empty():
		return
	var tw := create_tween().set_parallel(true)
	for c in cells:
		var i := int(c)
		var sp := tiles[i]
		_burst(center_of(i), cur[i])
		tw.tween_property(sp, "scale", Vector2.ZERO, 0.2 * speed()).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	await tw.finished
	for c in cells:
		var i := int(c)
		cur[i] = ""
		tiles[i].visible = false
	_lit = {}
	queue_redraw()


func _burst(at: Vector2, sym: String) -> void:
	var p := CPUParticles2D.new()
	p.position = at
	p.amount = 14
	p.one_shot = true
	p.explosiveness = 1.0
	p.lifetime = 0.55 * speed()
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = cell.x * 1.2
	p.initial_velocity_max = cell.x * 2.6
	p.gravity = Vector2(0, cell.y * 4.0)
	p.scale_amount_min = cell.x * 0.04
	p.scale_amount_max = cell.x * 0.09
	var idx := int(sym.substr(1)) if sym.begins_with("t") else 4
	p.color = BURST[clampi(idx, 0, 7)]
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.2).timeout.connect(p.queue_free)


## Survivors fall onto the removed cells; new pieces enter from above (same order as the engine's gravity).
func settle(grid: Array, removed: Dictionary) -> void:
	var tw: Tween = null
	var b := base_scale()
	for col in N:
		var empties := 0
		var moves := []
		for row in range(N - 1, -1, -1):
			var i := row * N + col
			if removed.has(i) or str(cur[i]) == "":
				empties += 1
			else:
				moves.append([row + empties, row])
		for k in empties:
			moves.append([k, k - empties])
		for m in moves:
			var nr: int = m[0]
			var fr: int = m[1]
			var i := nr * N + col
			var sym := str(grid[i]) if grid[i] != null else ""
			cur[i] = sym
			var sp := tiles[i]
			_apply(sp, sym)
			sp.scale = b
			var target := center_of(i)
			if nr == fr:
				sp.position = target
				continue
			sp.position = Vector2(target.x, (fr + 0.5) * cell.y)
			if tw == null:
				tw = create_tween().set_parallel(true)
			tw.tween_property(sp, "position", target, (0.2 + 0.045 * (nr - fr)) * speed()).set_delay(col * 0.02 * speed()).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	# cells that did not move still take the engine's symbol (wild spawns, transformations)
	for i in N * N:
		var sym := str(grid[i]) if grid[i] != null else ""
		if sym != cur[i]:
			cur[i] = sym
			_apply(tiles[i], sym)
	if tw != null:
		await tw.finished
	else:
		await get_tree().process_frame


func bolt(a: int, b: int) -> void:
	var line := Line2D.new()
	var p0 := center_of(a)
	var p1 := center_of(b)
	line.width = maxf(3.0, cell.x * 0.05)
	line.default_color = Color(0.7, 1.0, 1.0, 0.95)
	var n := 7
	for k in n + 1:
		var t := float(k) / n
		var p := p0.lerp(p1, t)
		if k > 0 and k < n:
			p += Vector2(randf_range(-1, 1), randf_range(-1, 1)) * cell.x * 0.35
		line.add_point(p)
	add_child(line)
	var tw := create_tween()
	tw.tween_property(line, "modulate:a", 0.0, 0.45)
	tw.tween_callback(line.queue_free)
