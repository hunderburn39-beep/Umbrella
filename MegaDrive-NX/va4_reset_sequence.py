"""Offline VA4 reset sequencing diagnostic. Not connected to the Switch NRO.

Sources: Sega PAL-G maintenance manual; Charles MacDonald, SpritesMind
'Fun with reset signals' (2012). Analog RC is idealized; measured delays
must not be mistaken for a precise chip implementation.
"""
from dataclasses import dataclass
from va4_reset import ResetRC

PAL_MASTER_HZ = 53_203_424
CPU_DIVIDER = 7
VRES_LOW_VCLKS = 128
# VRES low pulse is approximately 16.8 microseconds, NOT milliseconds.
# The separate 12.8 ms figure is a reported cold-boot release delay.


@dataclass(frozen=True)
class ResetSnapshot:
    elapsed_s: float
    mres_high: bool
    sres_high: bool
    vres_high: bool


class VA4ResetSequence:
    def __init__(self, rc=None, vres_release_delay_s=0.0128):
        self.rc = rc or ResetRC()
        if vres_release_delay_s < 0:
            raise ValueError("VRES release delay must be nonnegative")
        # 12.8 ms is a reported cold-boot measurement, NOT the 128-cycle pulse.
        self.vres_release_delay_s = vres_release_delay_s

    @property
    def vclk_hz(self):
        return PAL_MASTER_HZ / CPU_DIVIDER

    @property
    def button_pulse_s(self):
        return VRES_LOW_VCLKS / self.vclk_hz

    def power_on(self, elapsed_s):
        if elapsed_s < 0:
            raise ValueError("Time cannot be negative")
        sres = self.rc.sres_released(elapsed_s)
        return ResetSnapshot(
            elapsed_s=elapsed_s,
            mres_high=elapsed_s > 0,
            sres_high=sres,
            vres_high=sres and elapsed_s >=
                self.rc.threshold_time_s + self.vres_release_delay_s,
        )

    def reset_button_vres(self, since_pulse_start_s):
        """True if VRES# is high. Pulse start is an external event.

        The latency from pressing the button to pulse start is intentionally
        not invented; it is hardware-dependent and was reported variable.
        """
        if since_pulse_start_s < 0:
            raise ValueError("Time cannot be negative")
        return since_pulse_start_s >= self.button_pulse_s


if __name__ == "__main__":
    seq = VA4ResetSequence()
    print("Nominal PAL VCLK (Hz):", seq.vclk_hz)
    print("VRES button low pulse (us):", seq.button_pulse_s * 1e6)
    print("Ideal RC SRES release (s):", seq.rc.threshold_time_s)
    print("Approximate modeled VRES release (s):",
          seq.rc.threshold_time_s + seq.vres_release_delay_s)
