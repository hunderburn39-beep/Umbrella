class_name EngineBridge
extends RefCounted
## Talks to the validated JavaScript engine (Reactor-Rush/engine/engine.js) through web/rr_bridge.js.
## Outside the Web export there is no engine: the game shows a preview board and pays nothing.

var ok := false


func init(seed: int) -> bool:
	ok = false
	if OS.has_feature("web"):
		var r = JavaScriptBridge.eval("(window.RRG && window.RREngine) ? window.RRG.init(%d) : 'missing'" % seed, true)
		ok = str(r) == "ok"
	return ok


func spin(bet: float) -> Dictionary:
	if ok:
		var s = JavaScriptBridge.eval("window.RRG.spin(%.2f)" % bet, true)
		var d = JSON.parse_string(str(s))
		if d is Dictionary:
			return d
		push_error("RRG.spin: invalid answer from the engine")
	return preview_round()


func random_grid() -> Array:
	var g := []
	for i in 49:
		g.append("t%d" % (randi() % 8))
	return g


func preview_round() -> Dictionary:
	return {
		"win": 0.0, "credited": 0.0, "preview": true,
		"frames": [{"type": "start", "grid": random_grid(), "qm": 0, "level": 0, "fl": 0, "flMax": 4, "garg": false, "fluct": 0}],
	}
