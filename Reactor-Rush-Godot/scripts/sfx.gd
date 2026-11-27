class_name Sfx
extends Node
## Music (Quantum Arcade.mp3) and short synthesised effects, like the HTML version's WebAudio sounds.

var players: Array[AudioStreamPlayer] = []
var music := AudioStreamPlayer.new()
var muted := true
var _cache := {}


func _ready() -> void:
	for i in 6:
		var p := AudioStreamPlayer.new()
		p.volume_db = -6.0
		add_child(p)
		players.append(p)
	add_child(music)
	var m = load("res://assets/audio/quantum_arcade.mp3")
	if m is AudioStreamMP3:
		m.loop = true
		music.stream = m
		music.volume_db = -11.0


func set_muted(v: bool) -> void:
	muted = v
	if muted:
		music.stop()
	elif music.stream and not music.playing:
		music.play()


func _tone(key: String, freqs: Array, ms: float, wave: String, vol: float) -> AudioStreamWAV:
	if _cache.has(key):
		return _cache[key]
	var rate := 22050
	var n := int(rate * ms / 1000.0)
	var data := PackedByteArray()
	data.resize(n * 2)
	var phase := 0.0
	for s in n:
		var tt := float(s) / rate
		var seg := mini(int(float(s) / n * freqs.size()), freqs.size() - 1)
		var f: float = freqs[seg]
		phase += f / rate
		var v := 0.0
		match wave:
			"sine":
				v = sin(TAU * phase)
			"square":
				v = 1.0 if fmod(phase, 1.0) < 0.5 else -1.0
			"tri":
				v = 4.0 * absf(fmod(phase, 1.0) - 0.5) - 1.0
			"noise":
				v = randf() * 2.0 - 1.0
		var env := minf(1.0, tt * 200.0) * pow(1.0 - float(s) / n, 1.6)
		data.encode_s16(s * 2, int(clampf(v * env * vol, -1.0, 1.0) * 32767.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.stereo = false
	w.data = data
	_cache[key] = w
	return w


func play(key: String) -> void:
	if muted:
		return
	var st: AudioStreamWAV = null
	match key:
		"spin":
			st = _tone(key, [520.0, 660.0], 110, "tri", 0.35)
		"drop":
			st = _tone(key, [190.0, 120.0], 120, "sine", 0.45)
		"win":
			st = _tone(key, [523.0, 659.0, 784.0, 1046.0], 380, "tri", 0.35)
		"zap":
			st = _tone(key, [0.0], 200, "noise", 0.22)
		"level":
			st = _tone(key, [330.0, 440.0, 554.0, 659.0, 880.0], 650, "square", 0.16)
		"big":
			st = _tone(key, [392.0, 523.0, 659.0, 784.0, 1046.0, 1318.0], 950, "tri", 0.35)
		"click":
			st = _tone(key, [880.0], 50, "sine", 0.3)
	if st == null:
		return
	for p in players:
		if not p.playing:
			p.stream = st
			p.play()
			return
	players[0].stream = st
	players[0].play()
