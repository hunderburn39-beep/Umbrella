extends Node2D
## Reactor Rush V5.1 — Godot graphics. Layout matches the HTML version over the same approved artwork.
## Free Play only: virtual credits, house reserve rule disclosed in the info screen.

const LAND := Vector2(1920, 1080)
const PORT := Vector2(1080, 1920)
const BETS := [0.05, 0.10, 0.20, 0.40, 0.60, 1.0, 2.0, 5.0, 10.0]
const WIN_TIERS := [[1000.0, "MAX WIN", "ultra"], [250.0, "QUANTUM WIN", "ultra"], [100.0, "EPIC WIN", "super"], [50.0, "SUPER WIN", "super"], [20.0, "MEGA WIN", "mega"], [10.0, "BIG WIN", "grande"]]
# rectangles in % of the artwork: [left, top, width, height] (measured on the HTML version)
const L := {
	"arena": [25.45, 9.3, 40.65, 69.7], "p1": [69.2, 9.4, 28.4, 29.2], "p2": [69.2, 40.6, 28.4, 22.5],
	"version": [8.1, 26.9, 9.4, 4.4], "balance": [20.6, 90.3, 11.3, 4.35], "lastwin": [34.4, 90.3, 10.8, 4.35], "bet": [50.8, 90.3, 8.3, 4.35],
	"message": [25.3, 79.6, 41.1, 3.0], "topup": [3.0, 4.0, 16.0, 4.0],
	"spin": [83.67, 78.43, 11.25, 20.0], "info": [2.08, 87.08, 5.1, 9.07], "sound": [7.6, 87.08, 5.1, 9.07], "menu": [13.2, 87.08, 5.1, 9.07],
	"minus": [46.98, 88.7, 3.7, 6.57], "plus": [59.22, 88.7, 3.7, 6.57], "turbo": [64.0, 87.1, 8.5, 8.6], "auto": [73.4, 87.1, 8.4, 8.6],
}
const P := {
	"arena": [14.1, 35.6, 71.9, 37.7], "p1": [9.0, 16.9, 82.0, 7.5], "p2": [9.0, 24.4, 82.0, 10.4],
	"version": [43.5, 14.5, 13.1, 2.1], "balance": [10.2, 80.1, 17.6, 2.45], "lastwin": [75.5, 80.1, 15.7, 2.45], "bet": [42.1, 79.8, 16.0, 2.5],
	"message": [13.0, 73.5, 74.0, 3.0], "topup": [3.0, 1.0, 20.0, 3.0],
	"spin": [39.44, 83.39, 21.3, 11.98], "info": [12.5, 85.52, 7.96, 4.48], "sound": [87.22, 85.29, 8.8, 4.95], "menu": [3.0, 85.3, 8.0, 4.6],
	"minus": [34.54, 78.88, 6.3, 3.54], "plus": [58.98, 78.88, 6.3, 3.54], "turbo": [22.6, 84.7, 15.7, 6.5], "auto": [62.0, 84.7, 16.0, 6.5],
}
const HOUSE_RULE := "Regra da casa (Free Play): em cada sessão o total pago nunca ultrapassa 94% do total apostado, por isso a casa nunca fica em prejuízo. Para cumprir a regra, uma ronda cujo prémio a reserva da sessão não pode pagar é substituída por outra. Os resultados dependem, portanto, do saldo da sessão e não são sorteios independentes; prémios muito grandes só saem quando a reserva os cobre. A reserva recomeça quando a página é aberta ou recarregada."

var stage := Node2D.new()
var bg := Sprite2D.new()
var tex_land: Texture2D
var tex_port: Texture2D
var board: Board
var qpanel: QuantumPanel
var fpanel: FluctPanel
var sfx: Sfx
var bridge := EngineBridge.new()
var labels := {}
var plates := {}
var buttons := {}
var msg: Label
var win_label: Label
var banner := Sprite2D.new()
var banner_text: Label
var info_layer: Control
var info_text: RichTextLabel
var marks := {}
var celeb := {}
var portrait := false
var design := LAND

var balance := 1000.0
var bet_idx := 2
var last_win := 0.0
var busy := false
var turbo := false
var auto_on := false
var spins := 0
var hits := [0, 0, 0, 0]
var last_res := {}
var js_cb = null


