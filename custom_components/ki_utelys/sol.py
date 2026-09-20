"""Solgeometri: hvor lavt sola kommer i natt, og hvor lenge den er under terskelen.

Dette er kjernen i sommersperren. Home Assistant forteller solhøyden NÅ, men for å vite
om det i det hele tatt blir mørkt i natt må vi regne framover — og da holder det ikke å
spørre `sun.sun`.

Regnestykket er rent geometrisk og trenger ingen nettverkstilgang:

    laveste solhøyde i natt = deklinasjon - (90° - breddegrad)

Deklinasjonen er hvor langt nord eller sør sola står i forhold til ekvator, og varierer
mellom ±23,44° gjennom året. Ved midtsommer i Oslo (59,91°) gir det

    23,44 - (90 - 59,91) = -6,65°

altså at sola aldri kommer lenger ned enn 6,65 grader under horisonten. Det er så vidt
under borgerlig tussmørke (-6°), og forklarer hvorfor lysstyring på solhøyde alene slår
på midt på natta i juni.

Nøyaktigheten er rundt en fjerdedels grad, som svarer til et par minutter i tid. Mer
presisjon ville ikke endret noen beslutning her: forskjellen på å slå på lyset 20:14 og
20:16 er ingen.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

# Jordaksens helning. Setter grensen for hvor høyt og lavt sola kan stå.
AKSEHELNING = 23.44


def deklinasjon(dag: date) -> float:
    """Solens deklinasjon i grader for en gitt dato.

    Den enkle kosinusformelen bommer med nesten en hel grad rundt jevndøgn — omtrent
    sju minutter i tid — fordi jordbanen ikke er en sirkel. Her er banens eksentrisitet
    med, og da er avviket under 0,3° hele året — rundt to minutter i tid.

    Formelen er den vanlige tilnærmingen:

        δ = asin( sin(-23,44°) · cos(360/365,24·(N+10) + 1,914·sin(360/365,24·(N-2))) )

    der leddet med 1,914 er korreksjonen for at jorda går fortere i banen nær perihel i
    januar enn nær aphel i juli.
    """
    n = dag.timetuple().tm_yday
    # 10 dager forskyver året fra 1. januar til vintersolverv 21. desember.
    a = math.radians(360 / 365.24 * (n + 10))
    # 2 dager fra nyttår til perihel, der jorda er nærmest sola.
    b = math.radians(360 / 365.24 * (n - 2))
    vinkel = a + math.radians(1.914) * math.sin(b)
    return math.degrees(math.asin(math.sin(math.radians(-AKSEHELNING)) * math.cos(vinkel)))


def laveste_hoyde(dag: date, breddegrad: float) -> float:
    """Hvor lavt sola kommer ved solmidnatt, i grader.

    Negativt tall betyr under horisonten. Jo lenger nord, jo mindre negativt om sommeren
    — det er derfor Strömstad (58,9°) får litt lengre mørke enn Toten (60,7°).
    """
    return deklinasjon(dag) - (90.0 - abs(breddegrad))


def hoyeste_hoyde(dag: date, breddegrad: float) -> float:
    """Hvor høyt sola kommer midt på dagen. Brukt for mørketid om vinteren."""
    return 90.0 - abs(breddegrad) + deklinasjon(dag)


def timer_under(dag: date, breddegrad: float, terskel: float) -> float:
    """Hvor mange timer sola er under `terskel` i løpet av døgnet.

    Brukes til sommersperren: er den mørke perioden kortere enn det man orker å slå på
    lys for, hopper vi over natta.

    Timevinkelen der sola krysser terskelen kommer fra

        cos(H) = (sin(h) - sin(φ)·sin(δ)) / (cos(φ)·cos(δ))

    der h er terskelen, φ breddegraden og δ deklinasjonen. Er brøken utenfor [-1, 1],
    krysser sola aldri terskelen: enten er den under hele døgnet (mørketid) eller over
    hele døgnet (midnattssol).
    """
    fi = math.radians(abs(breddegrad))
    d = math.radians(deklinasjon(dag))
    h = math.radians(terskel)

    nevner = math.cos(fi) * math.cos(d)
    if abs(nevner) < 1e-9:
        return 0.0 if terskel > 0 else 24.0

    x = (math.sin(h) - math.sin(fi) * math.sin(d)) / nevner
    if x <= -1:
        # Sola er over terskelen hele døgnet.
        return 0.0
    if x >= 1:
        # Sola er under terskelen hele døgnet.
        return 24.0

    # H er halve buen sola står OVER terskelen, i grader.
    H = math.degrees(math.acos(x))
    timer_over = 2 * H / 15.0
    return max(0.0, 24.0 - timer_over)


def blir_morkt(dag: date, breddegrad: float, terskel: float,
               minst_timer: float = 1.5) -> bool:
    """Er det verdt å slå på lys i natt?

    To krav: sola må faktisk komme under terskelen, og den må bli der lenge nok. Uten
    det andre kravet ville lysene blinket på i tjue minutter rundt midnatt i juni.
    """
    if laveste_hoyde(dag, breddegrad) >= terskel:
        return False
    return timer_under(dag, breddegrad, terskel) >= minst_timer


def naar_krysser(naa: datetime, breddegrad: float, terskel: float,
                 synkende: bool) -> datetime | None:
    """Når krysser sola terskelen neste gang, på vei ned eller opp?

    Brukes til å fortelle når lyset slår seg på og av i kveld, slik at man ser det i
    stedet for å lure på om automasjonen lever.

    Returnerer None når sola ikke krysser terskelen det døgnet — midnattssol, mørketid,
    eller en sommernatt der det aldri blir mørkt nok.
    """
    dag = naa.date()
    timer = timer_under(dag, breddegrad, terskel)
    if timer <= 0 or timer >= 24:
        return None

    # Solmidnatt og solmiddag som utgangspunkt. Vi bruker lokal tid slik HA oppgir den;
    # tidsligningen bommer med opptil ~16 minutter, og det tåler vi her.
    halv_morke = timer / 2.0
    midnatt = datetime.combine(dag, datetime.min.time(), tzinfo=naa.tzinfo)

    if synkende:
        # Sola går under terskelen halve mørkeperioden før midnatt.
        tid = midnatt + timedelta(hours=24 - halv_morke)
        if tid <= naa:
            tid += timedelta(days=1)
    else:
        tid = midnatt + timedelta(hours=halv_morke)
        if tid <= naa:
            tid += timedelta(days=1)
    return tid
