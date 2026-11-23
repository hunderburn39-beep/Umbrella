"""Minimal instruction-level 68000 reference harness for boot research.

Supports NOP, MOVEQ, BRA.s/BRA.w, and selected MOVE.W forms.
All instruction fetches use ReferenceBusController's ROM/RAM handshake.
Not a full 68000 emulator, ASIC core, or ROM-compatible execution engine.
"""
from dataclasses import dataclass
from boot_bus import reset_vectors
from bus_controller import ReferenceBusController
from bus_cycle import Request

@dataclass(frozen=True)
class StepResult:
    pc_before: int
    opcode: int
    pc_after: int
    mnemonic: str

class CPU68KReference:
    def __init__(self, controller: ReferenceBusController):
        self.bus = controller
        self.pc = 0
        self.ssp = 0
        self.d = [0] * 8
        self.a = [0] * 8
        self.stopped = False
        self.vdp_ready = False  # Explicit test-only peripheral readiness.

    def reset(self):
        vectors = reset_vectors(self.bus.memory.rom)
        if vectors.initial_pc & 1:
            raise ValueError("odd reset PC")
        self.pc = vectors.initial_pc
        self.ssp = vectors.initial_ssp
        self.d[:] = [0] * 8
        self.a[:] = [0] * 8
        self.a[7] = self.ssp
        self.stopped = False

    def fetch_word(self):
        if self.pc & 1:
            raise ValueError("odd instruction fetch PC")
        self.bus.begin(Request(self.pc & 0xffffff, True))
        try:
            if not self.bus.clock():
                raise NotImplementedError("instruction fetch responder not ready")
            acknowledged, word = self.bus.finish()
            if not acknowledged or word is None:
                raise RuntimeError("instruction fetch did not complete")
        except BaseException:
            from bus_cycle import Phase
            if self.bus.cycle.phase is not Phase.IDLE:
                self.bus.finish()
            raise
        self.pc = (self.pc + 2) & 0xffffffff
        return word

    def read_word(self, address: int) -> int:
        """Read a word via the bus, with explicit VDP readiness required."""
        if not 0 <= address <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        self.bus.begin(Request(address, True))
        try:
            if address in (0xc00000, 0xc00004):
                acknowledged = self.bus.clock_vdp_reference(ready=self.vdp_ready)
            else:
                acknowledged = self.bus.clock()
            if not acknowledged:
                raise NotImplementedError("bus responder not ready")
            completed, value = self.bus.finish()
            if not completed or value is None:
                raise RuntimeError("bus read did not complete")
            return value
        except BaseException:
            from bus_cycle import Phase
            if self.bus.cycle.phase is not Phase.IDLE:
                self.bus.finish()
            raise

    def write_word(self, address: int, value: int):
        """Issue one 68000 word write through the reference bus.

        VDP transactions require an explicitly enabled reference responder;
        this does not infer VA2 hardware DTACK or FIFO readiness.
        """
        self.bus.begin(Request(address & 0xffffff, False, value))
        try:
            if address in (0xc00000, 0xc00004):
                ack = self.bus.clock_vdp_reference(ready=self.vdp_ready)
            else:
                ack = self.bus.clock()
            if not ack:
                raise NotImplementedError("bus responder not ready")
            completed, _ = self.bus.finish()
            if not completed:
                raise RuntimeError("bus write not acknowledged")
        except BaseException:
            from bus_cycle import Phase
            if self.bus.cycle.phase is not Phase.IDLE:
                self.bus.finish()
            raise

    def step(self) -> StepResult:
        if self.stopped:
            raise RuntimeError("CPU is stopped")
        before = self.pc
        opcode = self.fetch_word()
        if opcode == 0x4e71:
            mnemonic = "NOP"
        elif opcode == 0x4e72:
            raise NotImplementedError("STOP requires supervisor/status-register model")
        elif opcode & 0xf100 == 0x7000:
            register = (opcode >> 9) & 7
            immediate = opcode & 0xff
            self.d[register] = (immediate - 256 if immediate & 0x80 else immediate) & 0xffffffff
            mnemonic = "MOVEQ"
        elif opcode & 0xf1ff == 0x207c:
            # MOVEA.L #immediate,An; no condition codes modeled.
            register = (opcode >> 9) & 7
            self.a[register] = (self.fetch_word() << 16) | self.fetch_word()
            mnemonic = "MOVEA.L #imm,An"
        elif opcode & 0xf1f8 == 0x3010:
            # MOVE.W (An),Dn, preserving upper 16 bits.
            dst = (opcode >> 9) & 7
            src = opcode & 7
            value = self.read_word(self.a[src])
            self.d[dst] = (self.d[dst] & 0xffff0000) | value
            mnemonic = "MOVE.W (An),Dn"
        elif opcode & 0xf1f8 == 0x3080:
            # MOVE.W Dn,(An)
            dst = (opcode >> 9) & 7
            src = opcode & 7
            self.write_word(self.a[dst], self.d[src] & 0xffff)
            mnemonic = "MOVE.W Dn,(An)"
        elif opcode & 0xf1ff == 0x3039:
            # MOVE.W (absolute long), Dn. Word writes preserve upper Dn.
            register = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            value = self.read_word(address)
            self.d[register] = (self.d[register] & 0xffff0000) | value
            mnemonic = "MOVE.W (abs.l),Dn"
        elif opcode & 0xf1ff == 0x303c:
            # MOVE.W #immediate, Dn.
            register = (opcode >> 9) & 7
            value = self.fetch_word()
            self.d[register] = (self.d[register] & 0xffff0000) | value
            mnemonic = "MOVE.W #imm,Dn"
        elif opcode == 0x33fc:
            # MOVE.W #immediate, (absolute long)
            value = self.fetch_word()
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.write_word(address, value)
            mnemonic = "MOVE.W #imm,(abs.l)"
        elif opcode & 0xfff8 == 0x33c0:
            # MOVE.W Dn, (absolute long)
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.write_word(address, self.d[opcode & 7] & 0xffff)
            mnemonic = "MOVE.W Dn,(abs.l)"
        elif opcode & 0xff00 == 0x6000:
            displacement = opcode & 0xff
            if displacement == 0:
                extension = self.fetch_word()
                displacement = extension - 65536 if extension & 0x8000 else extension
            else:
                displacement = displacement - 256 if displacement & 0x80 else displacement
            target = (self.pc + displacement) & 0xffffffff
            if target & 1:
                raise ValueError("odd BRA target")
            self.pc = target
            mnemonic = "BRA"
        else:
            self.pc = before
            raise NotImplementedError(f"68000 opcode 0x{opcode:04x} not implemented")
        return StepResult(before, opcode, self.pc, mnemonic)

    def run(self, max_steps: int = 100):
        if not 1 <= max_steps <= 100000:
            raise ValueError("max_steps must be 1..100000")
        return tuple(self.step() for _ in range(max_steps))
