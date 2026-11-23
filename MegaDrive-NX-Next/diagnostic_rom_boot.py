"""Inspect a user-supplied 68000 ROM using the incomplete reference CPU.

No bundled commercial ROM, hardware timing, or claim of game compatibility.
Example: python3 diagnostic_rom_boot.py game.bin --steps 200
"""
import argparse
from pathlib import Path
from boot_bus import boot_probe
from bus_controller import ReferenceBusController
from cpu68k_reference import CPU68KReference


def inspect_rom(rom: bytes, max_steps: int = 100):
    if not 1 <= max_steps <= 100000:
        raise ValueError("steps must be 1..100000")
    probe = boot_probe(rom)
    cpu = CPU68KReference(ReferenceBusController(rom))
    cpu.reset()
    events = []
    failure = None
    for _ in range(max_steps):
        pc = cpu.pc
        try:
            step = cpu.step()
        except (NotImplementedError, ValueError, RuntimeError) as exc:
            failure = {"pc": pc, "type": type(exc).__name__, "message": str(exc)}
            break
        events.append({"pc": step.pc_before, "opcode": step.opcode,
                       "mnemonic": step.mnemonic, "next_pc": step.pc_after})
        if cpu.stopped:
            failure = {"pc": cpu.pc, "type": "STOP",
                       "message": "CPU stopped; interrupt source not supplied"}
            break
    return {"reset": probe, "steps": events, "halt": failure,
            "limit_reached": failure is None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="path to a user-supplied ROM")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--json", action="store_true", help="machine-readable trace")
    args = parser.parse_args()
    result = inspect_rom(args.rom.read_bytes(), args.steps)
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        r = result["reset"]
        print(f"RESET SSP={r['ssp']:08X} PC={r['pc']:08X} opcode={r['first_opcode']:04X}")
        for item in result["steps"]:
            print(f"{item['pc']:08X}: {item['opcode']:04X} {item['mnemonic']} -> {item['next_pc']:08X}")
        if result["halt"]:
            h = result["halt"]
            print(f"HALT {h['type']} at {h['pc']:08X}: {h['message']}")
        else:
            print(f"LIMIT: {len(result['steps'])} steps")
    return 0 if result["halt"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
