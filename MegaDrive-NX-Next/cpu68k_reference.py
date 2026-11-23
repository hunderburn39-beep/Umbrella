"""Minimal instruction-level 68000 reference harness for boot research.

Supports selected MOVE, MOVEQ, CMP, branch, call, and return forms, plus the
ADD/SUB/AND/OR/EOR/CMP/shift/LEA/TST groups with the standard addressing modes
(see cpu68k_alu_ops.py and cpu68k_ea.py).
All instruction fetches use ReferenceBusController's ROM/RAM handshake.
Not a full 68000 emulator, ASIC core, or ROM-compatible execution engine.
"""
from dataclasses import dataclass
from boot_bus import reset_vectors
from bus_controller import ReferenceBusController
from bus_cycle import Request
from cpu68k_alu_ops import execute as execute_alu_group

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
        self.ccr = 0  # X N Z V C; only N/Z/V/C updates for modeled operations.
        self.sr_upper = 0x2700  # Reset supervisor mode, interrupt mask 7.

    def reset(self):
        vectors = reset_vectors(self.bus.memory.rom)
        # Validate both reset vectors before mutating the CPU state.
        if vectors.initial_ssp & 1:
            raise ValueError("odd reset SSP")
        if not 0 <= vectors.initial_ssp <= 0xffffff:
            raise ValueError("reset SSP outside 24-bit reference bus")
        if vectors.initial_pc & 1:
            raise ValueError("odd reset PC")
        if not 0 <= vectors.initial_pc <= 0xfffffe:
            raise ValueError("reset PC outside 24-bit reference bus")
        self.pc = vectors.initial_pc
        self.ssp = vectors.initial_ssp
        self.d[:] = [0] * 8
        self.a[:] = [0] * 8
        self.a[7] = self.ssp
        self.stopped = False
        self.vdp_ready = False  # Reset must revoke test-only external readiness.
        self.ccr = 0
        self.sr_upper = 0x2700

    @property
    def sr(self) -> int:
        return self.sr_upper | self.ccr

    def set_sr_reference(self, value: int):
        """Limited supervisor SR write; no user/supervisor stack switching yet."""
        if not 0 <= value <= 0xffff:
            raise ValueError("SR must be 16-bit")
        if not (self.sr_upper & 0x2000):
            raise NotImplementedError("privilege exception entry not modeled")
        if not (value & 0x2000):
            raise NotImplementedError("user-mode stack switching not modeled")
        if value & 0x08e0:
            raise NotImplementedError("unmodeled SR control bits")
        self.sr_upper = value & 0xff00
        self.ccr = value & 0x1f

    def fetch_word(self):
        if self.pc & 1:
            raise ValueError("odd instruction fetch PC")
        if not 0 <= self.pc <= 0xfffffe:
            raise ValueError("instruction PC outside 24-bit reference bus")
        self.bus.begin(Request(self.pc, True))
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
        if address & 1:
            raise ValueError("unaligned 68000 word read")
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
        if not 0 <= address <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        if address & 1:
            raise ValueError("unaligned 68000 word write")
        self.bus.begin(Request(address, False, value))
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

    def read_byte(self, address: int) -> int:
        """Read one byte through a bus byte lane (even=upper, odd=lower).

        Only cartridge ROM and work RAM model byte lanes; peripheral byte
        accesses are refused by the bus controller with NotImplementedError.
        """
        if not 0 <= address <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        odd = bool(address & 1)
        self.bus.begin(Request(address, True, upper=not odd, lower=odd))
        try:
            if not self.bus.clock():
                raise NotImplementedError("bus responder not ready")
            completed, value = self.bus.finish()
            if not completed or value is None:
                raise RuntimeError("bus read did not complete")
            return value & 0xff if odd else value >> 8
        except BaseException:
            from bus_cycle import Phase
            if self.bus.cycle.phase is not Phase.IDLE:
                self.bus.finish()
            raise

    def write_byte(self, address: int, value: int):
        """Write one byte through a bus byte lane; see read_byte limits."""
        if not 0 <= address <= 0xffffff:
            raise ValueError("address outside 24-bit bus")
        if not 0 <= value <= 0xff:
            raise ValueError("byte value required")
        odd = bool(address & 1)
        self.bus.begin(Request(address, False, value if odd else value << 8,
                               upper=not odd, lower=odd))
        try:
            if not self.bus.clock():
                raise NotImplementedError("bus responder not ready")
            completed, _ = self.bus.finish()
            if not completed:
                raise RuntimeError("bus write not acknowledged")
        except BaseException:
            from bus_cycle import Phase
            if self.bus.cycle.phase is not Phase.IDLE:
                self.bus.finish()
            raise

    def read_long(self, address: int) -> int:
        """Read a big-endian longword as two ordered word bus cycles."""
        return (self.read_word(address) << 16) | self.read_word(address + 2)

    def write_long(self, address: int, value: int):
        """Write a longword as two ordered word cycles, high word first.

        A fault on the second word leaves the first word already written;
        real 68000 bus-error behavior is not modeled.
        """
        if not 0 <= value <= 0xffffffff:
            raise ValueError("32-bit value required")
        self.write_word(address, value >> 16)
        self.write_word(address + 2, value & 0xffff)

    def push_long(self, value: int):
        """Push a longword as two big-endian bus words onto A7."""
        if self.a[7] & 1:
            raise ValueError("unaligned stack pointer")
        new_sp = (self.a[7] - 4) & 0xffffffff
        if new_sp > 0xffffff:
            raise NotImplementedError("stack address outside reference bus")
        self.write_word(new_sp, (value >> 16) & 0xffff)
        self.write_word(new_sp + 2, value & 0xffff)
        self.a[7] = new_sp

    def pop_long(self) -> int:
        """Pop a big-endian longword from the A7 stack."""
        sp = self.a[7]
        if sp & 1:
            raise ValueError("unaligned stack pointer")
        if not 0 <= sp <= 0xfffffc:
            raise NotImplementedError("stack read outside reference bus")
        value = (self.read_word(sp) << 16) | self.read_word(sp + 2)
        self.a[7] = (sp + 4) & 0xffffffff
        return value

    def _enter_exception_reference(self, vector: int, irq_level=None):
        """Enter a supervisor-only 68000 short exception frame."""
        if not (self.sr_upper & 0x2000):
            raise NotImplementedError("user-mode exception entry not modeled")
        vector_address = vector * 4
        target = (self.read_word(vector_address) << 16) | self.read_word(vector_address + 2)
        if target & 1:
            raise ValueError("odd exception handler PC")
        sp = self.a[7]
        if sp & 1 or not 6 <= sp <= 0xffffff:
            raise ValueError("invalid supervisor exception stack")
        saved_sr, saved_pc = self.sr, self.pc
        self.push_long(saved_pc)
        self.write_word(self.a[7] - 2, saved_sr)
        self.a[7] -= 2
        self.sr_upper &= ~0x8000
        if irq_level is not None:
            self.sr_upper = (self.sr_upper & ~0x0700) | (irq_level << 8)
        self.pc = target
        self.stopped = False

    def trap_reference(self, number: int):
        """Explicit TRAP #n via vector 32+n, not a hardware IRQ."""
        if not 0 <= number <= 15:
            raise ValueError("TRAP vector must be 0..15")
        self._enter_exception_reference(32 + number)

    def service_autovector_irq_reference(self, level: int) -> bool:
        """Explicit test-only autovector IRQ level 1..6.

        The caller supplies an asserted IRQ and its autovector selection.
        No physical VDP signal, arbitration, or IACK timing is inferred.
        """
        if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 6:
            raise ValueError("supported autovector IRQ level must be 1..6")
        if level <= ((self.sr_upper >> 8) & 7):
            return False
        self._enter_exception_reference(24 + level, irq_level=level)
        return True

    def _logic_flags(self, value: int, bits: int):
        """MOVE/MOVEQ: preserve X, set N/Z, clear V/C."""
        mask = (1 << bits) - 1
        result = value & mask
        self.ccr = (self.ccr & 0x10) | (0x08 if result & (1 << (bits - 1)) else 0) | (0x04 if result == 0 else 0)

    def _compare_word(self, destination: int, source: int):
        """CMP.W: destination - source; preserve X."""
        a, b = destination & 0xffff, source & 0xffff
        result = (a - b) & 0xffff
        negative = bool(result & 0x8000)
        overflow = bool(((a ^ b) & (a ^ result)) & 0x8000)
        carry = a < b
        self.ccr = (self.ccr & 0x10) | (0x08 if negative else 0) | (0x04 if result == 0 else 0) | (0x02 if overflow else 0) | (0x01 if carry else 0)

    def _condition(self, code: int) -> bool:
        n, z, v, carry = (bool(self.ccr & bit) for bit in (8, 4, 2, 1))
        return (True, False, not (carry or z), carry or z, not carry, carry,
                not z, z, not v, v, not n, n, n == v, n != v,
                not z and n == v, z or n != v)[code]

    def step(self) -> StepResult:
        if self.stopped:
            raise RuntimeError("CPU is stopped")
        before = self.pc
        opcode = self.fetch_word()
        if opcode == 0x4e71:
            mnemonic = "NOP"
        elif opcode == 0x4ef9:
            # JMP (absolute long), no stack write.
            target = (self.fetch_word() << 16) | self.fetch_word()
            if target & 1:
                raise ValueError("odd JMP target")
            self.pc = target
            mnemonic = "JMP"
        elif opcode & 0xfff8 == 0x4ed0:
            # JMP (An), no stack write.
            target = self.a[opcode & 7]
            if target & 1:
                raise ValueError("odd JMP target")
            self.pc = target
            mnemonic = "JMP"
        elif opcode & 0xfff8 == 0x4e50:
            # LINK An,#disp16: save old frame pointer then allocate stack.
            register = opcode & 7
            displacement = self.fetch_word()
            if displacement & 0x8000:
                displacement -= 0x10000
            self.push_long(self.a[register])
            frame = self.a[7]
            new_sp = (frame + displacement) & 0xffffffff
            if new_sp & 1:
                raise ValueError("unaligned LINK stack pointer")
            if not 0 <= new_sp <= 0xffffff:
                raise ValueError("LINK stack outside 24-bit reference bus")
            self.a[register] = frame
            self.a[7] = new_sp
            mnemonic = "LINK An,#disp16"
        elif opcode & 0xfff8 == 0x4e58:
            # UNLK An: restore A7 from frame pointer, then pop saved An.
            register = opcode & 7
            frame = self.a[register]
            if frame & 1 or not 0 <= frame <= 0xfffffc:
                raise ValueError("invalid UNLK frame pointer")
            saved_sp = self.a[7]
            self.a[7] = frame
            try:
                previous = self.pop_long()
            except BaseException:
                self.a[7] = saved_sp
                raise
            self.a[register] = previous
            mnemonic = "UNLK An"
        elif opcode & 0xfff8 == 0x4850:
            # PEA (An): push effective address, not the pointed-to value.
            address = self.a[opcode & 7]
            self.push_long(address)
            mnemonic = "PEA (An)"
        elif opcode == 0x4879:
            # PEA (abs.l): push 32-bit absolute effective address.
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.push_long(address)
            mnemonic = "PEA (abs.l)"
        elif opcode == 0x4e75:
            target = self.pop_long()
            if target & 1:
                raise ValueError("odd RTS target")
            self.pc = target
            mnemonic = "RTS"
        elif opcode == 0x4eb9:
            # JSR (absolute long)
            target = (self.fetch_word() << 16) | self.fetch_word()
            if target & 1:
                raise ValueError("odd JSR target")
            self.push_long(self.pc)
            self.pc = target
            mnemonic = "JSR"
        elif opcode & 0xfff8 == 0x4e90:
            # JSR (An)
            target = self.a[opcode & 7]
            if target & 1:
                raise ValueError("odd JSR target")
            self.push_long(self.pc)
            self.pc = target
            mnemonic = "JSR"
        elif opcode == 0x4e73:
            # RTE: restore 68000 short supervisor exception frame.
            if not (self.sr_upper & 0x2000):
                raise NotImplementedError("privilege exception entry not modeled")
            sp = self.a[7]
            if sp & 1 or not 0 <= sp <= 0xfffffa:
                raise ValueError("invalid supervisor exception frame")
            restored_sr = self.read_word(sp)
            restored_pc = (self.read_word(sp + 2) << 16) | self.read_word(sp + 4)
            if restored_pc & 1:
                raise ValueError("odd RTE return PC")
            if not (restored_sr & 0x2000) or restored_sr & 0x08e0:
                raise NotImplementedError("unsupported restored SR")
            self.a[7] = sp + 6
            self.set_sr_reference(restored_sr)
            self.pc = restored_pc
            mnemonic = "RTE"
        elif opcode & 0xfff0 == 0x4e40:
            self.trap_reference(opcode & 15)
            mnemonic = "TRAP"
        elif opcode == 0x4e72:
            # STOP #SR: reference-only halt; interrupts and exceptions absent.
            if not (self.sr_upper & 0x2000):
                raise NotImplementedError("privilege exception entry not modeled")
            value = self.fetch_word()
            self.set_sr_reference(value)
            self.stopped = True
            mnemonic = "STOP"
        elif opcode & 0xf100 == 0x7000:
            register = (opcode >> 9) & 7
            immediate = opcode & 0xff
            self.d[register] = (immediate - 256 if immediate & 0x80 else immediate) & 0xffffffff
            self._logic_flags(self.d[register], 32)
            mnemonic = "MOVEQ"
        elif opcode & 0xf1ff == 0x203c:
            # MOVE.L #immediate,Dn; two big-endian extension words.
            register = (opcode >> 9) & 7
            value = (self.fetch_word() << 16) | self.fetch_word()
            self.d[register] = value
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L #imm,Dn"
        elif opcode & 0xf1ff == 0x2039:
            # MOVE.L (abs.l),Dn; high word then low word.
            register = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            if address > 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self.d[register] = value
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L (abs.l),Dn"
        elif opcode == 0x23fc:
            # MOVE.L #immediate,(abs.l); two word writes.
            value = (self.fetch_word() << 16) | self.fetch_word()
            address = (self.fetch_word() << 16) | self.fetch_word()
            if address > 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            self.write_word(address, value >> 16)
            self.write_word(address + 2, value & 0xffff)
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L #imm,(abs.l)"
        elif opcode & 0xfff8 == 0x23c0:
            # MOVE.L Dn,(abs.l), two ordered big-endian word transfers.
            register = opcode & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            if address > 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = self.d[register] & 0xffffffff
            self.write_word(address, (value >> 16) & 0xffff)
            self.write_word(address + 2, value & 0xffff)
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L Dn,(abs.l)"
        elif opcode & 0xf1f8 == 0x3050:
            # MOVEA.W (An),Am reads a signed word through the reference bus.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            value = self.read_word(self.a[source])
            self.a[destination] = value | 0xffff0000 if value & 0x8000 else value
            mnemonic = "MOVEA.W (An),Am"
        elif opcode & 0xf1ff == 0x3079:
            # MOVEA.W (abs.l),An sign-extends memory word, CCR unchanged.
            destination = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            value = self.read_word(address)
            self.a[destination] = value | 0xffff0000 if value & 0x8000 else value
            mnemonic = "MOVEA.W (abs.l),An"
        elif opcode & 0xf1ff == 0x307c:
            # MOVEA.W #imm,An sign-extends 16-bit immediate; CCR unchanged.
            register = (opcode >> 9) & 7
            value = self.fetch_word()
            self.a[register] = (value | 0xffff0000) if value & 0x8000 else value
            mnemonic = "MOVEA.W #imm,An"
        elif opcode & 0xf1ff == 0x41f9:
            # LEA (abs.l),An loads an effective address without bus data read.
            register = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.a[register] = address
            mnemonic = "LEA (abs.l),An"
        elif opcode & 0xf1f8 == 0x41d0:
            # LEA (An),Am copies address register, not pointed-to contents.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            self.a[destination] = self.a[source]
            mnemonic = "LEA (An),Am"
        elif opcode & 0xf1f8 in (0x1000, 0x2000, 0x3000):
            bits = {1: 8, 2: 32, 3: 16}[opcode >> 12]
            mask = (1 << bits) - 1
            source, destination = opcode & 7, (opcode >> 9) & 7
            value = self.d[source] & mask
            self.d[destination] = (self.d[destination] & ~mask) | value
            self._logic_flags(value, bits)
            mnemonic = "MOVE." + {8: "B", 16: "W", 32: "L"}[bits] + " Dn,Dm"
        elif opcode & 0xf1f8 in (0x2040, 0x3040):
            source, destination = opcode & 7, (opcode >> 9) & 7
            value = self.d[source]
            word = (opcode >> 12) == 3
            if word:
                value &= 0xffff
                if value & 0x8000:
                    value |= 0xffff0000
            self.a[destination] = value & 0xffffffff
            mnemonic = "MOVEA." + ("W" if word else "L") + " Dn,An"
        elif opcode & 0xf1f8 in (0xb000, 0xb080):
            bits = 32 if opcode & 0x80 else 8
            mask = (1 << bits) - 1
            sign = 1 << (bits - 1)
            a = self.d[(opcode >> 9) & 7] & mask
            b = self.d[opcode & 7] & mask
            result = (a - b) & mask
            self.ccr = ((self.ccr & 16) | (8 if result & sign else 0)
                        | (4 if result == 0 else 0)
                        | (2 if (a ^ b) & (a ^ result) & sign else 0)
                        | int(a < b))
            mnemonic = "CMP." + ("L" if bits == 32 else "B") + " Dn,Dm"
        elif opcode & 0xf1ff == 0x207c:
            # MOVEA.L #immediate,An; no condition codes modeled.
            register = (opcode >> 9) & 7
            self.a[register] = (self.fetch_word() << 16) | self.fetch_word()
            mnemonic = "MOVEA.L #imm,An"
        elif opcode & 0xf1ff == 0x2079:
            # MOVEA.L (abs.l),An: address-register transfer leaves CCR unchanged.
            destination = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            if not 0 <= address <= 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self.a[destination] = value
            mnemonic = "MOVEA.L (abs.l),An"
        elif opcode & 0xf1f8 == 0x2050:
            # MOVEA.L (An),Am: source address captured before destination update.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            address = self.a[source]
            if not 0 <= address <= 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self.a[destination] = value
            mnemonic = "MOVEA.L (An),Am"
        elif opcode & 0xf1f8 == 0x2010:
            # MOVE.L (An),Dn. Preserve An; two big-endian word reads.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            address = self.a[source]
            if not 0 <= address <= 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self.d[destination] = value
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L (An),Dn"
        elif opcode & 0xf1f8 == 0x2080:
            # MOVE.L Dn,(An). Preserve An; high word before low word.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            address = self.a[destination]
            if not 0 <= address <= 0xfffffd:
                raise ValueError("longword crosses reference bus boundary")
            value = self.d[source] & 0xffffffff
            self.write_word(address, (value >> 16) & 0xffff)
            self.write_word(address + 2, value & 0xffff)
            self._logic_flags(value, 32)
            mnemonic = "MOVE.L Dn,(An)"
        elif opcode & 0xf1f8 == 0x3010:
            # MOVE.W (An),Dn, preserving upper 16 bits.
            dst = (opcode >> 9) & 7
            src = opcode & 7
            value = self.read_word(self.a[src])
            self.d[dst] = (self.d[dst] & 0xffff0000) | value
            self._logic_flags(value, 16)
            mnemonic = "MOVE.W (An),Dn"
        elif opcode & 0xf1f8 == 0x3080:
            # MOVE.W Dn,(An)
            dst = (opcode >> 9) & 7
            src = opcode & 7
            self.write_word(self.a[dst], self.d[src] & 0xffff)
            self._logic_flags(self.d[src], 16)
            mnemonic = "MOVE.W Dn,(An)"
        elif opcode & 0xf1ff == 0x3039:
            # MOVE.W (absolute long), Dn. Word writes preserve upper Dn.
            register = (opcode >> 9) & 7
            address = (self.fetch_word() << 16) | self.fetch_word()
            value = self.read_word(address)
            self.d[register] = (self.d[register] & 0xffff0000) | value
            self._logic_flags(value, 16)
            mnemonic = "MOVE.W (abs.l),Dn"
        elif opcode & 0xf1ff == 0x303c:
            # MOVE.W #immediate, Dn.
            register = (opcode >> 9) & 7
            value = self.fetch_word()
            self.d[register] = (self.d[register] & 0xffff0000) | value
            self._logic_flags(value, 16)
            mnemonic = "MOVE.W #imm,Dn"
        elif opcode == 0x33fc:
            # MOVE.W #immediate, (absolute long)
            value = self.fetch_word()
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.write_word(address, value)
            self._logic_flags(value, 16)
            mnemonic = "MOVE.W #imm,(abs.l)"
        elif opcode & 0xfff8 == 0x33c0:
            # MOVE.W Dn, (absolute long)
            address = (self.fetch_word() << 16) | self.fetch_word()
            self.write_word(address, self.d[opcode & 7] & 0xffff)
            self._logic_flags(self.d[opcode & 7], 16)
            mnemonic = "MOVE.W Dn,(abs.l)"
        elif opcode & 0xf1f8 in (0x5000, 0x5100):
            # ADDQ.B / SUBQ.B #1..8,Dn; only the low byte changes.
            register = opcode & 7
            immediate = (opcode >> 9) & 7 or 8
            subtract = bool(opcode & 0x0100)
            original = self.d[register] & 0xff
            result = (original - immediate if subtract else original + immediate) & 0xff
            if subtract:
                overflow = bool(((original ^ immediate) & (original ^ result)) & 0x80)
                carry = original < immediate
            else:
                overflow = bool((~(original ^ immediate) & (original ^ result)) & 0x80)
                carry = original + immediate > 0xff
            self.d[register] = (self.d[register] & 0xffffff00) | result
            self.ccr = ((0x10 if carry else 0) | (0x08 if result & 0x80 else 0)
                        | (0x04 if result == 0 else 0) | (0x02 if overflow else 0)
                        | (0x01 if carry else 0))
            mnemonic = "SUBQ.B #imm,Dn" if subtract else "ADDQ.B #imm,Dn"
        elif opcode & 0xf1f8 in (0x5048, 0x5148, 0x5088, 0x5188):
            # ADDQ/SUBQ to An: word and long forms both operate on
            # the full 32-bit address register and never modify CCR.
            register = opcode & 7
            immediate = (opcode >> 9) & 7 or 8
            subtract = bool(opcode & 0x0100)
            self.a[register] = ((self.a[register] - immediate) if subtract
                                else (self.a[register] + immediate)) & 0xffffffff
            size = "L" if opcode & 0x0080 else "W"
            mnemonic = ("SUBQ" if subtract else "ADDQ") + "." + size + " #imm,An"
        elif opcode & 0xf1f8 in (0x5080, 0x5180):
            # ADDQ.L / SUBQ.L #1..8,Dn. X follows C on arithmetic.
            register = opcode & 7
            immediate = (opcode >> 9) & 7 or 8
            subtract = bool(opcode & 0x0100)
            original = self.d[register] & 0xffffffff
            result = (original - immediate if subtract else original + immediate) & 0xffffffff
            if subtract:
                overflow = bool(((original ^ immediate) & (original ^ result)) & 0x80000000)
                carry = original < immediate
            else:
                overflow = bool((~(original ^ immediate) & (original ^ result)) & 0x80000000)
                carry = original + immediate > 0xffffffff
            self.d[register] = result
            self.ccr = ((0x10 if carry else 0) | (0x08 if result & 0x80000000 else 0)
                        | (0x04 if result == 0 else 0) | (0x02 if overflow else 0)
                        | (0x01 if carry else 0))
            mnemonic = "SUBQ.L #imm,Dn" if subtract else "ADDQ.L #imm,Dn"
        elif opcode & 0xf1f8 in (0x5040, 0x5140):
            # ADDQ.W / SUBQ.W #1..8,Dn; upper word is preserved.
            register = opcode & 7
            immediate = (opcode >> 9) & 7 or 8
            subtract = bool(opcode & 0x0100)
            original = self.d[register] & 0xffff
            result = (original - immediate if subtract else original + immediate) & 0xffff
            self.d[register] = (self.d[register] & 0xffff0000) | result
            negative = bool(result & 0x8000)
            zero = result == 0
            if subtract:
                overflow = bool(((original ^ immediate) & (original ^ result)) & 0x8000)
                carry = original < immediate
            else:
                overflow = bool((~(original ^ immediate) & (original ^ result)) & 0x8000)
                carry = original + immediate > 0xffff
            self.ccr = ((0x10 if carry else 0) | (0x08 if negative else 0)
                        | (0x04 if zero else 0) | (0x02 if overflow else 0)
                        | (0x01 if carry else 0))
            mnemonic = "SUBQ.W #imm,Dn" if subtract else "ADDQ.W #imm,Dn"
        elif opcode & 0xfff8 in (0x0400, 0x0440, 0x0480, 0x0600, 0x0640, 0x0680, 0x0c00, 0x0c40, 0x0c80):
            register = opcode & 7
            size = (opcode >> 6) & 3
            bits = (8, 16, 32)[size]
            mask = (1 << bits) - 1
            sign = 1 << (bits - 1)
            immediate = self.fetch_word()
            if bits == 32:
                immediate = (immediate << 16) | self.fetch_word()
            immediate &= mask
            original = self.d[register] & mask
            operation = opcode & 0xff00
            compare = operation == 0x0c00
            if operation == 0x0600:
                result = (original + immediate) & mask
                carry = original + immediate > mask
                overflow = bool(~(original ^ immediate) & (original ^ result) & sign)
                name = "ADDI"
            else:
                result = (original - immediate) & mask
                carry = original < immediate
                overflow = bool((original ^ immediate) & (original ^ result) & sign)
                name = "CMPI" if compare else "SUBI"
            if not compare:
                self.d[register] = (self.d[register] & ~mask) | result
            extend = self.ccr & 0x10 if compare else (0x10 if carry else 0)
            self.ccr = (extend | (8 if result & sign else 0) | (4 if result == 0 else 0)
                        | (2 if overflow else 0) | (1 if carry else 0))
            mnemonic = name + "." + ("B", "W", "L")[size] + " #imm,Dn"
        elif opcode & 0xfff8 in (0x0000, 0x0040, 0x0080, 0x0200, 0x0240, 0x0280, 0x0a00, 0x0a40, 0x0a80):
            # ORI, ANDI, EORI immediate to Dn, all three operand sizes.
            register = opcode & 7
            size = (opcode >> 6) & 3
            bits = (8, 16, 32)[size]
            mask = (1 << bits) - 1
            immediate = self.fetch_word()
            if bits == 32:
                immediate = (immediate << 16) | self.fetch_word()
            immediate &= mask
            original = self.d[register] & mask
            operation = opcode & 0xff00
            if operation == 0x0000:
                result, name = original | immediate, "ORI"
            elif operation == 0x0200:
                result, name = original & immediate, "ANDI"
            else:
                result, name = original ^ immediate, "EORI"
            self.d[register] = (self.d[register] & ~mask) | result
            self._logic_flags(result, bits)
            mnemonic = name + "." + ("B", "W", "L")[size] + " #imm,Dn"
        elif opcode & 0xfff8 == 0x4880:
            # EXT.W Dn: sign-extend low byte into low word.
            register = opcode & 7
            byte = self.d[register] & 0xff
            result = byte | (0xff00 if byte & 0x80 else 0)
            self.d[register] = (self.d[register] & 0xffff0000) | result
            self._logic_flags(result, 16)
            mnemonic = "EXT.W Dn"
        elif opcode & 0xfff8 == 0x48c0:
            # EXT.L Dn: sign-extend low word into full longword.
            register = opcode & 7
            word = self.d[register] & 0xffff
            result = word | (0xffff0000 if word & 0x8000 else 0)
            self.d[register] = result
            self._logic_flags(result, 32)
            mnemonic = "EXT.L Dn"
        elif opcode & 0xfff8 == 0x4840:
            # SWAP Dn exchanges high and low 16-bit halves of Dn.
            register = opcode & 7
            original = self.d[register] & 0xffffffff
            result = ((original & 0xffff) << 16) | (original >> 16)
            self.d[register] = result
            self._logic_flags(result, 32)
            mnemonic = "SWAP Dn"
        elif opcode & 0xfff8 in (0x4600, 0x4640, 0x4680):
            # NOT.B/W/L Dn: complement selected operand, preserving upper bits.
            register = opcode & 7
            size_code = (opcode >> 6) & 3
            bits = (8, 16, 32)[size_code]
            mask = (1 << bits) - 1
            result = (~self.d[register]) & mask
            self.d[register] = (self.d[register] & ~mask) | result
            self._logic_flags(result, bits)
            mnemonic = ("NOT.B Dn", "NOT.W Dn", "NOT.L Dn")[size_code]
        elif opcode & 0xfff8 in (0x4400, 0x4440, 0x4480):
            # NEG.B/W/L Dn: 0 - operand, with X=C and V on min negative.
            register = opcode & 7
            size_code = (opcode >> 6) & 3
            bits = (8, 16, 32)[size_code]
            mask = (1 << bits) - 1
            original = self.d[register] & mask
            result = (-original) & mask
            self.d[register] = (self.d[register] & ~mask) | result
            carry = original != 0
            overflow = original == (1 << (bits - 1))
            self.ccr = ((0x10 if carry else 0) |
                        (0x08 if result & (1 << (bits - 1)) else 0) |
                        (0x04 if result == 0 else 0) |
                        (0x02 if overflow else 0) |
                        (0x01 if carry else 0))
            mnemonic = ("NEG.B Dn", "NEG.W Dn", "NEG.L Dn")[size_code]
        elif opcode & 0xfff8 == 0x4200:
            # CLR.B Dn: only low eight bits change, X is preserved.
            register = opcode & 7
            self.d[register] &= 0xffffff00
            self._logic_flags(0, 8)
            mnemonic = "CLR.B Dn"
        elif opcode & 0xfff8 == 0x4240:
            # CLR.W Dn: zero low 16 bits, preserve high 16 and X.
            self.d[opcode & 7] &= 0xffff0000
            self._logic_flags(0, 16)
            mnemonic = "CLR.W Dn"
        elif opcode & 0xfff8 == 0x4280:
            # CLR.L Dn: zero all 32 bits, preserve X.
            self.d[opcode & 7] = 0
            self._logic_flags(0, 32)
            mnemonic = "CLR.L Dn"
        elif opcode & 0xfff8 == 0x4a00:
            # TST.B Dn: only the low byte affects N/Z; preserve X and Dn.
            self._logic_flags(self.d[opcode & 7], 8)
            mnemonic = "TST.B Dn"
        elif opcode & 0xfff8 == 0x4a40:
            # TST.W Dn: update N/Z, clear V/C, preserve X; no data change.
            self._logic_flags(self.d[opcode & 7], 16)
            mnemonic = "TST.W Dn"
        elif opcode & 0xfff8 == 0x4a50:
            # TST.W (An): read through the reference bus, update CCR.
            # The address register and memory remain unchanged.
            value = self.read_word(self.a[opcode & 7])
            self._logic_flags(value, 16)
            mnemonic = "TST.W (An)"
        elif opcode & 0xfff8 == 0x4a90:
            # TST.L (An): read both big-endian words via the bus.
            # A real 68000 also requires an even address for long operands.
            address = self.a[opcode & 7]
            if address & 1:
                raise ValueError("unaligned 68000 long read")
            if not 0 <= address <= 0xfffffc:
                raise ValueError("long operand outside 24-bit reference bus")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self._logic_flags(value, 32)
            mnemonic = "TST.L (An)"
        elif opcode == 0x4a79:
            # TST.W (abs.l): fetch the address, read through the bus,
            # and update CCR without changing the memory word.
            address = (self.fetch_word() << 16) | self.fetch_word()
            value = self.read_word(address)
            self._logic_flags(value, 16)
            mnemonic = "TST.W (abs.l)"
        elif opcode == 0x4aB9:
            # TST.L (abs.l): two big-endian 16-bit reads; preserve memory.
            address = (self.fetch_word() << 16) | self.fetch_word()
            if not 0 <= address <= 0xfffffc:
                raise ValueError("long operand outside 24-bit reference bus")
            if address & 1:
                raise ValueError("unaligned 68000 long read")
            value = (self.read_word(address) << 16) | self.read_word(address + 2)
            self._logic_flags(value, 32)
            mnemonic = "TST.L (abs.l)"
        elif opcode & 0xfff8 == 0x4a80:
            # TST.L Dn: full 32-bit signed/zero test.
            self._logic_flags(self.d[opcode & 7], 32)
            mnemonic = "TST.L Dn"
        elif opcode & 0xfff8 == 0x0c40:
            # CMPI.W #imm,Dn
            register = opcode & 7
            immediate = self.fetch_word()
            self._compare_word(self.d[register], immediate)
            mnemonic = "CMPI.W #imm,Dn"
        elif opcode & 0xf1f8 == 0xb040:
            # CMP.W Dn,Dm: destination register in bits 11..9.
            destination = (opcode >> 9) & 7
            source = opcode & 7
            self._compare_word(self.d[destination], self.d[source])
            mnemonic = "CMP.W Dn,Dm"
        elif opcode & 0xff00 == 0x6100:
            # BSR.s / BSR.w (68000). Displacement is relative to PC
            # after opcode/extension fetch; push return PC as a longword.
            branch_base = self.pc  # 68000 branch displacement base: opcode address + 2.
            displacement = opcode & 0xff
            if displacement == 0:
                extension = self.fetch_word()
                displacement = extension - 65536 if extension & 0x8000 else extension
            elif displacement & 0x80:
                displacement -= 256
            target = (branch_base + displacement) & 0xffffffff
            if target & 1:
                raise ValueError("odd BSR target")
            self.push_long(self.pc)
            self.pc = target
            mnemonic = "BSR"
        elif opcode & 0xf0f8 == 0x50c0:
            # Scc Dn: write condition result to low byte; CCR unchanged.
            condition = (opcode >> 8) & 15
            register = opcode & 7
            value = 0xff if self._condition(condition) else 0
            self.d[register] = (self.d[register] & 0xffffff00) | value
            mnemonic = "Scc Dn"
        elif opcode & 0xf0f8 == 0x50c8:
            # DBcc Dn,disp16. Decrement only if condition is false.
            # Branch displacement is relative to extension-word address.
            condition = (opcode >> 8) & 15
            register = opcode & 7
            extension_address = self.pc
            extension = self.fetch_word()
            displacement = extension - 65536 if extension & 0x8000 else extension
            if not self._condition(condition):
                value = ((self.d[register] & 0xffff) - 1) & 0xffff
                target = (extension_address + displacement) & 0xffffffff
                if value != 0xffff and target & 1:
                    raise ValueError("odd DBcc target")
                self.d[register] = (self.d[register] & 0xffff0000) | value
                if value != 0xffff:
                    self.pc = target
            mnemonic = "DBcc"
        elif opcode & 0xf000 == 0x6000 and ((opcode >> 8) & 15) != 1:
            condition = (opcode >> 8) & 15
            branch_base = self.pc  # Opcode address + 2; also for word extensions.
            displacement = opcode & 0xff
            if displacement == 0:
                extension = self.fetch_word()
                displacement = extension - 65536 if extension & 0x8000 else extension
            elif displacement & 0x80:
                displacement -= 256
            if self._condition(condition):
                target = (branch_base + displacement) & 0xffffffff
                if target & 1:
                    raise ValueError("odd branch target")
                self.pc = target
            mnemonic = "BRA" if condition == 0 else "Bcc"
        else:
            # ALU/compare/shift/LEA/TST groups. A failed instruction leaves
            # registers, CCR and PC as they were before it was fetched.
            saved = (list(self.d), list(self.a), self.ccr)
            try:
                mnemonic = execute_alu_group(self, opcode)
            except BaseException:
                self.d[:], self.a[:], self.ccr = saved
                self.pc = before
                raise
            if mnemonic is None:
                self.pc = before
                raise NotImplementedError(f"68000 opcode 0x{opcode:04x} not implemented")
        return StepResult(before, opcode, self.pc, mnemonic)

    def run(self, max_steps: int = 100):
        if not 1 <= max_steps <= 100000:
            raise ValueError("max_steps must be 1..100000")
        return tuple(self.step() for _ in range(max_steps))
