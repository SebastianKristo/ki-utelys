"""Avgjørelsen: skal utelysene stå på akkurat nå?

Alt som avgjør ligger i `bor_lyse()`. Den tar tilstanden som argumenter og returnerer
svaret sammen med en begrunnelse, slik at den kan testes uten Home Assistant — og slik
at kortet kan vise HVORFOR lyset står som det står.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass
class Svar:
    """Om lyset skal lyse, og hvorfor."""

    paa: bool
    grunn: str
    terskel: float | None = None


def _tid(t: str | time | None, standard: time) -> time:
    if isinstance(t, time):
        return t
    if isinstance(t, str) and ":" in t:
        try:
            deler = [int(x) for x in t.split(":")[:2]]
            return time(deler[0], deler[1])
        except ValueError:
            return standard
    return standard


def sky_terskel(grunn_terskel: float, skydekke: float | None,
                justering: float) -> float:
    """Flytter terskelen oppover når det er overskyet.

    En overskyet ettermiddag i oktober blir mørk tidligere enn solhøyden alene sier.
    Uten en lux-sensor er skydekket det nærmeste vi kommer å måle det.

    Justeringen er lineær i skydekket: klar himmel gir ingen endring, helt overskyet
    gir full justering. Vi kunne brukt en kurve, men forskjellen ville vært mindre enn
    presisjonen i selve solhøyden.
    """
    if skydekke is None or justering <= 0:
        return grunn_terskel
    try:
        andel = max(0.0, min(100.0, float(skydekke))) / 100.0
    except (TypeError, ValueError):
        return grunn_terskel
    return grunn_terskel + justering * andel


def bor_lyse(
    *,
    naa: datetime,
    hoyde: float,
    star_paa: bool,
    morkt_i_natt: bool,
    terskel_paa: float,
    terskel_av: float,
    senest_paa: str | time = "23:30",
    tidligst_av: str | time = "05:00",
    morgen_paa: str | time = "05:30",
    morgen_av: str | time = "09:00",
    kveld_aktiv: bool = True,
    morgen_aktiv: bool = True,
    skydekke: float | None = None,
    sky_justering: float = 0.0,
) -> Svar:
    """Skal lyset stå på nå?

    `star_paa` er med fordi terskelen er ulik på vei ned og opp. Uten den ville lyset
    blafret rundt terskelen i tussmørket, som er nøyaktig det hysteresen skal hindre.
    """
    klokke = naa.time()
    p_terskel = sky_terskel(terskel_paa, skydekke, sky_justering)
    a_terskel = sky_terskel(terskel_av, skydekke, sky_justering)

    t_senest = _tid(senest_paa, time(23, 30))
    t_tidligst_av = _tid(tidligst_av, time(5, 0))
    t_morgen_paa = _tid(morgen_paa, time(5, 30))
    t_morgen_av = _tid(morgen_av, time(9, 0))

    # Er vi i morgenvinduet eller kveldsvinduet? Vinduene deles ved morgengrensen:
    # alt før `morgen_av` regnes som morgen, resten som kveld.
    er_morgen = klokke < t_morgen_av

    if er_morgen:
        if not morgen_aktiv:
            return Svar(False, "Morgenlys er slått av", p_terskel)
        if klokke < t_morgen_paa:
            # Før morgenvinduet åpner. Lyset kan likevel stå på fra kvelden før — da
            # lar vi det stå til det blir lyst, i stedet for å slå det av midt på natta.
            if star_paa and klokke < t_tidligst_av:
                return Svar(True, "Natt — lyset står på fra i går kveld", p_terskel)
            if star_paa:
                if hoyde >= a_terskel:
                    return Svar(False, "Lyst nok", a_terskel)
                return Svar(True, "Fortsatt mørkt", a_terskel)
            return Svar(False, "For tidlig", p_terskel)

        # I morgenvinduet: på så lenge det er mørkt, av når det lysner.
        if star_paa:
            if hoyde >= a_terskel:
                return Svar(False, "Lyst nok om morgenen", a_terskel)
            return Svar(True, "Mørkt om morgenen", a_terskel)
        if hoyde < p_terskel:
            return Svar(True, "Mørkt om morgenen", p_terskel)
        return Svar(False, "Lyst nok om morgenen", p_terskel)

    # --- kveld ---
    if not kveld_aktiv:
        return Svar(False, "Kveldslys er slått av", p_terskel)

    if not morkt_i_natt:
        # Sommersperren. Den gjelder bare kvelden; står lyset på fra i går, slås det
        # av av morgenreglene over.
        return Svar(False, "Lys sommernatt — hopper over", p_terskel)

    if star_paa:
        if hoyde >= a_terskel:
            return Svar(False, "Lyst nok", a_terskel)
        if klokke >= t_tidligst_av and klokke < t_morgen_av:
            return Svar(True, "Mørkt", a_terskel)
        return Svar(True, "Mørkt", a_terskel)

    # Av, og vurderer å slå på.
    if klokke >= t_senest:
        # For sent. Blir det først mørkt etter denne grensen, dropper vi kvelden —
        # ellers tennes lyset når alle sover.
        return Svar(False, "For sent på kvelden", p_terskel)
    if hoyde < p_terskel:
        return Svar(True, "Mørkt", p_terskel)
    return Svar(False, "Lyst nok", p_terskel)