func _ready() -> void:
	tex_land = load("res://assets/frames/landscape.webp")
	tex_port = load("res://assets/frames/portrait.webp")
	add_child(stage)
	bg.centered = false
	stage.add_child(bg)
	board = Board.new()
	stage.add_child(board)
	qpanel = QuantumPanel.new()
	stage.add_child(qpanel)
	fpanel = FluctPanel.new()
	stage.add_child(fpanel)
	sfx = Sfx.new()
	add_child(sfx)
	for k in ["version", "balance", "lastwin", "bet"]:
		_make_plate(k)
	labels["version"].text = "V5.1 • FREE PLAY"
	msg = _label(Color("fff4c2"))
	stage.add_child(msg)
	win_label = _label(Color("ffe27a"))
	win_label.visible = false
	stage.add_child(win_label)
	banner.visible = false
	stage.add_child(banner)
	banner_text = _label(Color.WHITE)
	banner_text.visible = false
	stage.add_child(banner_text)
	for k in ["spin", "info", "sound", "menu", "minus", "plus", "turbo", "auto"]:
		_make_hit(k)
	_make_topup()
	_make_marks()
	_build_info()
	get_viewport().size_changed.connect(_relayout)
	var ok := bridge.init(0)
	_relayout()
	fpanel.set_symbol(board.textures["t0"])
	board.show_grid(bridge.random_grid(), true)
	_message("Liga 5 ou mais criaturas iguais!" if ok else "PRÉ-VISUALIZAÇÃO SEM MOTOR — abre a versão Web para jogar")
	_update_hud()
	_expose_js()


# ---------- layout ----------
func _r(p: Array) -> Rect2:
	return Rect2(design.x * float(p[0]) / 100.0, design.y * float(p[1]) / 100.0, design.x * float(p[2]) / 100.0, design.y * float(p[3]) / 100.0)


func _lay() -> Dictionary:
	return P if portrait else L


func _relayout() -> void:
	var vp := get_viewport_rect().size
	portrait = vp.y > vp.x
	design = PORT if portrait else LAND
	if portrait:
		# like the HTML version, tall phones stretch the portrait artwork vertically (limited to +30%)
		design.y = PORT.y * clampf((vp.y / vp.x) / (PORT.y / PORT.x), 1.0, 1.3)
	var s := minf(vp.x / design.x, vp.y / design.y)
	stage.scale = Vector2(s, s)
	stage.position = (vp - design * s) * 0.5
	var tex := tex_port if portrait else tex_land
	bg.texture = tex
	bg.scale = design / tex.get_size()
	var lay := _lay()
	board.set_area(_r(lay["arena"]))
	qpanel.set_area(_r(lay["p1"]), portrait)
	fpanel.set_area(_r(lay["p2"]), portrait)
	for k in plates.keys():
		var r := _r(lay[k])
		_place(plates[k], r)
		labels[k].add_theme_font_size_override("font_size", int(r.size.y * 0.66))
	for k in buttons.keys():
		_place(buttons[k], _r(lay[k]))
	var mr := _r(lay["message"])
	_place(msg, mr)
	msg.add_theme_font_size_override("font_size", int(mr.size.y * 0.8))
	var ar := _r(lay["arena"])
	_place(win_label, Rect2(ar.position.x, ar.get_center().y - ar.size.y * 0.09, ar.size.x, ar.size.y * 0.18))
	win_label.add_theme_font_size_override("font_size", int(ar.size.y * 0.11))
	_place(banner_text, Rect2(ar.position.x, ar.get_center().y + ar.size.y * 0.14, ar.size.x, ar.size.y * 0.12))
	banner_text.add_theme_font_size_override("font_size", int(ar.size.y * 0.07))
	_place(info_layer, Rect2(Vector2.ZERO, design))
	_layout_marks()


func _place(c: Control, r: Rect2) -> void:
	c.position = r.position
	c.size = r.size


func _label(col: Color) -> Label:
	var l := Label.new()
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("outline_size", 8)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _make_plate(k: String) -> void:
	var p := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.035, 0.045, 0.15, 1.0)
	sb.border_color = Color(0.2, 0.2, 0.5, 0.9)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := _label(Color("ffd15c") if k != "version" else Color("e6f6ff"))
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	p.add_child(l)
	stage.add_child(p)
	plates[k] = p
	labels[k] = l


