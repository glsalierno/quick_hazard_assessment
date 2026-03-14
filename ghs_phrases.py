"""
GHS Hazard (H) and Precautionary (P) phrase lookup.
Based on UN GHS Rev.10/11. Source: Wikipedia Module:GHS_phrases/data.
"""

from __future__ import annotations

# H-phrases: code -> phrase
GHS_H_PHRASES: dict[str, str] = {
    "H200": "Unstable explosive.",
    "H201": "Explosive; mass explosion hazard.",
    "H202": "Explosive; severe projection hazard.",
    "H203": "Explosive; fire, blast or projection hazard.",
    "H204": "Fire or projection hazard.",
    "H206": "Fire, blast or projection hazard: increased risk of explosion if desensitizing agent is reduced.",
    "H207": "Fire or projection hazard; increased risk of explosion if desensitizing agent is reduced.",
    "H208": "Fire hazard; increased risk of explosion if desensitizing agent is reduced.",
    "H209": "Explosive.",
    "H210": "Very explosive.",
    "H211": "May be sensitive.",
    "H220": "Extremely flammable gas.",
    "H221": "Flammable gas.",
    "H222": "Extremely flammable aerosol.",
    "H223": "Flammable aerosol.",
    "H224": "Extremely flammable liquid and vapour.",
    "H225": "Highly flammable liquid and vapour.",
    "H226": "Flammable liquid and vapour.",
    "H227": "Combustible liquid.",
    "H228": "Flammable solid.",
    "H229": "Pressurized container: may burst if heated.",
    "H230": "May react explosively even in the absence of air.",
    "H231": "May react explosively even in the absence of air at elevated pressure and/or temperature.",
    "H232": "May ignite spontaneously if exposed to air.",
    "H240": "Heating may cause an explosion.",
    "H241": "Heating may cause a fire or explosion.",
    "H242": "Heating may cause a fire.",
    "H250": "Catches fire spontaneously if exposed to air.",
    "H251": "Self-heating: may catch fire.",
    "H252": "Self-heating in large quantities: may catch fire.",
    "H260": "In contact with water releases flammable gases which may ignite spontaneously.",
    "H261": "In contact with water releases flammable gas.",
    "H270": "May cause or intensify fire: oxidizer.",
    "H271": "May cause fire or explosion: strong oxidizer.",
    "H272": "May intensify fire: oxidizer.",
    "H280": "Contains gas under pressure: may explode if heated.",
    "H281": "Contains refrigerated gas: may cause cryogenic burns or injury.",
    "H282": "Extremely flammable chemical under pressure: May explode if heated.",
    "H283": "Flammable chemical under pressure: May explode if heated.",
    "H284": "Chemical under pressure: May explode if heated.",
    "H290": "May be corrosive to metals.",
    "H300": "Fatal if swallowed.",
    "H300+H310": "Fatal if swallowed or in contact with skin.",
    "H300+H310+H330": "Fatal if swallowed, in contact with skin or if inhaled.",
    "H300+H330": "Fatal if swallowed or if inhaled.",
    "H301": "Toxic if swallowed.",
    "H301+H311": "Toxic if swallowed or in contact with skin.",
    "H301+H311+H331": "Toxic if swallowed, in contact with skin or if inhaled.",
    "H301+H331": "Toxic if swallowed or if inhaled.",
    "H302": "Harmful if swallowed.",
    "H302+H312": "Harmful if swallowed or in contact with skin.",
    "H302+H312+H332": "Harmful if swallowed, in contact with skin or if inhaled.",
    "H302+H332": "Harmful if swallowed or inhaled.",
    "H303": "May be harmful if swallowed.",
    "H303+H313": "May be harmful if swallowed or in contact with skin.",
    "H303+H313+H333": "May be harmful if swallowed, in contact with skin or if inhaled.",
    "H303+H333": "May be harmful if swallowed or if inhaled.",
    "H304": "May be fatal if swallowed and enters airways.",
    "H305": "May be harmful if swallowed and enters airways.",
    "H310": "Fatal in contact with skin.",
    "H310+H330": "Fatal in contact with skin or if inhaled.",
    "H311": "Toxic in contact with skin.",
    "H311+H331": "Toxic in contact with skin or if inhaled.",
    "H312": "Harmful in contact with skin.",
    "H312+H332": "Harmful in contact with skin or if inhaled.",
    "H313": "May be harmful in contact with skin.",
    "H313+H333": "May be harmful in contact with skin or if inhaled.",
    "H314": "Causes severe skin burns and eye damage.",
    "H315": "Causes skin irritation.",
    "H315+H319": "Causes skin irritation and serious eye irritation.",
    "H315+H320": "Causes skin and eye irritation.",
    "H316": "Causes mild skin irritation.",
    "H317": "May cause an allergic skin reaction.",
    "H318": "Causes serious eye damage.",
    "H319": "Causes serious eye irritation.",
    "H320": "Causes eye irritation.",
    "H330": "Fatal if inhaled.",
    "H331": "Toxic if inhaled.",
    "H332": "Harmful if inhaled.",
    "H333": "May be harmful if inhaled.",
    "H334": "May cause allergy or asthma symptoms or breathing difficulties if inhaled.",
    "H335": "May cause respiratory irritation.",
    "H336": "May cause drowsiness or dizziness.",
    "H340": "May cause genetic defects.",
    "H341": "Suspected of causing genetic defects.",
    "H350": "May cause cancer.",
    "H350i": "May cause cancer by inhalation.",
    "H351": "Suspected of causing cancer.",
    "H360": "May damage fertility or the unborn child.",
    "H360D": "May damage the unborn child.",
    "H360Df": "May damage the unborn child. Suspected of damaging fertility.",
    "H360F": "May damage fertility.",
    "H360FD": "May damage fertility. May damage the unborn child.",
    "H360Fd": "May damage fertility. Suspected of damaging the unborn child.",
    "H361": "Suspected of damaging fertility or the unborn child.",
    "H361d": "Suspected of damaging the unborn child.",
    "H361f": "Suspected of damaging fertility.",
    "H361fd": "Suspected of damaging fertility. Suspected of damaging the unborn child.",
    "H362": "May cause harm to breast-fed children.",
    "H370": "Causes damage to organs.",
    "H371": "May cause damage to organs.",
    "H372": "Causes damage to organs through prolonged or repeated exposure.",
    "H373": "May cause damage to organs through prolonged or repeated exposure.",
    "H400": "Very toxic to aquatic life.",
    "H401": "Toxic to aquatic life.",
    "H402": "Harmful to aquatic life.",
    "H410": "Very toxic to aquatic life with long lasting effects.",
    "H411": "Toxic to aquatic life with long lasting effects.",
    "H412": "Harmful to aquatic life with long lasting effects.",
    "H413": "May cause long lasting harmful effects to aquatic life.",
    "H420": "Harms public health and the environment by destroying ozone in the upper atmosphere.",
    "H421": "Harms public health and the environment by contributing to global warming.",
}

