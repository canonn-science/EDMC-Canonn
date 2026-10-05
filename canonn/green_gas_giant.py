"""Green Gas Giant predictor.

Speculative reconstruction of the community "seven-layer ladder" model for
why certain gas giants render green in the Codex. The model was found by
CMDR Regza (with AI assistance), following a hint from Dr. K. Ross and
CMDR Arcanic. It is a reverse-engineered reconstruction, not the game's own
code - see https://github.com/canonn-science/EDMC-Canonn/issues/222.

Class rules are kept as data (``RULES`` below) rather than branching code so
they can be corrected as new in-game results come in, without touching the
algorithm itself.
"""

import math
import struct

M_EARTH_KG = 5.9722e24
UNCAPPED_TOLERANCE_K = 0.0002

CONFIRMED = "confirmed"
STATED = "stated"
DERIVED = "derived"

GREEN = "GREEN"
GREEN_LOW_CONFIDENCE = "GREEN_LOW_CONFIDENCE"
NOT_GREEN = "NOT_GREEN"
UNPREDICTABLE = "UNPREDICTABLE"


def f32(value):
    """Round a python float through a 32-bit float, like the game does."""
    return struct.unpack("f", struct.pack("f", value))[0]


def classify(planet_class):
    """Map a PlanetClass/subType string onto one of our rule-table keys."""
    s = (planet_class or "").lower().replace("-", " ")
    if "helium" in s:
        return "helium"
    if "water giant" in s:
        return "water_giant"
    if "ammonia" in s and "life" in s:
        return "ammonia_life"
    if "water" in s and "life" in s:
        return "water_life"
    if "class v" in s:
        return "class5"
    if "class iv" in s:
        return "class4"
    if "class iii" in s:
        return "class3"
    if "class ii" in s:
        return "class2"
    if "class i" in s:
        return "class1"
    return None


# Real Codex entries (english_name values from data/codex_name_ref.json,
# hud_category "Tourist") that supersede a prediction for the body once the
# commander has actually found them in-game.
CODEX_NAMES = {
    "class1": ["Green Class I Gas Giant"],
    "class2": ["Green Class II Gas Giant"],
    "class3": ["Green Class III Gas Giant"],
    "class4": ["Green Class IV Gas Giant"],
    "class5": ["Green Class V Gas Giant"],
    "water_giant": ["Green Water Giant"],
    "ammonia_life": ["Green Gas Giant with Ammonia Life"],
    # Per the design doc, green water-life giants don't get their own Codex
    # slot in-game - it's taken by the ammonia-life entry - so check both.
    "water_life": ["Green Gas Giant with Ammonia Life", "Green Gas Giant"],
}

# Every real Codex "Green ..." name, regardless of class - used to blanket
# -suppress predictions for the whole system once any one of them has
# actually been found, since a confirmed green gas giant in a system means
# the commander can just go and check the rest visually.
ALL_CODEX_NAMES = sorted({name for names in CODEX_NAMES.values() for name in names})

# Candidate label used for the speculative Tourist POI, mirroring the real
# Codex names above but with a trailing "?" to flag it as a prediction.
CANDIDATE_LABELS = {
    "class1": "Green Class I Gas Giant?",
    "class3": "Green Class III Gas Giant?",
    "class4": "Green Class IV Gas Giant?",
    "water_giant": "Green Water Giant?",
    "ammonia_life": "Green Gas Giant with Ammonia Life?",
    "water_life": "Green Gas Giant with Water Based Life?",
}

# Each rule applies to a (class_key, [t_min, t_max)) band. ``nudged`` ranges
# are known to be unpredictable (the game nudges the bottom rung by some
# small, apparently-random offset) - we deliberately report UNPREDICTABLE
# instead of guessing. A band simply absent from this table (e.g. Class II
# at any temperature, or Class III 415-490 K) is just as unpredictable.
RULES = [
    # Class I - predictable outside the ~80-113 K nudge window.
    dict(cls="class1", t_min=None, t_max=80, ceiling=340, min_step=None,
         borders=[115, 250, 270], confidence=CONFIRMED),
    dict(cls="class1", t_min=80, t_max=113, nudged=True),
    dict(cls="class1", t_min=113, t_max=330, ceiling=340, min_step=None,
         borders=[115, 250, 270], confidence=CONFIRMED),

    # Gas giant with ammonia-based life - same nudge window as Class I.
    dict(cls="ammonia_life", t_min=None, t_max=80, ceiling=340, min_step=None,
         borders=[175, 250, 270], confidence=CONFIRMED),
    dict(cls="ammonia_life", t_min=80, t_max=113, nudged=True),
    dict(cls="ammonia_life", t_min=113, t_max=None, ceiling=340, min_step=None,
         borders=[175, 250, 270], confidence=CONFIRMED),

    # Gas giant with water-based life.
    dict(cls="water_life", t_min=150, t_max=250, ceiling=340, min_step=None,
         borders=[210, 270], confidence=CONFIRMED),

    # Water giant - only the catalogued 158 K case is understood.
    dict(cls="water_giant", t_min=157.999, t_max=158.001, ceiling=340,
         min_step=None, borders=[210], confidence=CONFIRMED),

    # Class II - nudged at every catalogued temperature, no known pattern.
    dict(cls="class2", t_min=None, t_max=None, nudged=True),

    # Class III.
    dict(cls="class3", t_min=None, t_max=370, nudged=True),
    dict(cls="class3", t_min=370, t_max=370.0001, ceiling=None, min_step=None,
         borders=[370], confidence=CONFIRMED),
    dict(cls="class3", t_min=370.0001, t_max=415, nudged=True),
    # 415-490 K: a genuine gap - no ceiling/step/borders are known.
    dict(cls="class3", t_min=490, t_max=680, ceiling=700, min_step=30,
         borders=[700], confidence=CONFIRMED),
    dict(cls="class3", t_min=680, t_max=900, ceiling=1200, min_step=30,
         borders=[700, 900], confidence=DERIVED),
    dict(cls="class3", t_min=900, t_max=None, ceiling=1500, min_step=30,
         borders=[1400], confidence=DERIVED),

    # Class IV - only confirmed at/above 900 K.
    dict(cls="class4", t_min=900, t_max=None, ceiling=1500, min_step=None,
         borders=[900, 1400], confidence=CONFIRMED),

    # Class V, helium-rich/helium gas giants - no catalogued examples.
    dict(cls="class5", t_min=None, t_max=None, nudged=True),
    dict(cls="helium", t_min=None, t_max=None, nudged=True),
]