func _make_hit(k: String) -> void:
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	var empty := StyleBoxEmpty.new()
	var hover := StyleBoxFlat.new()
	hover.bg_color = Color(1, 1, 1, 0.07)
	hover.set_corner_radius_all(80)
	var pressed := StyleBoxFlat.new()
	pressed.bg_color = Color(1, 1, 1, 0.16)
	pressed.set_corner_radius_all(80)
	b.add_theme_stylebox_override("normal", empty)
	b.add_theme_stylebox_override("focus", empty)
	b.add_theme_stylebox_override("disabled", empty)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.tooltip_text = k
	b.pressed.connect(func() -> void: _on_button(k))
	stage.add_child(b)
	buttons[k] = b


func _make_topup() -> void:
	var b := Button.new()
	b.text = "+1.000 CR"
	b.focus_mode = Control.FOCUS_NONE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.06, 0.2, 0.95)
	sb.border_color = Color("6f5be0")
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	b.add_theme_stylebox_override("normal", sb)
	b.add_theme_stylebox_override("hover", sb)
	b.add_theme_stylebox_override("pressed", sb)
	b.add_theme_color_override("font_color", Color("9fe8ff"))
	b.add_theme_font_size_override("font_size", 24)
	b.pressed.connect(func() -> void: _on_button("topup"))
	stage.add_child(b)
	buttons["topup"] = b


func _make_marks() -> void:
	for k in ["turbo", "auto", "spin"]:
		var p := Panel.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0, 0, 0, 0)
		sb.border_color = Color("7ffcff")
		sb.set_border_width_all(4)
		sb.set_corner_radius_all(90)
		sb.shadow_color = Color(0.25, 0.9, 1.0, 0.6)
		sb.shadow_size = 14
		p.add_theme_stylebox_override("panel", sb)
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		p.visible = false
		stage.add_child(p)
		marks[k] = p
	var slash := Line2D.new()
	slash.width = 7.0
	slash.default_color = Color("ff4d6d")
	slash.add_point(Vector2.ZERO)
	slash.add_point(Vector2.ZERO)
	stage.add_child(slash)
	marks["mute"] = slash


func _layout_marks() -> void:
	var lay := _lay()
	for k in ["turbo", "auto", "spin"]:
		_place(marks[k], _r(lay[k]).grow(-4))
	var s := _r(lay["sound"]).grow(-_r(lay["sound"]).size.x * 0.22)
	var line: Line2D = marks["mute"]
	line.set_point_position(0, s.position)
	line.set_point_position(1, s.end)
	line.width = s.size.x * 0.09


func _build_info() -> void:
	info_layer = Control.new()
	info_layer.visible = false
	info_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.72)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	info_layer.add_child(dim)
	var panel := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("0b1240")
	sb.border_color = Color("6f5be0")
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(18)
	panel.add_theme_stylebox_override("panel", sb)
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	panel.offset_left = 60
	panel.offset_top = 60
	panel.offset_right = -60
	panel.offset_bottom = -60
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	info_layer.add_child(panel)
	info_text = RichTextLabel.new()
	info_text.bbcode_enabled = true
	info_text.set_anchors_preset(Control.PRESET_FULL_RECT)
	info_text.offset_left = 36
	info_text.offset_top = 30
	info_text.offset_right = -36
	info_text.offset_bottom = -30
	info_text.add_theme_font_size_override("normal_font_size", 26)
	info_text.add_theme_font_size_override("bold_font_size", 28)
	info_text.mouse_filter = Control.MOUSE_FILTER_PASS
	info_text.text = _info_bbcode()
	panel.add_child(info_text)
	info_layer.gui_input.connect(_on_info_input)
	stage.add_child(info_layer)


func _info_bbcode() -> String:
	var s := "[center][b][color=#7eeeff]REACTOR RUSH V5.1 — FREE PLAY[/color][/b][/center]\n\n"
	s += "Grelha 7×7 com cascatas: liga [b]5 ou mais[/b] criaturas iguais na horizontal ou vertical. As peças ganhadoras explodem e as de cima caem.\n"
	s += "[b]Wilds[/b] substituem qualquer criatura. O [b]Quantumeter[/b] carrega com as peças ganhadoras e ativa os quatro reatores (55 / 85 / 110 / 135). O [b]Fluctometer[/b] carrega com o símbolo flutuante e cria Wilds.\n\n"
	s += "[color=#ffd79a]" + HOUSE_RULE + "[/color]\n\n"
	s += "RTP efetivo desta implementação com a regra da casa (simulação): cerca de 85% em sessões de 100 jogadas, 93,1% em 1.000 e 93,9% em 10.000; nunca acima de 94%. Créditos virtuais, sem dinheiro real.\n\n"
	s += "[center][color=#9fe8ff]Toca em qualquer lado para fechar.[/color][/center]"
	return s


