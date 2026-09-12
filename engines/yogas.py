"""Classical Vedic Astrological Yogas and Doshas Detection Engine.

Implements BPHS (Brihat Parashara Hora Shastra) rules for:
- 5 Pancha Mahapurusha Yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasa)
- 15+ Major Raja, Dhana, and Auspicious Yogas (Gajakesari, Budhaditya,
  Dharma-Karmadhipati, Kendra-Trikona, Neechabhanga, Vipareeta, Amala, Parivartana, etc.)
- Solar and Lunar Stream Yogas (Veshi, Vosi, Ubhayachari, Sunapha, Anapha, Durudhura)
- 6 Major Doshas with classical cancellation (Apavada) logic:
  - Manglik / Kuja Dosha (with 8 cancellation conditions)
  - Kaal Sarp Dosha (all 12 types: Anant to Sheshnag, Purna vs. Anshik)
  - Kemadruma Yoga (with Kendra cancellation checks)
  - Guru Chandal Dosha
  - Grahan (Eclipse) Dosha
  - Visha (Shani-Chandra) Dosha
  - Sade Sati status (Rising, Peak, Setting, Dhaiya, Inactive)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.constants import PlanetEnum, ZODIAC_SIGNS
from schemas.models import UnifiedChartData


class YogaNature(str, Enum):
    AUSPICIOUS = "Auspicious"
    RAJA = "Raja"
    DHANA = "Dhana"
    MAHAPURUSHA = "Mahapurusha"
    NEUTRAL = "Neutral"
    DOSHA = "Dosha"


class YogaItem(BaseModel):
    """Represents a single detected or analyzed astrological yoga/dosha."""
    id: str
    name: str
    sanskrit_name: str
    nature: YogaNature
    category: str
    is_active: bool = True
    intensity: str = "Strong"  # "Strong", "Moderate", "Mild", "Cancelled"
    planets_involved: List[str] = Field(default_factory=list)
    houses_involved: List[int] = Field(default_factory=list)
    description: str
    classical_effects: str
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None


class YogasSummary(BaseModel):
    """Aggregate statistics for yogas detected in a birth chart."""
    total_yogas: int = 0
    auspicious_count: int = 0
    raja_count: int = 0
    dhana_count: int = 0
    mahapurusha_count: int = 0
    doshas_count: int = 0
    sade_sati_status: str = "Inactive"
    kuja_dosha_status: str = "Absent"
    kaal_sarp_status: str = "Absent"


class YogaEvaluationReport(BaseModel):
    """Complete evaluation report containing summary and all evaluated yogas."""
    summary: YogasSummary
    yogas: List[YogaItem] = Field(default_factory=list)


# =============================================================================
# Classical Dignity Tables (BPHS Standards)
# =============================================================================

EXALTATION_SIGNS: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 1,       # Aries / Mesha
    PlanetEnum.MOON: 2,      # Taurus / Vrishabha
    PlanetEnum.MARS: 10,     # Capricorn / Makara
    PlanetEnum.MERCURY: 6,   # Virgo / Kanya
    PlanetEnum.JUPITER: 4,   # Cancer / Karka
    PlanetEnum.VENUS: 12,    # Pisces / Meena
    PlanetEnum.SATURN: 7,    # Libra / Tula
    PlanetEnum.RAHU: 2,      # Taurus
    PlanetEnum.KETU: 8,      # Scorpio
}

DEBILITATION_SIGNS: Dict[PlanetEnum, int] = {
    PlanetEnum.SUN: 7,       # Libra / Tula
    PlanetEnum.MOON: 8,      # Scorpio / Vrishchika
    PlanetEnum.MARS: 4,      # Cancer / Karka
    PlanetEnum.MERCURY: 12,  # Pisces / Meena
    PlanetEnum.JUPITER: 10,  # Capricorn / Makara
    PlanetEnum.VENUS: 6,     # Virgo / Kanya
    PlanetEnum.SATURN: 1,    # Aries / Mesha
    PlanetEnum.RAHU: 8,      # Scorpio
    PlanetEnum.KETU: 2,      # Taurus
}

OWN_SIGNS: Dict[PlanetEnum, List[int]] = {
    PlanetEnum.SUN: [5],           # Leo
    PlanetEnum.MOON: [4],          # Cancer
    PlanetEnum.MARS: [1, 8],       # Aries, Scorpio
    PlanetEnum.MERCURY: [3, 6],    # Gemini, Virgo
    PlanetEnum.JUPITER: [9, 12],   # Sagittarius, Pisces
    PlanetEnum.VENUS: [2, 7],      # Taurus, Libra
    PlanetEnum.SATURN: [10, 11],   # Capricorn, Aquarius
}

NATURAL_BENEFICS: Set[PlanetEnum] = {
    PlanetEnum.JUPITER,
    PlanetEnum.VENUS,
    PlanetEnum.MERCURY,
    PlanetEnum.MOON,
}

NATURAL_MALEFICS: Set[PlanetEnum] = {
    PlanetEnum.SATURN,
    PlanetEnum.MARS,
    PlanetEnum.SUN,
    PlanetEnum.RAHU,
    PlanetEnum.KETU,
}


class YogaDetectorEngine:
    """Evaluates classical Parashari Yogas and Doshas for a UnifiedChartData."""

    @classmethod
    def evaluate(cls, chart: UnifiedChartData, sign_mode: str = "sanskrit") -> YogaEvaluationReport:
        lagna_sign = chart.angles.ascendant_sign.id
        moon_pos = chart.planets[PlanetEnum.MOON]
        moon_sign = moon_pos.sign.id

        planet_houses: Dict[PlanetEnum, int] = {}
        planet_signs: Dict[PlanetEnum, int] = {}
        for p_name, p_pos in chart.planets.items():
            h = ((p_pos.sign.id - lagna_sign) % 12) + 1
            planet_houses[p_name] = h
            planet_signs[p_name] = p_pos.sign.id

        house_lords: Dict[int, PlanetEnum] = {}
        for h in range(1, 13):
            sign_of_house = ((lagna_sign - 1 + h - 1) % 12) + 1
            house_lords[h] = ZODIAC_SIGNS[sign_of_house]["lord"]

        yogas: List[YogaItem] = []

        # 1. Pancha Mahapurusha Yogas
        yogas.extend(cls._detect_mahapurusha(chart, planet_houses, planet_signs))

        # 2. Raja & Royal Auspicious Yogas
        yogas.extend(cls._detect_raja_yogas(chart, planet_houses, planet_signs, house_lords))

        # 3. Dhana & Wealth Yogas
        yogas.extend(cls._detect_dhana_yogas(chart, planet_houses, planet_signs, house_lords))

        # 4. Solar & Lunar Stream Yogas
        yogas.extend(cls._detect_solar_lunar_yogas(chart, planet_houses, planet_signs))

        # 5. Doshas & Afflictions
        yogas.extend(cls._detect_doshas(chart, planet_houses, planet_signs, house_lords))

        # 6. Build Summary Statistics
        auspicious_cnt = sum(1 for y in yogas if y.nature in (YogaNature.AUSPICIOUS, YogaNature.RAJA, YogaNature.DHANA, YogaNature.MAHAPURUSHA) and not y.is_cancelled)
        raja_cnt = sum(1 for y in yogas if y.nature == YogaNature.RAJA and not y.is_cancelled)
        dhana_cnt = sum(1 for y in yogas if y.nature == YogaNature.DHANA and not y.is_cancelled)
        mahapurusha_cnt = sum(1 for y in yogas if y.nature == YogaNature.MAHAPURUSHA and not y.is_cancelled)
        doshas_cnt = sum(1 for y in yogas if y.nature == YogaNature.DOSHA and not y.is_cancelled)

        kuja = next((y for y in yogas if y.id == "kuja_dosha"), None)
        kuja_status = "Absent"
        if kuja:
            kuja_status = "Cancelled" if kuja.is_cancelled else kuja.intensity

        kaal_sarp = next((y for y in yogas if "kaal_sarp" in y.id), None)
        kaal_sarp_status = "Absent"
        if kaal_sarp:
            kaal_sarp_status = "Partial" if "Anshik" in kaal_sarp.name else "Full (Purna)"

        sade_sati = next((y for y in yogas if y.id == "sade_sati"), None)
        sade_sati_status = sade_sati.intensity if sade_sati and sade_sati.is_active else "Inactive"

        summary = YogasSummary(
            total_yogas=len(yogas),
            auspicious_count=auspicious_cnt,
            raja_count=raja_cnt,
            dhana_count=dhana_cnt,
            mahapurusha_count=mahapurusha_cnt,
            doshas_count=doshas_cnt,
            sade_sati_status=sade_sati_status,
            kuja_dosha_status=kuja_status,
            kaal_sarp_status=kaal_sarp_status,
        )

        return YogaEvaluationReport(summary=summary, yogas=yogas)

    @classmethod
    def _detect_mahapurusha(
        cls,
        chart: UnifiedChartData,
        planet_houses: Dict[PlanetEnum, int],
        planet_signs: Dict[PlanetEnum, int],
    ) -> List[YogaItem]:
        results: List[YogaItem] = []
        kendra_houses = {1, 4, 7, 10}

        configs = [
            (
                PlanetEnum.MARS,
                "Ruchaka Yoga",
                "रूचक योग",
                "Presents physical courage, leadership, magnetic authority, victorious willpower, and success in defense or technical enterprise.",
            ),
            (
                PlanetEnum.MERCURY,
                "Bhadra Yoga",
                "भद्र योग",
                "Grants profound intellect, eloquence, analytical genius, executive statesmanship, and mastery over mathematics and commerce.",
            ),
            (
                PlanetEnum.JUPITER,
                "Hamsa Yoga",
                "हंस योग",
                "Bestows spiritual nobility, righteous wisdom, reverence from authorities, unblemished integrity, and divine grace.",
            ),
            (
                PlanetEnum.VENUS,
                "Malavya Yoga",
                "मालव्य योग",
                "Bestows refined artistic taste, marital felicity, vehicle and property luxury, and magnetic worldly charm.",
            ),
            (
                PlanetEnum.SATURN,
                "Sasa Yoga",
                "शश योग",
                "Confers strategic acumen, grassroots authority, enduring stamina, mastery over wealth and organization, and longevity.",
            ),
        ]

        for planet, name, skt, effects in configs:
            h = planet_houses.get(planet)
            s = planet_signs.get(planet)
            if h in kendra_houses:
                is_exalted = (s == EXALTATION_SIGNS.get(planet))
                is_own = (s in OWN_SIGNS.get(planet, []))
                if is_exalted or is_own:
                    sign_desc = "exaltation" if is_exalted else "own sign"
                    s_name = ZODIAC_SIGNS[s]["sanskrit_name"]
                    results.append(
                        YogaItem(
                            id=f"mahapurusha_{planet.value.lower()}",
                            name=name,
                            sanskrit_name=skt,
                            nature=YogaNature.MAHAPURUSHA,
                            category="Pancha Mahapurusha",
                            intensity="Strong",
                            planets_involved=[planet.value],
                            houses_involved=[h],
                            description=f"{planet.value} in {h}th house Kendra in {sign_desc} ({s_name}).",
                            classical_effects=effects,
                        )
                    )

        return results

    @classmethod
    def _detect_raja_yogas(
        cls,
        chart: UnifiedChartData,
        planet_houses: Dict[PlanetEnum, int],
        planet_signs: Dict[PlanetEnum, int],
        house_lords: Dict[int, PlanetEnum],
    ) -> List[YogaItem]:
        results: List[YogaItem] = []

        # A. Gajakesari Yoga
        jup_sign = planet_signs[PlanetEnum.JUPITER]
        moon_sign = planet_signs[PlanetEnum.MOON]
        jup_from_moon = ((jup_sign - moon_sign) % 12) + 1
        if jup_from_moon in (1, 4, 7, 10):
            jup_combust = chart.planets[PlanetEnum.JUPITER].is_combust
            jup_deb = (jup_sign == DEBILITATION_SIGNS[PlanetEnum.JUPITER])
            intensity = "Moderate" if (jup_combust or jup_deb) else "Strong"
            results.append(
                YogaItem(
                    id="gajakesari_yoga",
                    name="Gajakesari Yoga",
                    sanskrit_name="गजकेसरी योग",
                    nature=YogaNature.RAJA,
                    category="Royal & Auspicious",
                    intensity=intensity,
                    planets_involved=["Jupiter", "Moon"],
                    houses_involved=[planet_houses[PlanetEnum.JUPITER], planet_houses[PlanetEnum.MOON]],
                    description=f"Jupiter in {jup_from_moon}th house (Kendra) from natal Moon.",
                    classical_effects="Bestows virtuous reputation, enduring wealth, sharp intellectual brilliance, and triumph over competitors.",
                )
            )

        # B. Budhaditya Yoga
        if planet_signs[PlanetEnum.SUN] == planet_signs[PlanetEnum.MERCURY]:
            sun_lon = chart.planets[PlanetEnum.SUN].longitude
            merc_lon = chart.planets[PlanetEnum.MERCURY].longitude
            diff = abs(sun_lon - merc_lon)
            diff = min(diff, 360.0 - diff)
            is_deep_combust = diff < 3.0
            intensity = "Moderate" if is_deep_combust else "Strong"
            s_name = ZODIAC_SIGNS[planet_signs[PlanetEnum.SUN]]["sanskrit_name"]
            results.append(
                YogaItem(
                    id="budhaditya_yoga",
                    name="Budhaditya Yoga",
                    sanskrit_name="बुधादित्य योग",
                    nature=YogaNature.RAJA,
                    category="Intellectual & Executive",
                    intensity=intensity,
                    planets_involved=["Sun", "Mercury"],
                    houses_involved=[planet_houses[PlanetEnum.SUN]],
                    description=f"Sun and Mercury conjunct in {s_name} ({planet_houses[PlanetEnum.SUN]}th house, {diff:.2f}° orb).",
                    classical_effects="Confers exceptional analytical acumen, administrative distinction, sharp communication skills, and executive success.",
                )
            )

        # C. Dharma-Karmadhipati Yoga
        l9 = house_lords[9]
        l10 = house_lords[10]
        if l9 != l10:
            h9_pos = planet_houses[l9]
            h10_pos = planet_houses[l10]
            s9 = planet_signs[l9]
            s10 = planet_signs[l10]
            if s9 == s10:
                results.append(
                    YogaItem(
                        id="dharma_karmadhipati_yoga",
                        name="Dharma-Karmadhipati Yoga",
                        sanskrit_name="धर्म-कर्माधिपति योग",
                        nature=YogaNature.RAJA,
                        category="Highest Parashari Raja Yoga",
                        intensity="Strong",
                        planets_involved=[l9.value, l10.value],
                        houses_involved=[h9_pos],
                        description=f"9th Lord ({l9.value}) and 10th Lord ({l10.value}) conjunct in house {h9_pos}.",
                        classical_effects="One of the paramount Raja Yogas in BPHS: confers eminent societal status, governmental favor, ethical leadership, and lasting legacy.",
                    )
                )
            elif ((s9 - s10) % 12) == 6:
                results.append(
                    YogaItem(
                        id="dharma_karmadhipati_aspect",
                        name="Dharma-Karmadhipati Yoga (Drishti)",
                        sanskrit_name="धर्म-कर्माधिपति योग (दृष्टि)",
                        nature=YogaNature.RAJA,
                        category="Highest Parashari Raja Yoga",
                        intensity="Strong",
                        planets_involved=[l9.value, l10.value],
                        houses_involved=[h9_pos, h10_pos],
                        description=f"9th Lord ({l9.value}) and 10th Lord ({l10.value}) in mutual 7th aspect.",
                        classical_effects="Blends righteous fortune (Dharma) with worldly achievement (Karma), bringing fame and executive authority.",
                    )
                )

        # D. Kendra-Trikona Raja Yogas
        kendra_lords = {house_lords[1], house_lords[4], house_lords[7], house_lords[10]}
        trikona_lords = {house_lords[5], house_lords[9]}
        checked_pairs = set()
        for kl in kendra_lords:
            for tl in trikona_lords:
                if kl != tl and (kl, tl) not in checked_pairs and (tl, kl) not in checked_pairs:
                    checked_pairs.add((kl, tl))
                    if planet_signs[kl] == planet_signs[tl]:
                        results.append(
                            YogaItem(
                                id=f"kendra_trikona_{kl.value}_{tl.value}".lower(),
                                name=f"Kendra-Trikona Raja Yoga ({kl.value} + {tl.value})",
                                sanskrit_name="केन्द्र-त्रिकोण राजयोग",
                                nature=YogaNature.RAJA,
                                category="Parashari Raja Yoga",
                                intensity="Strong",
                                planets_involved=[kl.value, tl.value],
                                houses_involved=[planet_houses[kl]],
                                description=f"Kendra Lord ({kl.value}) and Trikona Lord ({tl.value}) conjunct in house {planet_houses[kl]}.",
                                classical_effects="Harmonizes action (Kendra) with grace and luck (Trikona), producing upward mobility and prosperity.",
                            )
                        )

        # E. Neechabhanga Raja Yoga
        for p_name, deb_sign in DEBILITATION_SIGNS.items():
            if p_name in (PlanetEnum.RAHU, PlanetEnum.KETU):
                continue
            if planet_signs.get(p_name) == deb_sign:
                disp_lord = ZODIAC_SIGNS[deb_sign]["lord"]
                disp_h_lagna = planet_houses[disp_lord]
                disp_sign = planet_signs[disp_lord]
                disp_from_moon = ((disp_sign - planet_signs[PlanetEnum.MOON]) % 12) + 1
                if disp_h_lagna in (1, 4, 7, 10) or disp_from_moon in (1, 4, 7, 10):
                    results.append(
                        YogaItem(
                            id=f"neechabhanga_{p_name.value.lower()}",
                            name=f"Neechabhanga Raja Yoga ({p_name.value})",
                            sanskrit_name="नीचभंग राजयोग",
                            nature=YogaNature.RAJA,
                            category="Transformative Raja Yoga",
                            intensity="Strong",
                            planets_involved=[p_name.value, disp_lord.value],
                            houses_involved=[planet_houses[p_name], disp_h_lagna],
                            description=f"{p_name.value} debilitated in {ZODIAC_SIGNS[deb_sign]['sanskrit_name']}, but its dispositor ({disp_lord.value}) is in Kendra.",
                            classical_effects="Overcomes early setbacks, transforming liabilities into extraordinary perseverance and success.",
                        )
                    )

        # F. Vipareeta Raja Yogas
        l6 = house_lords[6]
        l8 = house_lords[8]
        l12 = house_lords[12]
        trik_houses = {6, 8, 12}

        if planet_houses[l6] in trik_houses:
            results.append(
                YogaItem(
                    id="harsha_yoga",
                    name="Harsha Yoga (Vipareeta)",
                    sanskrit_name="हर्ष योग",
                    nature=YogaNature.RAJA,
                    category="Vipareeta Raja Yoga",
                    intensity="Moderate",
                    planets_involved=[l6.value],
                    houses_involved=[planet_houses[l6]],
                    description=f"6th Lord ({l6.value}) placed in dusthana house {planet_houses[l6]}.",
                    classical_effects="Invincible against adversaries, grants robust health, freedom from fear, and sudden breakthroughs.",
                )
            )

        if planet_houses[l8] in trik_houses:
            results.append(
                YogaItem(
                    id="sarala_yoga",
                    name="Sarala Yoga (Vipareeta)",
                    sanskrit_name="सरल योग",
                    nature=YogaNature.RAJA,
                    category="Vipareeta Raja Yoga",
                    intensity="Moderate",
                    planets_involved=[l8.value],
                    houses_involved=[planet_houses[l8]],
                    description=f"8th Lord ({l8.value}) placed in dusthana house {planet_houses[l8]}.",
                    classical_effects="Grants long life, scholarly determination, mastery over hidden knowledge, and unexpected financial windfalls.",
                )
            )

        if planet_houses[l12] in trik_houses:
            results.append(
                YogaItem(
                    id="vimala_yoga",
                    name="Vimala Yoga (Vipareeta)",
                    sanskrit_name="विमल योग",
                    nature=YogaNature.RAJA,
                    category="Vipareeta Raja Yoga",
                    intensity="Moderate",
                    planets_involved=[l12.value],
                    houses_involved=[planet_houses[l12]],
                    description=f"12th Lord ({l12.value}) placed in dusthana house {planet_houses[l12]}.",
                    classical_effects="Bestows frugal wisdom, financial independence, spiritual discernment, and virtue in expenditures.",
                )
            )

        # G. Amala Yoga
        h10_lagna_planets = [p for p, h in planet_houses.items() if h == 10 and p in NATURAL_BENEFICS]
        h10_moon_planets = [
            p for p, s in planet_signs.items()
            if ((s - planet_signs[PlanetEnum.MOON]) % 12) + 1 == 10 and p in NATURAL_BENEFICS
        ]
        if h10_lagna_planets or h10_moon_planets:
            active_p = list(set(h10_lagna_planets + h10_moon_planets))
            results.append(
                YogaItem(
                    id="amala_yoga",
                    name="Amala Yoga",
                    sanskrit_name="अमल योग",
                    nature=YogaNature.RAJA,
                    category="Virtue & Career",
                    intensity="Strong",
                    planets_involved=[p.value for p in active_p],
                    houses_involved=[10],
                    description=f"Natural benefic ({', '.join(p.value for p in active_p)}) occupying 10th house.",
                    classical_effects="Bestows spotless reputation, ethical leadership, and lasting professional honor.",
                )
            )

        # H. Parivartana Yogas
        for h1 in range(1, 13):
            for h2 in range(h1 + 1, 13):
                l_h1 = house_lords[h1]
                l_h2 = house_lords[h2]
                if l_h1 != l_h2:
                    if planet_houses[l_h1] == h2 and planet_houses[l_h2] == h1:
                        if h1 in (6, 8, 12) or h2 in (6, 8, 12):
                            y_cat = "Dainya Parivartana (Difficult)"
                            nature = YogaNature.NEUTRAL
                            effects = "Brings volatile reversals and lessons through financial and relationship challenges."
                        elif h1 == 3 or h2 == 3:
                            y_cat = "Khala Parivartana (Fluctuating)"
                            nature = YogaNature.NEUTRAL
                            effects = "Produces alternating periods of struggle and sudden triumphs through courage."
                        else:
                            y_cat = "Maha Parivartana (Auspicious)"
                            nature = YogaNature.RAJA
                            effects = "Substantially empowers both houses, bringing wealth, social honor, and divine assistance."

                        results.append(
                            YogaItem(
                                id=f"parivartana_{h1}_{h2}",
                                name=f"Parivartana Yoga ({h1} ⇄ {h2})",
                                sanskrit_name="परिवर्तन योग",
                                nature=nature,
                                category=y_cat,
                                intensity="Strong",
                                planets_involved=[l_h1.value, l_h2.value],
                                houses_involved=[h1, h2],
                                description=f"Mutual exchange: {l_h1.value} in house {h2}, and {l_h2.value} in house {h1}.",
                                classical_effects=effects,
                            )
                        )

        return results

    @classmethod
    def _detect_dhana_yogas(
        cls,
        chart: UnifiedChartData,
        planet_houses: Dict[PlanetEnum, int],
        planet_signs: Dict[PlanetEnum, int],
        house_lords: Dict[int, PlanetEnum],
    ) -> List[YogaItem]:
        results: List[YogaItem] = []

        # Chandra-Mangala Yoga
        m_sign = planet_signs[PlanetEnum.MOON]
        ma_sign = planet_signs[PlanetEnum.MARS]
        is_conj = (m_sign == ma_sign)
        is_7th = (((ma_sign - m_sign) % 12) == 6)
        if is_conj or is_7th:
            desc_str = "conjunct" if is_conj else "in mutual 7th aspect"
            results.append(
                YogaItem(
                    id="chandra_mangala_yoga",
                    name="Chandra-Mangala Yoga",
                    sanskrit_name="चन्द्र-मंगल योग",
                    nature=YogaNature.DHANA,
                    category="Enterprise & Wealth",
                    intensity="Strong",
                    planets_involved=["Moon", "Mars"],
                    houses_involved=[planet_houses[PlanetEnum.MOON], planet_houses[PlanetEnum.MARS]],
                    description=f"Moon and Mars {desc_str} in the chart.",
                    classical_effects="Bestows fierce commercial enterprise, resourcefulness in business, real estate profits, and energetic accumulation of wealth.",
                )
            )

        # 2nd Lord + 11th Lord Combination
        l2 = house_lords[2]
        l11 = house_lords[11]
        if l2 != l11:
            if planet_signs[l2] == planet_signs[l11]:
                results.append(
                    YogaItem(
                        id="dhana_2_11_conjunction",
                        name="Dhana Yoga (2nd & 11th Lords)",
                        sanskrit_name="धन योग",
                        nature=YogaNature.DHANA,
                        category="Financial Prosperity",
                        intensity="Strong",
                        planets_involved=[l2.value, l11.value],
                        houses_involved=[planet_houses[l2]],
                        description=f"2nd Lord ({l2.value}) and 11th Lord ({l11.value}) conjunct in house {planet_houses[l2]}.",
                        classical_effects="Assures abundant prosperity, recurring income streams, liquid savings, and financial stability.",
                    )
                )

        # Vasumathi Yoga
        benefics_upachaya = [
            p for p in (PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.MERCURY)
            if planet_houses[p] in (3, 6, 10, 11)
        ]
        if len(benefics_upachaya) >= 2:
            results.append(
                YogaItem(
                    id="vasumathi_yoga",
                    name="Vasumathi Yoga",
                    sanskrit_name="वसुमति योग",
                    nature=YogaNature.DHANA,
                    category="Autonomous Wealth",
                    intensity="Strong" if len(benefics_upachaya) == 3 else "Moderate",
                    planets_involved=[p.value for p in benefics_upachaya],
                    houses_involved=[planet_houses[p] for p in benefics_upachaya],
                    description=f"{len(benefics_upachaya)} natural benefics ({', '.join(p.value for p in benefics_upachaya)}) in Upachaya houses.",
                    classical_effects="Assures financial self-reliance and self-earned affluence.",
                )
            )

        # Saraswati Yoga
        saraswati_houses = {1, 2, 4, 5, 7, 9, 10}
        if (
            planet_houses[PlanetEnum.JUPITER] in saraswati_houses
            and planet_houses[PlanetEnum.VENUS] in saraswati_houses
            and planet_houses[PlanetEnum.MERCURY] in saraswati_houses
        ):
            results.append(
                YogaItem(
                    id="saraswati_yoga",
                    name="Saraswati Yoga",
                    sanskrit_name="सरस्वती योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Wisdom & Arts",
                    intensity="Strong",
                    planets_involved=["Jupiter", "Venus", "Mercury"],
                    houses_involved=[
                        planet_houses[PlanetEnum.JUPITER],
                        planet_houses[PlanetEnum.VENUS],
                        planet_houses[PlanetEnum.MERCURY],
                    ],
                    description="Jupiter, Venus, and Mercury placed in Kendra, Trikona, or 2nd house.",
                    classical_effects="Endows eloquence, creative and literary genius, and academic mastery.",
                )
            )

        return results

    @classmethod
    def _detect_solar_lunar_yogas(
        cls,
        chart: UnifiedChartData,
        planet_houses: Dict[PlanetEnum, int],
        planet_signs: Dict[PlanetEnum, int],
    ) -> List[YogaItem]:
        results: List[YogaItem] = []

        sun_sign = planet_signs[PlanetEnum.SUN]
        moon_sign = planet_signs[PlanetEnum.MOON]

        qualifying_solar = [
            p for p in (PlanetEnum.MARS, PlanetEnum.MERCURY, PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN)
        ]
        in_2nd_sun = [p for p in qualifying_solar if ((planet_signs[p] - sun_sign) % 12) + 1 == 2]
        in_12th_sun = [p for p in qualifying_solar if ((planet_signs[p] - sun_sign) % 12) + 1 == 12]

        if in_2nd_sun and in_12th_sun:
            results.append(
                YogaItem(
                    id="ubhayachari_yoga",
                    name="Ubhayachari Yoga",
                    sanskrit_name="उभयचारी योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Solar Stream",
                    intensity="Strong",
                    planets_involved=[p.value for p in in_2nd_sun + in_12th_sun],
                    houses_involved=[planet_houses[PlanetEnum.SUN]],
                    description="Planets flanking Sun in both 2nd and 12th houses from it.",
                    classical_effects="Grants balanced temperament, eloquent diplomacy, noble stature, and strong vitality.",
                )
            )
        elif in_2nd_sun:
            results.append(
                YogaItem(
                    id="veshi_yoga",
                    name="Veshi Yoga",
                    sanskrit_name="वेशि योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Solar Stream",
                    intensity="Moderate",
                    planets_involved=[p.value for p in in_2nd_sun],
                    houses_involved=[planet_houses[PlanetEnum.SUN]],
                    description=f"Planet ({', '.join(p.value for p in in_2nd_sun)}) in 2nd house from Sun.",
                    classical_effects="Bestows upright character, truthfulness, and comfortable lifestyle.",
                )
            )
        elif in_12th_sun:
            results.append(
                YogaItem(
                    id="vosi_yoga",
                    name="Vosi Yoga",
                    sanskrit_name="वोशि योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Solar Stream",
                    intensity="Moderate",
                    planets_involved=[p.value for p in in_12th_sun],
                    houses_involved=[planet_houses[PlanetEnum.SUN]],
                    description=f"Planet ({', '.join(p.value for p in in_12th_sun)}) in 12th house from Sun.",
                    classical_effects="Confers industrious spirit, sharp memory, and generous expenditure.",
                )
            )

        qualifying_lunar = [
            p for p in (PlanetEnum.MARS, PlanetEnum.MERCURY, PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN)
        ]
        in_2nd_moon = [p for p in qualifying_lunar if ((planet_signs[p] - moon_sign) % 12) + 1 == 2]
        in_12th_moon = [p for p in qualifying_lunar if ((planet_signs[p] - moon_sign) % 12) + 1 == 12]

        if in_2nd_moon and in_12th_moon:
            results.append(
                YogaItem(
                    id="durudhura_yoga",
                    name="Durudhura Yoga",
                    sanskrit_name="दुरुधुरा योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Lunar Stream",
                    intensity="Strong",
                    planets_involved=[p.value for p in in_2nd_moon + in_12th_moon],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description="Planets flanking Moon in both 2nd and 12th houses from it.",
                    classical_effects="Bestows tremendous worldly security, wealth, generosity, and contentment.",
                )
            )
        elif in_2nd_moon:
            results.append(
                YogaItem(
                    id="sunapha_yoga",
                    name="Sunapha Yoga",
                    sanskrit_name="सुनफा योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Lunar Stream",
                    intensity="Moderate",
                    planets_involved=[p.value for p in in_2nd_moon],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description=f"Planet ({', '.join(p.value for p in in_2nd_moon)}) in 2nd house from Moon.",
                    classical_effects="Grants self-created wealth, practical intelligence, and steady success.",
                )
            )
        elif in_12th_moon:
            results.append(
                YogaItem(
                    id="anapha_yoga",
                    name="Anapha Yoga",
                    sanskrit_name="अनफा योग",
                    nature=YogaNature.AUSPICIOUS,
                    category="Lunar Stream",
                    intensity="Moderate",
                    planets_involved=[p.value for p in in_12th_moon],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description=f"Planet ({', '.join(p.value for p in in_12th_moon)}) in 12th house from Moon.",
                    classical_effects="Confers refined habits, good health, self-control, and emotional calm.",
                )
            )

        return results

    @classmethod
    def _detect_doshas(
        cls,
        chart: UnifiedChartData,
        planet_houses: Dict[PlanetEnum, int],
        planet_signs: Dict[PlanetEnum, int],
        house_lords: Dict[int, PlanetEnum],
    ) -> List[YogaItem]:
        results: List[YogaItem] = []

        mars_h_lagna = planet_houses[PlanetEnum.MARS]
        mars_sign = planet_signs[PlanetEnum.MARS]
        moon_sign = planet_signs[PlanetEnum.MOON]
        venus_sign = planet_signs[PlanetEnum.VENUS]

        mars_from_moon = ((mars_sign - moon_sign) % 12) + 1
        mars_from_venus = ((mars_sign - venus_sign) % 12) + 1

        manglik_houses = {1, 2, 4, 7, 8, 12}
        is_manglik_lagna = mars_h_lagna in manglik_houses
        is_manglik_moon = mars_from_moon in manglik_houses
        is_manglik_venus = mars_from_venus in manglik_houses

        if is_manglik_lagna or is_manglik_moon or is_manglik_venus:
            cancellations: List[str] = []

            if mars_sign in (1, 8, 10):
                cancellations.append("Mars in own or exaltation sign (Mesha/Vrishchika/Makara)")

            if mars_h_lagna == 1 and mars_sign == 1:
                cancellations.append("Mars in 1st house in Aries")
            elif mars_h_lagna == 4 and mars_sign == 8:
                cancellations.append("Mars in 4th house in Scorpio")
            elif mars_h_lagna == 7 and mars_sign == 10:
                cancellations.append("Mars in 7th house in Capricorn")
            elif mars_h_lagna == 8 and mars_sign in (9, 12):
                cancellations.append("Mars in 8th house in Sagittarius/Pisces")
            elif mars_h_lagna == 2 and mars_sign in (3, 6):
                cancellations.append("Mars in 2nd house in Gemini/Virgo")

            jup_sign = planet_signs[PlanetEnum.JUPITER]
            if mars_sign == jup_sign:
                cancellations.append("Mars conjunct benefic Guru (Jupiter)")
            elif ((jup_sign - mars_sign) % 12) == 6 or ((mars_sign - jup_sign) % 12) in (4, 8):
                cancellations.append("Mars aspected by benefic Guru (Jupiter)")

            if mars_sign == moon_sign:
                cancellations.append("Mars conjunct Chandra (Moon)")

            is_cancelled = len(cancellations) > 0
            reason = "; ".join(cancellations) if is_cancelled else None

            score = (1 if is_manglik_lagna else 0) + (1 if is_manglik_moon else 0) + (1 if is_manglik_venus else 0)
            intensity = "High" if score >= 2 else "Moderate"
            if is_cancelled:
                intensity = "Cancelled"

            sources = []
            if is_manglik_lagna:
                sources.append(f"Lagna ({mars_h_lagna}th)")
            if is_manglik_moon:
                sources.append(f"Moon ({mars_from_moon}th)")
            if is_manglik_venus:
                sources.append(f"Venus ({mars_from_venus}th)")

            results.append(
                YogaItem(
                    id="kuja_dosha",
                    name="Manglik / Kuja Dosha",
                    sanskrit_name="कुज / मांगलिक दोष",
                    nature=YogaNature.DOSHA,
                    category="Marital Harmony",
                    is_active=not is_cancelled,
                    intensity=intensity,
                    planets_involved=["Mars"],
                    houses_involved=[mars_h_lagna],
                    description=f"Mars occupies an active affliction house from {', '.join(sources)}.",
                    classical_effects="Can create friction, temperament mismatches, or delays in partnerships unless channelled through mature self-awareness or balanced by a matching chart.",
                    is_cancelled=is_cancelled,
                    cancellation_reason=reason,
                )
            )

        # Kaal Sarp Dosha
        rahu_lon = chart.planets[PlanetEnum.RAHU].longitude
        ketu_lon = chart.planets[PlanetEnum.KETU].longitude

        physical_planets = [
            PlanetEnum.SUN,
            PlanetEnum.MOON,
            PlanetEnum.MARS,
            PlanetEnum.MERCURY,
            PlanetEnum.JUPITER,
            PlanetEnum.VENUS,
            PlanetEnum.SATURN,
        ]

        arc_rk = (ketu_lon - rahu_lon) % 360.0
        in_rk_count = 0
        in_kr_count = 0
        for p in physical_planets:
            p_lon = chart.planets[p].longitude
            p_from_r = (p_lon - rahu_lon) % 360.0
            if p_from_r <= arc_rk:
                in_rk_count += 1
            else:
                in_kr_count += 1

        is_purna_kaal_sarp = (in_rk_count == 7 or in_kr_count == 7)
        is_anshik_kaal_sarp = (in_rk_count == 6 or in_kr_count == 6)

        if is_purna_kaal_sarp or is_anshik_kaal_sarp:
            rahu_h = planet_houses[PlanetEnum.RAHU]
            kaal_sarp_names = {
                1: "Anant Kaal Sarp",
                2: "Kulik Kaal Sarp",
                3: "Vasuki Kaal Sarp",
                4: "Shankhpal Kaal Sarp",
                5: "Padma Kaal Sarp",
                6: "Mahapadma Kaal Sarp",
                7: "Takshak Kaal Sarp",
                8: "Karkotak Kaal Sarp",
                9: "Shankhachur Kaal Sarp",
                10: "Ghatak Kaal Sarp",
                11: "Vishdhar Kaal Sarp",
                12: "Sheshnag Kaal Sarp",
            }
            ks_type = kaal_sarp_names.get(rahu_h, "Kaal Sarp")
            ks_prefix = "Purna (Full)" if is_purna_kaal_sarp else "Anshik (Partial)"
            results.append(
                YogaItem(
                    id=f"kaal_sarp_h{rahu_h}",
                    name=f"{ks_type} ({ks_prefix})",
                    sanskrit_name="कालसर्प दोष",
                    nature=YogaNature.DOSHA,
                    category="Karmic Life Pattern",
                    intensity="Strong" if is_purna_kaal_sarp else "Mild",
                    planets_involved=["Rahu", "Ketu"],
                    houses_involved=[rahu_h, planet_houses[PlanetEnum.KETU]],
                    description=f"All physical planets hemmed between Rahu ({rahu_h}th) and Ketu ({planet_houses[PlanetEnum.KETU]}th).",
                    classical_effects="Brings intense initial struggles followed by dramatic rise after age 33-36; forces profound spiritual detachment and soul refinement.",
                )
            )

        # Kemadruma Yoga
        qualifying_kemadruma = [
            p for p in (PlanetEnum.MARS, PlanetEnum.MERCURY, PlanetEnum.JUPITER, PlanetEnum.VENUS, PlanetEnum.SATURN)
        ]
        has_2nd_moon = any(((planet_signs[p] - moon_sign) % 12) + 1 == 2 for p in qualifying_kemadruma)
        has_12th_moon = any(((planet_signs[p] - moon_sign) % 12) + 1 == 12 for p in qualifying_kemadruma)

        if not has_2nd_moon and not has_12th_moon:
            planets_in_kendra_lagna = any(planet_houses[p] in (1, 4, 7, 10) for p in qualifying_kemadruma)
            planets_in_kendra_moon = any(
                ((planet_signs[p] - moon_sign) % 12) + 1 in (1, 4, 7, 10) for p in qualifying_kemadruma
            )
            is_cancelled = planets_in_kendra_lagna or planets_in_kendra_moon
            cancel_reason = "Cancelled: Planets placed in Kendras from Lagna or Moon anchor the chart" if is_cancelled else None

            results.append(
                YogaItem(
                    id="kemadruma_yoga",
                    name="Kemadruma Yoga",
                    sanskrit_name="केमद्रुम योग",
                    nature=YogaNature.DOSHA,
                    category="Lunar Affliction",
                    is_active=not is_cancelled,
                    intensity="Cancelled" if is_cancelled else "Moderate",
                    planets_involved=["Moon"],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description="Moon stands isolated with no physical planets in the 2nd or 12th houses from it.",
                    classical_effects="Can induce bouts of loneliness or financial fluctuation; mitigated completely when other planets anchor the angles.",
                    is_cancelled=is_cancelled,
                    cancellation_reason=cancel_reason,
                )
            )

        # Guru Chandal Dosha
        jup_sign = planet_signs[PlanetEnum.JUPITER]
        if jup_sign == planet_signs[PlanetEnum.RAHU]:
            results.append(
                YogaItem(
                    id="guru_chandal_rahu",
                    name="Guru Chandal Dosha (Jupiter-Rahu)",
                    sanskrit_name="गुरु चांडाल दोष",
                    nature=YogaNature.DOSHA,
                    category="Belief & Wisdom",
                    intensity="Moderate",
                    planets_involved=["Jupiter", "Rahu"],
                    houses_involved=[planet_houses[PlanetEnum.JUPITER]],
                    description="Jupiter and Rahu conjunct in the same sign.",
                    classical_effects="Questions orthodox dogmas; confers unconventional philosophical or technological breakthroughs.",
                )
            )
        elif jup_sign == planet_signs[PlanetEnum.KETU]:
            results.append(
                YogaItem(
                    id="guru_chandal_ketu",
                    name="Guru Chandal Dosha (Jupiter-Ketu)",
                    sanskrit_name="गुरु चांडाल दोष",
                    nature=YogaNature.DOSHA,
                    category="Spiritual Quest",
                    intensity="Moderate",
                    planets_involved=["Jupiter", "Ketu"],
                    houses_involved=[planet_houses[PlanetEnum.JUPITER]],
                    description="Jupiter and Ketu conjunct in the same sign.",
                    classical_effects="Deep mystical impulses; detachment from conventional rituals and search for esoteric truth.",
                )
            )

        # Grahan Dosha
        sun_sign = planet_signs[PlanetEnum.SUN]
        rahu_s = planet_signs[PlanetEnum.RAHU]
        ketu_s = planet_signs[PlanetEnum.KETU]
        if sun_sign in (rahu_s, ketu_s):
            node_name = "Rahu" if sun_sign == rahu_s else "Ketu"
            results.append(
                YogaItem(
                    id="surya_grahan_dosha",
                    name=f"Surya Grahan Dosha (Sun-{node_name})",
                    sanskrit_name="सूर्य ग्रहण दोष",
                    nature=YogaNature.DOSHA,
                    category="Vitality & Father",
                    intensity="Moderate",
                    planets_involved=["Sun", node_name],
                    houses_involved=[planet_houses[PlanetEnum.SUN]],
                    description=f"Sun conjunct {node_name} in house {planet_houses[PlanetEnum.SUN]}.",
                    classical_effects="Tests self-confidence and relationship with authorities; prompts cultivation of spiritual radiance.",
                )
            )

        if moon_sign in (rahu_s, ketu_s):
            node_name = "Rahu" if moon_sign == rahu_s else "Ketu"
            results.append(
                YogaItem(
                    id="chandra_grahan_dosha",
                    name=f"Chandra Grahan Dosha (Moon-{node_name})",
                    sanskrit_name="चन्द्र ग्रहण दोष",
                    nature=YogaNature.DOSHA,
                    category="Emotional Equilibrium",
                    intensity="Moderate",
                    planets_involved=["Moon", node_name],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description=f"Moon conjunct {node_name} in house {planet_houses[PlanetEnum.MOON]}.",
                    classical_effects="High emotional sensitivity and intuitive empathy; benefits from meditation and grounded routines.",
                )
            )

        # Visha Dosha
        if moon_sign == planet_signs[PlanetEnum.SATURN]:
            results.append(
                YogaItem(
                    id="visha_dosha",
                    name="Visha Dosha (Saturn-Moon)",
                    sanskrit_name="विष दोष",
                    nature=YogaNature.DOSHA,
                    category="Emotional Resilience",
                    intensity="Moderate",
                    planets_involved=["Saturn", "Moon"],
                    houses_involved=[planet_houses[PlanetEnum.MOON]],
                    description="Saturn and Moon conjunct in the same sign.",
                    classical_effects="Builds immense stoic resilience, emotional depth, and practical patience through life tests.",
                )
            )

        # Sade Sati Tracker
        saturn_sign = planet_signs[PlanetEnum.SATURN]
        sat_from_moon = ((saturn_sign - moon_sign) % 12) + 1
        sade_sati_phase = None
        sade_sati_desc = None

        if sat_from_moon == 12:
            sade_sati_phase = "1st Phase (Rising / Aardha)"
            sade_sati_desc = "Saturn in 12th from Moon: restructuring finances, foreign matters, and inner discipline."
        elif sat_from_moon == 1:
            sade_sati_phase = "2nd Phase (Peak / Janma Shani)"
            sade_sati_desc = "Saturn in natal Moon sign: pivotal personal metamorphosis, heavy responsibilities, and perseverance."
        elif sat_from_moon == 2:
            sade_sati_phase = "3rd Phase (Setting / Antya)"
            sade_sati_desc = "Saturn in 2nd from Moon: consolidation of family, savings, speech, and transition to stability."
        elif sat_from_moon == 4:
            sade_sati_phase = "Dhaiya (Kantaka Shani / 4th)"
            sade_sati_desc = "Saturn in 4th from Moon: focus on domestic foundation, peace of mind, and property obligations."
        elif sat_from_moon == 8:
            sade_sati_phase = "Dhaiya (Ashtama Shani / 8th)"
            sade_sati_desc = "Saturn in 8th from Moon: sudden transformative events, deep psychological endurance, and patience."

        if sade_sati_phase:
            results.append(
                YogaItem(
                    id="sade_sati",
                    name=f"Shani Sade Sati / Dhaiya ({sade_sati_phase})",
                    sanskrit_name="शनि साढ़े साती / ढैय्या",
                    nature=YogaNature.NEUTRAL,
                    category="Transit Influence",
                    is_active=True,
                    intensity=sade_sati_phase,
                    planets_involved=["Saturn", "Moon"],
                    houses_involved=[planet_houses[PlanetEnum.SATURN]],
                    description=sade_sati_desc,
                    classical_effects="A profound cosmic calibration cycle that removes illusions, disciplines the ego, and rewards steady, persistent effort.",
                )
            )

        return results
