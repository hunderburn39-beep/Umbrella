"""Reference bus controller connecting ROM/RAM to explicit DTACK handshakes.

Only the reference cartridge and work-RAM paths can acknowledge. VDP,
Z80 and IO require independent hardware models. Not a VA2 ASIC simulation.
"""
from bus import ReferenceBus
from bus_cycle import BusCycle, Phase, Request
from boot_bus import decode_region

class ReferenceBusController:
    def __init__(self, rom: bytes):
        self.memory = ReferenceBus(rom)
        self.cycle = BusCycle()
        self.response = None

    def begin(self, request: Request):
        if request.address & 1 or not (request.upper and request.lower):
            raise NotImplementedError("byte-lane transfers not yet modeled")
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
        acknowledged = self.cycle.sample(as_n=as_n, dtack_n=dtack_n,
                                         vdp_selected=int(region == "vdp-candidate"))
        if acknowledged:
            if req.read:
                self.response = self.memory.read_word(req.address)
            else:
                self.memory.write_word(req.address, req.data)
        return acknowledged

    def finish(self):
        acknowledged = self.cycle.release()
        result = self.response
        self.response = None
        return acknowledged, result