# ---------- HUD ----------
func _money(x: float) -> String:
	return ("%.2f" % x).replace(".", ",")


func _update_hud() -> void:
	labels["balance"].text = _money(balance) + " CR"
	labels["lastwin"].text = _money(last_win) + " CR"
	labels["bet"].text = _money(float(BETS[bet_idx])) + " CR"
	marks["turbo"].visible = turbo
	marks["auto"].visible = auto_on
	marks["spin"].visible = busy
	marks["mute"].visible = sfx.muted
	_push_state()


func _message(t: String) -> void:
	msg.text = t


func _on_button(k: String) -> void:
	sfx.play("click")
	match k:
		"spin":
			if auto_on:
				auto_on = false
			else:
				_spin()
		"auto":
			auto_on = not auto_on
			if auto_on and not busy:
				_spin()
		"turbo":
			turbo = not turbo
			board.turbo = turbo
		"sound":
			sfx.set_muted(not sfx.muted)
		"info", "menu":
			info_layer.visible = true
		"minus":
			if not busy:
				bet_idx = maxi(0, bet_idx - 1)
		"plus":
			if not busy:
				bet_idx = mini(BETS.size() - 1, bet_idx + 1)
		"topup":
			if not busy:
				balance = roundf((balance + 1000.0) * 100.0) / 100.0
				_message("⚡ ADICIONADOS 1.000,00 CR VIRTUAIS")
	_update_hud()


func _on_info_input(e: InputEvent) -> void:
	var mb := e as InputEventMouseButton
	var st := e as InputEventScreenTouch
	if (mb != null and mb.pressed) or (st != null and st.pressed):
		info_layer.visible = false


func _unhandled_input(e: InputEvent) -> void:
	var key := e as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_SPACE:
		_spin()


# ---------- round ----------
func _spin() -> void:
	if busy:
		return
	if not bridge.ok:
		_message("PRÉ-VISUALIZAÇÃO SEM MOTOR — abre a versão Web para jogar")
		board.show_grid(bridge.random_grid(), true)
		return
	var bet: float = BETS[bet_idx]
	if balance + 0.00001 < bet:
		auto_on = false
		_message("Saldo insuficiente — usa +1.000 CR")
		_update_hud()
		return
	busy = true
	balance = roundf((balance - bet) * 100.0) / 100.0
	last_win = 0.0
	win_label.visible = false
	_message("")
	sfx.play("spin")
	_update_hud()
	var res := bridge.spin(bet)
	last_res = res
	await _play_round(res, bet)
	var won := float(res.get("credited", 0.0))
	balance = roundf((balance + won) * 100.0) / 100.0
	last_win = won
	spins += 1
	var mult := float(res.get("win", 0.0))
	if won > 0.0:
		_message("PRÉMIO %s CR" % _money(won))
		await _tier_banner(mult, won)
	else:
		_message("Sem prémio nesta ronda.")
	busy = false
	_update_hud()
	if auto_on:
		await get_tree().create_timer(0.12 if turbo else 0.4).timeout
		if auto_on:
			_spin()


func _meters(f: Dictionary) -> void:
	var garg := bool(f.get("garg", false))
	qpanel.set_state(int(f.get("qm", 0)), int(f.get("level", 0)), garg)
	fpanel.set_state(int(f.get("fl", 0)), int(f.get("flMax", 4)), garg)


