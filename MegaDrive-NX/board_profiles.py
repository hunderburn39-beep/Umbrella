"""Board profile metadata for controlled comparisons. No hardware behavior changes."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BoardProfile:
    key: str
    description: str
    implementation: str
    chip_model_verified: bool

PROFILES = {
    "legacy": BoardProfile("legacy", "Existing pinned Nuked-MD wiring", "nuked-md", True),
    "md2-va4": BoardProfile("md2-va4", "Mega Drive II VA4 research target", "not-implemented", False),
}

def select_profile(name: str) -> BoardProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown board profile: {name}") from exc

def require_executable(name: str) -> BoardProfile:
    profile = select_profile(name)
    if profile.implementation == "not-implemented":
        raise RuntimeError("VA4 ASIC model is not implemented; refusing to label legacy simulation as VA4")
    return profile