# P-phrases: code -> phrase
GHS_P_PHRASES: dict[str, str] = {
    "P101": "If medical advice is needed, have product container or label at hand.",
    "P102": "Keep out of reach of children.",
    "P103": "Read carefully and follow all instructions.",
    "P201": "Obtain special instructions before use.",
    "P202": "Do not handle until all safety precautions have been read and understood.",
    "P203": "Obtain, read and follow all safety instructions before use.",
    "P210": "Keep away from heat, hot surfaces, sparks, open flames and other ignition sources. No smoking.",
    "P211": "Do not spray on an open flame or other ignition source.",
    "P212": "Avoid heating under confinement or reduction of the desensitized agent.",
    "P220": "Keep away from clothing and other combustible materials.",
    "P222": "Do not allow contact with air.",
    "P223": "Do not allow contact with water.",
    "P230": "Keep diluted with ...",
    "P231": "Handle and store contents under inert gas/...",
    "P231+P232": "Handle and store contents under inert gas/... Protect from moisture.",
    "P232": "Protect from moisture.",
    "P233": "Keep container tightly closed.",
    "P234": "Keep only in original container.",
    "P235": "Keep cool.",
    "P240": "Ground and bond container and receiving equipment.",
    "P241": "Use explosion-proof [electrical/ventilating/lighting/...] equipment.",
    "P242": "Use non-sparking tools.",
    "P243": "Take action to prevent static discharges.",
    "P244": "Keep valves and fittings free from oil and grease.",
    "P250": "Do not subject to grinding/shock/friction/...",
    "P251": "Do not pierce or burn, even after use.",
    "P260": "Do not breathe dust/fume/gas/mist/vapours/spray.",
    "P261": "Avoid breathing dust/fume/gas/mist/vapours/spray.",
    "P262": "Do not get in eyes, on skin, or on clothing.",
    "P263": "Avoid contact during pregnancy and while nursing.",
    "P264": "Wash hands [and ...] thoroughly after handling.",
    "P264+P265": "Wash hands [and ...] thoroughly after handling. Do not touch eyes.",
    "P265": "Do not touch eyes.",
    "P270": "Do not eat, drink or smoke when using this product.",
    "P271": "Use only outdoors or with adequate ventilation.",
    "P272": "Contaminated work clothing should not be allowed out of the workplace.",
    "P273": "Avoid release to the environment.",
    "P280": "Wear protective gloves/protective clothing/eye protection/face protection/hearing protection/...",
    "P282": "Wear cold insulating gloves and either face shield or eye protection.",
    "P283": "Wear fire resistant or flame-retardant clothing.",
    "P284": "In case of inadequate ventilation wear respiratory protection.",
    "P301": "IF SWALLOWED:",
    "P301+P310": "IF SWALLOWED: Immediately call a POISON CENTER or doctor/physician.",
    "P301+P312": "IF SWALLOWED: Call a POISON CENTER or doctor/physician if you feel unwell.",
    "P301+P316": "IF SWALLOWED: Get emergency medical help immediately.",
    "P301+P330+P331": "IF SWALLOWED: Rinse mouth. Do NOT induce vomiting.",
    "P302": "IF ON SKIN:",
    "P302+P334": "IF ON SKIN: Immerse in cool water or wrap in wet bandages.",
    "P302+P335+P334": "IF ON SKIN: Brush off loose particles from skin and immerse in cool water [or wrap in wet bandages].",
    "P302+P352": "IF ON SKIN: Wash with plenty of water/...",
    "P302+P361+P354": "IF ON SKIN: Take off immediately all contaminated clothing. Immediately rinse with water for several minutes.",
    "P303": "IF ON SKIN (or hair):",
    "P303+P361+P353": "IF ON SKIN (or hair): Remove/Take off immediately all contaminated clothing. Rinse skin with water [or shower].",
    "P304": "IF INHALED:",
    "P304+P340": "IF INHALED: Remove person to fresh air and keep comfortable for breathing.",
    "P305": "IF IN EYES:",
    "P305+P351+P338": "IF IN EYES: Rinse continuously with water for several minutes. Remove contact lenses, if present and easy to do. Continue rinsing.",
    "P306": "IF ON CLOTHING:",
    "P306+P360": "IF ON CLOTHING: Rinse immediately contaminated clothing and skin with plenty of water before removing clothes.",
    "P308": "IF exposed or concerned:",
    "P308+P316": "IF exposed or concerned: Get emergency medical help immediately.",
    "P310": "Immediately call a POISON CENTER or doctor/physician.",
    "P311": "Call a POISON CENTER or doctor/physician.",
    "P312": "Call a POISON CENTER or doctor/physician if you feel unwell.",
    "P313": "Get medical advice/attention.",
    "P314": "Get medical advice/attention if you feel unwell.",
    "P315": "Get immediate medical advice/attention.",
    "P316": "Get emergency medical help immediately.",
    "P317": "Get medical help.",
    "P318": "If exposed or concerned, get medical advice.",
    "P319": "Get medical help if you feel unwell.",
    "P320": "Specific treatment is urgent (see information on this label and safety data sheet).",
    "P321": "Specific treatment (see information on this label and safety data sheet).",
    "P330": "Rinse mouth.",
    "P331": "Do NOT induce vomiting.",
    "P332": "If skin irritation occurs:",
    "P332+P317": "If skin irritation occurs: Get medical help.",
    "P333": "If skin irritation or a rash occurs:",
    "P333+P317": "If skin irritation or rash occurs: Get medical help.",
    "P334": "Immerse in cool water [or wrap in wet bandages].",
    "P335": "Brush off loose particles from skin.",
    "P336": "Thaw frosted parts with lukewarm water. Do not rub affected areas.",
    "P336+P317": "Immediately thaw frosted parts with lukewarm water. Do not rub affected area. Get medical help.",
    "P337": "If eye irritation persists:",
    "P337+P317": "If eye irritation persists: Get medical help.",
    "P338": "Remove contact lenses if present and easy to do. Continue rinsing.",
    "P340": "Remove person to fresh air and keep comfortable for breathing.",
    "P342": "If experiencing respiratory symptoms:",
    "P342+P316": "If experiencing respiratory symptoms: Get emergency medical help immediately.",
    "P351": "Rinse cautiously with water for several minutes.",
    "P352": "Wash with plenty of water/...",
    "P353": "Rinse skin with water [or shower].",
    "P354": "Immediately rinse with water for several minutes.",
    "P360": "Rinse immediately contaminated clothing and skin with plenty of water before removing clothes.",
    "P361": "Take off immediately all contaminated clothing.",
    "P361+P364": "Take off immediately all contaminated clothing and wash it before reuse.",
    "P362": "Take off contaminated clothing.",
    "P362+P364": "Take off contaminated clothing and wash it before reuse.",
    "P363": "Wash contaminated clothing before reuse.",
    "P364": "And wash it before reuse.",
    "P370": "In case of fire:",
    "P370+P378": "In case of fire: Use ... to extinguish.",
    "P370+P380": "In case of fire: Evacuate area.",
    "P370+P380+P375": "In case of fire: Evacuate area. Fight fire remotely due to the risk of explosion.",
    "P371": "In case of major fire and large quantities:",
    "P372": "Explosion risk.",
    "P373": "DO NOT fight fire when fire reaches explosives.",
    "P375": "Fight fire remotely due to the risk of explosion.",
    "P376": "Stop leak if safe to do so.",
    "P377": "Leaking gas fire: Do not extinguish, unless leak can be stopped safely.",
    "P378": "Use ... to extinguish.",
    "P380": "Evacuate area.",
    "P381": "In case of leakage, eliminate all ignition sources.",
    "P390": "Absorb spillage to prevent material damage.",
    "P391": "Collect spillage.",
    "P401": "Store in accordance with ...",
    "P402": "Store in a dry place.",
    "P402+P404": "Store in a dry place. Store in a closed container.",
    "P403": "Store in a well-ventilated place.",
    "P403+P233": "Store in a well-ventilated place. Keep container tightly closed.",
    "P403+P235": "Store in a well-ventilated place. Keep cool.",
    "P404": "Store in a closed container.",
    "P405": "Store locked up.",
    "P406": "Store in a corrosion resistant/... container with a resistant inner liner.",
    "P410": "Protect from sunlight.",
    "P410+P403": "Protect from sunlight. Store in a well-ventilated place.",
    "P411": "Store at temperatures not exceeding ... °C/... °F.",
    "P412": "Do not expose to temperatures exceeding 50 °C/122 °F.",
    "P413": "Store bulk masses greater than ... kg/... lbs at temperatures not exceeding ... °C/... °F.",
    "P420": "Store separately.",
    "P501": "Dispose of contents/container to ...",
    "P502": "Refer to manufacturer or supplier for information on recovery or recycling.",
}


