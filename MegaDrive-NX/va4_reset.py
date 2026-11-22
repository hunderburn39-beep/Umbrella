"""VA4 reset-circuit reference model. Offline diagnostic, not Switch runtime.

Approximate first-order RC response, ideal threshold comparator. This does not
claim transistor-level or exact hardware pulse timing. Units: ohms, farads, volts.
"""
from dataclasses import dataclass
from math import exp, log


@dataclass(frozen=True)
class ResetRC:
    resistance_ohm: float = 47_000.0
    capacitance_f: float = 10e-6
    supply_v: float = 5.0
    threshold_v: float = 2.0

    def __post_init__(self):
        if self.resistance_ohm <= 0 or self.capacitance_f <= 0:
            raise ValueError("R and C must be positive")
        if not 0 < self.threshold_v < self.supply_v:
            raise ValueError("Threshold must lie between 0 and supply")

    @property
    def tau_s(self) -> float:
        return self.resistance_ohm * self.capacitance_f

    @property
    def threshold_time_s(self) -> float:
        return -self.tau_s * log(1 - self.threshold_v / self.supply_v)

    def capacitor_voltage(self, elapsed_s: float) -> float:
        if elapsed_s < 0:
            raise ValueError("Time cannot be negative")
        return self.supply_v * (1 - exp(-elapsed_s / self.tau_s))

    def sres_released(self, elapsed_s: float) -> bool:
        return self.capacitor_voltage(elapsed_s) >= self.threshold_v


if __name__ == "__main__":
    model = ResetRC()
    print(f"VA4 nominal RC tau: {model.tau_s:.6f} s")
    print(f"Ideal 2V crossing: {model.threshold_time_s:.6f} s")
    print("This is not a measured board boot time.")