def _in_range(t, t_min, t_max):
    if t_min is not None and t < t_min:
        return False
    if t_max is not None and t >= t_max:
        return False
    return True


def find_rule(class_key, temperature):
    if class_key is None:
        return None
    for rule in RULES:
        if rule["cls"] == class_key and _in_range(temperature, rule.get("t_min"), rule.get("t_max")):
            return rule
    return None


def bulk_density(mass_em, radius_m):
    """kg/m^3. Returns None if mass/radius are missing or non-physical."""
    if not mass_em or not radius_m or radius_m <= 0:
        return None
    mass_kg = float(mass_em) * M_EARTH_KG
    volume_m3 = (4.0 / 3.0) * math.pi * (float(radius_m) ** 3)
    return mass_kg / volume_m3


def ladder_depth(temperature, density_kgm3):
    return (5.0 / 9.0 * 1300.0) * ((temperature / 1300.0) ** 1.2) * (density_kgm3 ** 0.2)


def predict(planet_class, surface_temperature, mass_em, radius_m, precision="full"):
    """Predict whether a gas giant renders green.

    Returns a dict with at least a ``verdict`` key (one of GREEN,
    GREEN_LOW_CONFIDENCE, NOT_GREEN, UNPREDICTABLE) plus diagnostics useful
    for logging/regression testing.
    """
    result = {
        "verdict": UNPREDICTABLE,
        "planet_class": planet_class,
        "surface_temperature": surface_temperature,
        "precision": precision,
    }

    if surface_temperature is None:
        return result

    t = float(surface_temperature)
    class_key = classify(planet_class)
    rule = find_rule(class_key, t)
    result["class_key"] = class_key

    if rule is None or rule.get("nudged"):
        return result

    result["rule_confidence"] = rule["confidence"]

    density = bulk_density(mass_em, radius_m)
    if density is None:
        # Can't compute the ladder without mass/radius.
        return result

    depth = ladder_depth(t, density)
    ceiling = rule.get("ceiling")
    min_step = rule.get("min_step")
    borders = rule.get("borders", [])

    capped = ceiling is not None and (t + depth) >= ceiling
    top = ceiling if capped else (t + depth)

    result.update(density=density, depth=depth, ceiling=ceiling, capped=capped, top=top)

    exact_path = capped or min_step is not None

    if exact_path:
        t32 = f32(t)
        top32 = f32(top)
        seven32 = f32(7.0)
        step = f32(f32(top32 - t32) / seven32)
        if min_step is not None:
            step = max(step, f32(min_step))

        rungs = []
        hit = None
        for k in range(7):
            rung = f32(t32 + f32(f32(k) * step))
            rungs.append(rung)
            for border in borders:
                if rung == f32(border):
                    hit = (k + 1, border, 0.0)

        result["step"] = step
        result["rungs"] = rungs
    else:
        step = depth / 7.0
        rungs = [t + k * step for k in range(7)]
        hit = None
        best_miss = None
        for k, rung in enumerate(rungs):
            for border in borders:
                residual = abs(rung - border)
                if best_miss is None or residual < best_miss:
                    best_miss = residual
                if residual <= UNCAPPED_TOLERANCE_K and hit is None:
                    hit = (k + 1, border, residual)

        result["step"] = step
        result["rungs"] = rungs
        result["near_miss_k"] = best_miss

    if hit is None:
        result["verdict"] = NOT_GREEN
        return result

    rung_number, border, residual = hit
    result.update(hit_rung=rung_number, hit_border=border, residual=residual)

    low_confidence = (
        rule["confidence"] in (STATED, DERIVED)
        or precision != "full"
    )
    result["verdict"] = GREEN_LOW_CONFIDENCE if low_confidence else GREEN
    return result
