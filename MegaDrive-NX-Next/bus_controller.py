"""Reference bus controller connecting ROM/RAM to explicit DTACK handshakes.

Only the reference cartridge and work-RAM paths can acknowledge. VDP,
Z80 and IO require independent hardware models. Not a VA2 ASIC simulation.
"""
from bus import ReferenceBus
from bus_cycle import BusCycle, Phase, Request
from boot_bus import decode_region
from z80_bridge import Z80Bridge
from z80_control import BUSREQ_ADDR, RESET_ADDR
from vdp_ports import VDPPorts, CONTROL_PORT

class ReferenceBusController:
    def __init__(self, rom: bytes):
        self.memory = ReferenceBus(rom)
        self.z80 = Z80Bridge()
        self.vdp = VDPPorts()
        self.cycle = BusCycle()
        self.response = None
        self.completed_reads = 0
        self.completed_writes = 0
        self.completed_vdp_reads = 0
        self.completed_vdp_writes = 0

    def diagnostic_bus_counts(self):
        """Completed acknowledged transfers only; not elapsed bus cycles."""
        return (self.completed_reads, self.completed_writes,
                self.completed_vdp_reads, self.completed_vdp_writes)

    def begin(self, request: Request):
        if request.address & 1 and request.upper:
            raise ValueError("invalid upper byte lane")
        if not (request.upper and request.lower) and decode_region(request.address) not in ("cartridge", "work-ram-mirror"):
            raise NotImplementedError("peripheral byte lanes not yet modeled")
        self.cycle.start(request)
        self.response = None

    def clock(self, *, as_n=0, external_dtack_n=1):
        """Advance a sampled bus phase. No invented acknowledgement for VDP."""
        if self.cycle.phase is Phase.IDLE:
            raise RuntimeError("no pending transaction")
        req = self.cycle.request
        region = decode_region(req.address)
        if region in ("cartridge", "work-ram-mirror"):
            # The reference RAM/ROM responder is immediate. This is a test
            # convention, not a claim about physical VA2 wait-state timing.
            dtack_n = 0
        else:
            dtack_n = external_dtack_n
            if dtack_n == 0:
                raise NotImplementedError(
                    f"{region} responder not implemented; cannot complete transfer"
                )
        was_acknowledged = self.cycle.phase is Phase.ACKNOWLEDGED
        acknowledged = self.cycle.sample(as_n=as_n, dtack_n=dtack_n,
                                         vdp_selected=int(region == "vdp-candidate"))
        if acknowledged and not was_acknowledged:
            if req.read:
                word = self.memory.read_word(req.address & ~1)
                self.response = word & ((0xff00 if req.upper else 0) | (0xff if req.lower else 0))
                self.completed_reads += 1
            else:
                address = req.address & ~1
                mask = (0xff00 if req.upper else 0) | (0xff if req.lower else 0)
                value = req.data
                if mask != 0xffff:
                    value = (self.memory.read_word(address) & ~mask) | (value & mask)
                self.memory.write_word(address, value)
                self.completed_writes += 1
        return acknowledged

    def clock_vdp_reference(self, *, as_n=0, ready=False):
        """Opt-in, externally gated reference VDP transaction.

        The caller supplies ready; this is not a measured VA2 DTACK source.
        Only canonical 16-bit VDP data/control ports are modeled.
        """
        if self.cycle.phase is Phase.IDLE:
            raise RuntimeError("no pending transaction")
        req = self.cycle.request
        if req.address not in (0xc00000, CONTROL_PORT):
            raise ValueError("not a supported canonical VDP port")
        if not isinstance(ready, bool):
            raise ValueError("ready must be boolean")
        if as_n != 0:
            raise RuntimeError("address strobe inactive during cycle")
        if self.cycle.phase is Phase.ACKNOWLEDGED:
            return self.cycle.sample(as_n=as_n, dtack_n=0, vdp_selected=1)
        if not ready:
            return self.cycle.sample(as_n=as_n, dtack_n=1, vdp_selected=1)
        # Validate supported operation before acknowledging, avoiding
        # successful bus completion for unimplemented peripheral behavior.
        if req.read and req.address == CONTROL_PORT:
            raise NotImplementedError("CPU-visible VDP status requires verified timing/FIFO")
        if req.read and req.address == 0xc00000:
            value = self.vdp.read_data()
        elif req.address == CONTROL_PORT:
            self.vdp.write_control(req.data)
            value = None
        else:
            self.vdp.write_data(req.data)
            value = None
        acknowledged = self.cycle.sample(as_n=as_n, dtack_n=0, vdp_selected=1)
        if acknowledged:
            self.response = value
            if req.read:
                self.completed_reads += 1
                self.completed_vdp_reads += 1
            else:
                self.completed_writes += 1
                self.completed_vdp_writes += 1
        return acknowledged

    def finish(self):
        acknowledged = self.cycle.release()
        result = self.response
        self.response = None
        return acknowledged, result

    def write_z80_control(self, address: int, value: int):
        """Reference register operation, not a timed 68000 bus transaction."""
        if self.cycle.phase is not Phase.IDLE:
            raise RuntimeError("cannot bypass an active bus cycle")
        if address not in (BUSREQ_ADDR, RESET_ADDR):
            raise ValueError("not a Z80 control register")
        self.z80.write_control_word(address, value)

    def observe_z80_grant(self, granted: bool):
        """Record an externally supplied bus grant; never infer one."""
        self.z80.observe_grant(granted)

    def read_z80_byte(self, address: int) -> int:
        """Explicit byte path until physical 68000 lane wiring is verified."""
        if self.cycle.phase is not Phase.IDLE:
            raise RuntimeError("cannot bypass an active bus cycle")
        return self.z80.read_byte(address)

    def write_z80_byte(self, address: int, value: int):
        if self.cycle.phase is not Phase.IDLE:
            raise RuntimeError("cannot bypass an active bus cycle")
        self.z80.write_byte(address, value)

    def diagnostic_read_vdp_status(self, address: int) -> int:
        """Inspect diagnostic status through a bus-controller API.

        This is NOT a 68000 read cycle: it never asserts DTACK and does
        not replace VDPPorts.read_status() or model FIFO/timing.
        """
        if self.cycle.phase is not Phase.IDLE:
            raise RuntimeError("cannot bypass an active bus cycle")
        if address != CONTROL_PORT:
            raise ValueError("only canonical VDP control/status port supported")
        return self.vdp.diagnostic_status_word()

    def stage_vdp_control_word(self, address: int, value: int) -> str:
        """Untimed test-only staging, not a completed 68000 bus transaction."""
        if self.cycle.phase is not Phase.IDLE:
            raise RuntimeError("cannot bypass an active bus cycle")
        if address != CONTROL_PORT:
            raise ValueError("only canonical VDP control port supported")
        return self.vdp.write_control(value)
