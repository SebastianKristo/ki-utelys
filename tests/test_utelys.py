"""Tester for solgeometrien og lysreglene.

Begge er rene funksjoner uten Home Assistant, så de kan kjøres direkte. Det er med
vilje: avgjørelsen om å tenne et lys skal kunne etterprøves uten å starte et helt hus.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "custom_components" / "ki_utelys"))

import regler  # noqa: E402
import sol  # noqa: E402

OSLO = 59.91
TOTEN = 60.68
STROMSTAD = 58.93


# ----------------------------------------------------------------- solgeometri
def test_deklinasjon_ved_solverv():
    """Solvervene er fasit: ±23,44°."""
    assert sol.deklinasjon(date(2026, 6, 21)) == pytest.approx(23.44, abs=0.05)
    assert sol.deklinasjon(date(2026, 12, 21)) == pytest.approx(-23.44, abs=0.05)


def test_deklinasjon_ved_jevndogn():
    """Jevndøgn er null. Her bommer den enkle kosinusformelen med nesten en grad."""
    assert sol.deklinasjon(date(2026, 3, 20)) == pytest.approx(0.0, abs=0.3)
    assert sol.deklinasjon(date(2026, 9, 23)) == pytest.approx(0.0, abs=0.3)


@pytest.mark.parametrize("dag", [date(2026, 1, 1) + timedelta(days=n)
                                 for n in range(0, 365, 11)])
def test_deklinasjon_holder_seg_innenfor(dag):
    """Sola kan aldri stå lenger nord eller sør enn jordaksens helning."""
    assert -23.5 <= sol.deklinasjon(dag) <= 23.5


def test_laveste_hoyde_midtsommer():
    """Kjernetallet: i Oslo kommer sola aldri under -6,65° ved midtsommer.

    Det er derfor lysstyring på solhøyde alene slår på midt på natta i juni.
    """
    assert sol.laveste_hoyde(date(2026, 6, 21), OSLO) == pytest.approx(-6.65, abs=0.1)


def test_lenger_nord_gir_lysere_netter():
    """Toten ligger nordligst og får den lyseste sommernatta."""
    d = date(2026, 6, 21)
    assert sol.laveste_hoyde(d, TOTEN) > sol.laveste_hoyde(d, OSLO)
    assert sol.laveste_hoyde(d, OSLO) > sol.laveste_hoyde(d, STROMSTAD)


def test_morketid_midtsommer_mot_midtvinter():
    assert sol.timer_under(date(2026, 6, 21), OSLO, -4.0) == pytest.approx(3.45, abs=0.2)
    assert sol.timer_under(date(2026, 12, 21), OSLO, -4.0) == pytest.approx(16.9, abs=0.3)


def test_sommersperre_ved_fem_timer():
    """Standardkravet hopper over den lyse sommeren, ikke hele året.

    Ved lavere krav enn fire timer slår sperren aldri inn i Oslo — sola ER under -4°
    i 3,45 timer selv ved midtsommer.
    """
    assert not sol.blir_morkt(date(2026, 6, 21), OSLO, -4.0, 5.0)
    assert sol.blir_morkt(date(2026, 4, 15), OSLO, -4.0, 5.0)
    assert sol.blir_morkt(date(2026, 8, 20), OSLO, -4.0, 5.0)
    # Med 1,5 time slår den aldri inn.
    assert sol.blir_morkt(date(2026, 6, 21), OSLO, -4.0, 1.5)


def test_hele_aret_uten_krasj():
    """Ingen dato skal gi unntak eller tall utenfor døgnet."""
    d = date(2026, 1, 1)
    while d.year == 2026:
        t = sol.timer_under(d, OSLO, -4.0)
        assert 0.0 <= t <= 24.0
        d += timedelta(days=1)


def test_polare_ytterpunkter():
    """Nord for polarsirkelen gir midnattssol og mørketid. Vi skal ikke kaste der."""
    assert sol.timer_under(date(2026, 6, 21), 78.0, -4.0) == 0.0     # Svalbard, midnattssol
    assert sol.timer_under(date(2026, 12, 21), 78.0, -4.0) == 24.0   # mørketid


# ---------------------------------------------------------------------- regler
def n(t: str) -> datetime:
    return datetime.combine(date(2026, 11, 10),
                            time(*[int(x) for x in t.split(":")]),
                            tzinfo=timezone.utc)


def kall(**kw):
    grunn = dict(naa=n("18:00"), hoyde=-8.0, star_paa=False, morkt_i_natt=True,
                 terskel_paa=-4.0, terskel_av=-2.5)
    grunn.update(kw)
    return regler.bor_lyse(**grunn)


def test_slar_paa_naar_det_blir_morkt():
    assert kall(hoyde=-5.0).paa is True


def test_ikke_paa_mens_det_er_lyst():
    assert kall(hoyde=2.0).paa is False


def test_hysterese_hindrer_blafring():
    """Mellom de to tersklene skjer ingenting — lyset beholder tilstanden sin.

    Uten dette ville et lys som nettopp slo på ved -4° slått seg av igjen ved -3,9°,
    og fram og tilbake gjennom hele tussmørket.
    """
    mellom = -3.0
    assert kall(hoyde=mellom, star_paa=False).paa is False
    assert kall(hoyde=mellom, star_paa=True).paa is True


def test_for_sent_paa_kvelden():
    """Blir det først mørkt etter grensen, dropper vi kvelden."""
    assert kall(naa=n("23:45"), hoyde=-8.0, senest_paa="23:30").paa is False


def test_lyset_star_natta_over():
    """Står lyset på fra i går kveld, slås det ikke av midt på natta."""
    s = kall(naa=n("02:00"), hoyde=-30.0, star_paa=True)
    assert s.paa is True
    assert "i går" in s.grunn


def test_slar_av_naar_det_lysner_om_morgenen():
    assert kall(naa=n("08:00"), hoyde=1.0, star_paa=True).paa is False


def test_morgenlys_paa_i_vinduet():
    assert kall(naa=n("07:00"), hoyde=-8.0, star_paa=False).paa is True


def test_for_tidlig_om_morgenen():
    """Før morgenvinduet tennes ikke lyset av seg selv."""
    assert kall(naa=n("04:00"), hoyde=-25.0, star_paa=False).paa is False


def test_sommersperre_gjelder_kvelden():
    s = kall(hoyde=-5.0, morkt_i_natt=False)
    assert s.paa is False
    assert "sommer" in s.grunn.lower()


def test_bryterne_slar_av_hver_sin_del():
    assert kall(hoyde=-8.0, kveld_aktiv=False).paa is False
    assert kall(naa=n("07:00"), hoyde=-8.0, morgen_aktiv=False).paa is False
    # Kveldsbryteren skal ikke påvirke morgenen.
    assert kall(naa=n("07:00"), hoyde=-8.0, kveld_aktiv=False).paa is True


# --------------------------------------------------------------- skyjustering
def test_skydekke_flytter_terskelen_oppover():
    """Overskyet gjør at lyset tennes tidligere."""
    klar = regler.sky_terskel(-4.0, 0, 1.5)
    halvt = regler.sky_terskel(-4.0, 50, 1.5)
    tett = regler.sky_terskel(-4.0, 100, 1.5)
    assert klar == -4.0
    assert halvt == pytest.approx(-3.25)
    assert tett == pytest.approx(-2.5)


def test_skydekke_som_mangler_endrer_ingenting():
    assert regler.sky_terskel(-4.0, None, 1.5) == -4.0
    assert regler.sky_terskel(-4.0, "tull", 1.5) == -4.0


def test_overskyet_tenner_tidligere():
    """Samme solhøyde, ulikt skydekke: bare den overskyede tenner."""
    h = -3.0
    assert kall(hoyde=h, skydekke=0, sky_justering=1.5).paa is False
    assert kall(hoyde=h, skydekke=100, sky_justering=1.5).paa is True


# ------------------------------------------------------------------ hele døgn
def test_et_novemberdogn():
    """Gjennom et døgn i november skal lyset gå på én gang og av én gang."""
    paa = False
    bytter = []
    for t in range(0, 24 * 60, 10):
        naa = datetime.combine(date(2026, 11, 10), time(t // 60, t % 60),
                               tzinfo=timezone.utc)
        # grov solhøyde: opp fra 08, ned fra 15
        minutter = t
        if 480 <= minutter <= 900:
            h = 8.0
        else:
            h = -10.0
        ny = regler.bor_lyse(naa=naa, hoyde=h, star_paa=paa, morkt_i_natt=True,
                             terskel_paa=-4.0, terskel_av=-2.5).paa
        if ny != paa:
            bytter.append((naa.strftime("%H:%M"), ny))
            paa = ny
    # Natt til morgen: på ved start, av når det lysner, på igjen om kvelden.
    assert len(bytter) <= 3, f"for mange bytter: {bytter}"
    assert any(b[1] is False for b in bytter), "lyset slås aldri av"
    assert any(b[1] is True for b in bytter), "lyset slås aldri på"


# --------------------------------------------------- klokkeslett, ikke bare vinkler
def test_tidspunkt_stemmer_med_virkeligheten():
    """Sebastian så på kamera at lyset burde tennes rundt 20:00 og slukkes 06:29.

    Den gamle utregningen antok at solmidnatt er klokka 00:00, og bommet med over en
    time: den sa 18:39 og 05:32. Lengdegrad og tidsligning er det som manglet.
    """
    from datetime import timezone as tz
    CEST = tz(timedelta(hours=2))
    ned = sol.naar_krysser(datetime(2026, 9, 19, 12, 0, tzinfo=CEST),
                           OSLO, -4.0, synkende=True, lengdegrad=10.75)
    opp = sol.naar_krysser(datetime(2026, 9, 20, 2, 0, tzinfo=CEST),
                           OSLO, -4.0, synkende=False, lengdegrad=10.75)
    assert ned.hour == 19 and 45 <= ned.minute <= 59, f"fikk {ned}"
    assert opp.hour == 6 and 20 <= opp.minute <= 40, f"fikk {opp}"


def test_lengdegrad_flytter_tidspunktet():
    """Lenger vest betyr senere solnedgang på klokka."""
    from datetime import timezone as tz
    CEST = tz(timedelta(hours=2))
    naa = datetime(2026, 9, 19, 12, 0, tzinfo=CEST)
    oslo = sol.naar_krysser(naa, OSLO, -4.0, True, lengdegrad=10.75)
    vest = sol.naar_krysser(naa, OSLO, -4.0, True, lengdegrad=5.32)   # Bergen
    assert vest > oslo


def test_tidsligningen_har_riktig_fortegn():
    """Sola kommer for tidlig i slutten av oktober, for sent i midten av februar."""
    assert sol.tidsligning(date(2026, 10, 30)) > 10
    assert sol.tidsligning(date(2026, 2, 11)) < -12


def test_ingen_kryssing_gir_none():
    """Midnattssol på Svalbard: terskelen krysses aldri."""
    from datetime import timezone as tz
    naa = datetime(2026, 6, 21, 12, 0, tzinfo=tz(timedelta(hours=2)))
    assert sol.naar_krysser(naa, 78.0, -4.0, True, lengdegrad=15.6) is None