def get_h_phrase(code: str) -> str:
    """Return H-code phrase, or 'code: (phrase not found)' if unknown."""
    if not code:
        return ""
    c = code.strip()
    return GHS_H_PHRASES.get(c, f"{c}: (phrase not found)")


def get_p_phrase(code: str) -> str:
    """Return P-code phrase, or 'code: (phrase not found)' if unknown."""
    if not code:
        return ""
    c = code.strip()
    return GHS_P_PHRASES.get(c, f"{c}: (phrase not found)")


def expand_h_codes_with_phrases(codes: list[str] | None) -> list[str]:
    """Convert ['H302','H312'] -> ['H302: Harmful if swallowed', 'H312: Harmful in contact with skin']."""
    if not codes:
        return []
    out = []
    for c in codes:
        c = (c or "").strip()
        if c:
            out.append(f"{c}: {get_h_phrase(c)}")
    return out


def expand_p_codes_with_phrases(codes: list[str] | None) -> list[str]:
    """Convert ['P264','P280'] -> ['P264: Wash hands...', 'P280: Wear protective gloves...']."""
    if not codes:
        return []
    out = []
    for c in codes:
        c = (c or "").strip()
        if c:
            out.append(f"{c}: {get_p_phrase(c)}")
    return out


def expand_ghs_pipe_separated(codes_str: str, kind: str = "H") -> list[str]:
    """
    Parse pipe-separated codes (e.g. 'H302|H312|H332') and return list with phrases.
    kind: 'H' for hazard, 'P' for precautionary.
    """
    if not codes_str:
        return []
    codes = [x.strip() for x in str(codes_str).split("|") if x.strip()]
    if kind.upper() == "H":
        return expand_h_codes_with_phrases(codes)
    return expand_p_codes_with_phrases(codes)