func _play_round(res: Dictionary, bet: float) -> void:
	var frames: Array = res.get("frames", [])
	var removed := {}
	for f in frames:
		var kind := str(f.get("type", ""))
		_meters(f)
		match kind:
			"start":
				hits = [0, 0, 0, 0]
				fpanel.set_hits(hits)
				var ft := maxi(0, int(f.get("fluct", 0)))
				fpanel.set_symbol(board.textures["t%d" % clampi(ft, 0, 7)])
				await board.show_grid(f["grid"], true)
				sfx.play("drop")
			"win":
				var cells := []
				for c in f.get("clusters", []):
					cells.append_array(c)
				sfx.play("win")
				await board.highlight(cells)
				_show_count(float(f.get("total", 0.0)) * bet)
				await board.remove(cells)
				for c in cells:
					removed[int(c)] = true
			"explosion":
				sfx.play("zap")
				var pair: Array = f.get("pair", [])
				if pair.size() >= 2:
					board.bolt(int(pair[0]), int(pair[1]))
				var el: Array = f.get("electric", [])
				for k in range(0, el.size() - 1):
					board.bolt(int(el[k]), int(el[k + 1]))
				var gone := []
				var g: Array = f["grid"]
				for k in 49:
					if str(g[k]) == "" and str(board.cur[k]) != "":
						gone.append(k)
				await board.remove(gone)
				for k in gone:
					removed[int(k)] = true
				await _banner("instabilidade", "", 0.5)
			"settle":
				await board.settle(f["grid"], removed)
				removed = {}
				sfx.play("drop")
				var spawn: Array = f.get("spawn", [])
				if spawn.has("G3") or spawn.has("G2"):
					await _banner("gargantoon", "GARGANTOON", 0.8)
				elif spawn.has("g2"):
					await _banner("giantoonz", "ENERGOON 2×2", 0.6)
				elif spawn.has("fluct"):
					await _banner("wilds", "", 0.35)
			"level":
				var rx := int(f.get("reactor", 0))
				if rx >= 1 and rx <= 4:
					hits[rx - 1] = 1
					fpanel.set_hits(hits)
				sfx.play("level")
				await _banner("flutuante", "REATOR %d" % rx, 0.6)
			_:
				var gg = f.get("grid", null)
				if gg is Array:
					await board.show_grid(gg, false)


func _show_count(amount: float) -> void:
	win_label.text = "+" + _money(amount) + " CR"
	win_label.visible = true
	win_label.modulate.a = 1.0


func _celeb(key: String) -> Texture2D:
	if not celeb.has(key):
		celeb[key] = load("res://assets/celebrations/%s.webp" % key)
	return celeb[key]


func _banner(key: String, text: String, hold: float) -> void:
	var tex := _celeb(key)
	if tex == null:
		return
	var ar := _r(_lay()["arena"])
	var sp := 0.45 if turbo else 1.0
	var target := ar.size.x * 0.78 / float(tex.get_width())
	banner.texture = tex
	banner.position = ar.get_center()
	banner.scale = Vector2(target, target) * 0.2
	banner.modulate.a = 1.0
	banner.visible = true
	banner_text.text = text
	banner_text.visible = text != ""
	banner_text.modulate.a = 1.0
	var tw := create_tween()
	tw.tween_property(banner, "scale", Vector2(target, target), 0.3 * sp).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(hold * sp)
	tw.tween_property(banner, "modulate:a", 0.0, 0.22 * sp)
	tw.parallel().tween_property(banner_text, "modulate:a", 0.0, 0.22 * sp)
	await tw.finished
	banner.visible = false
	banner_text.visible = false


func _tier_banner(mult: float, won: float) -> void:
	for tier in WIN_TIERS:
		if mult >= float(tier[0]):
			sfx.play("big")
			await _banner(str(tier[2]), "%s  %s CR" % [tier[1], _money(won)], 1.1)
			return


# ---------- test hooks (Web) ----------
func _expose_js() -> void:
	if not OS.has_feature("web"):
		return
	js_cb = JavaScriptBridge.create_callback(_js_spin)
	var w = JavaScriptBridge.get_interface("window")
	w.__rrg_spin = js_cb
	_push_state()


func _js_spin(_args: Array) -> void:
	_spin()


func _push_state() -> void:
	if not OS.has_feature("web"):
		return
	var st := {
		"ready": true, "engine": bridge.ok, "balance": balance, "spins": spins, "busy": busy, "portrait": portrait,
		"bet": BETS[bet_idx], "lastWin": last_win,
		"govPaid": last_res.get("govPaid", 0.0), "govBets": last_res.get("govBets", 0.0), "cap": last_res.get("cap", 0.94),
	}
	JavaScriptBridge.eval("window.__rrg_state = " + JSON.stringify(st) + ";", true)
