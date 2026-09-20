"""Navn og standardverdier for KI Utelys."""
from __future__ import annotations

DOMAIN = "ki_utelys"

# --- oppsett ---------------------------------------------------------------
CONF_LYS = "lys"
CONF_TERSKEL_PAA = "terskel_paa"
CONF_TERSKEL_AV = "terskel_av"
CONF_MINST_MORKE = "minst_morke"
CONF_SENEST_PAA = "senest_paa"
CONF_TIDLIGST_AV = "tidligst_av"
CONF_MORGEN_AV = "morgen_av"
CONF_MORGEN_PAA = "morgen_paa"
CONF_VAER = "vaer"
CONF_SKY_JUSTERING = "sky_justering"

STANDARD = {
    # Solhøyden der en typisk fotocelle slår på. Borgerlig tussmørke er -6°, men en
    # fotocelle reagerer tidligere — den ser at det er blitt grått, ikke at det er natt.
    CONF_TERSKEL_PAA: -4.0,
    # Av litt høyere enn på. To ulike verdier hindrer blafring rundt terskelen, og at
    # den slår av litt etter at den slo på er nettopp slik en fotocelle oppfører seg.
    CONF_TERSKEL_AV: -2.5,
    # Krav til sammenhengende mørketid før vi bryr oss. 5 timer hopper over omtrent
    # 23. mai til 20. juli i Oslo. Sett 0 for å aldri hoppe over.
    #
    # Tallet er ikke opplagt: ved midtsommer i Oslo er sola under -4° i 3,45 timer, så
    # en lavere grense enn 4 slår aldri inn i det hele tatt.
    CONF_MINST_MORKE: 5.0,
    # Klokkegrenser. «Senest på» hindrer at lyset tennes midt på natta når det først
    # blir mørkt sent; «morgen av» at det står på til langt ut på formiddagen i november.
    CONF_SENEST_PAA: "23:30",
    CONF_TIDLIGST_AV: "05:00",
    CONF_MORGEN_PAA: "05:30",
    CONF_MORGEN_AV: "09:00",
    # Skydekke kan flytte terskelen opptil så mange grader oppover. 1,5° svarer til
    # rundt 20 minutter tidligere på en overskyet ettermiddag i oktober.
    CONF_SKY_JUSTERING: 1.5,
}

# --- entiteter -------------------------------------------------------------
SWITCHES = [
    ("ki_utelys_auto", "KI Utelys Automatikk", True, "mdi:lightbulb-auto"),
    ("ki_utelys_morgen", "KI Utelys Morgen", True, "mdi:weather-sunset-up"),
    ("ki_utelys_kveld", "KI Utelys Kveld", True, "mdi:weather-sunset-down"),
]

NUMBERS = [
    ("ki_utelys_terskel_paa", "KI Utelys Terskel På", -12.0, 6.0, 0.5, "°",
     STANDARD[CONF_TERSKEL_PAA], "mdi:weather-sunset-down"),
    ("ki_utelys_terskel_av", "KI Utelys Terskel Av", -12.0, 6.0, 0.5, "°",
     STANDARD[CONF_TERSKEL_AV], "mdi:weather-sunset-up"),
    ("ki_utelys_minst_morke", "KI Utelys Minste Mørketid", 0.0, 10.0, 0.5, "t",
     STANDARD[CONF_MINST_MORKE], "mdi:weather-night"),
]

SENSORS = [
    ("ki_utelys_status", "KI Utelys Status", "mdi:lightbulb-auto"),
    ("ki_utelys_neste_paa", "KI Utelys Neste På", "mdi:weather-sunset-down"),
    ("ki_utelys_neste_av", "KI Utelys Neste Av", "mdi:weather-sunset-up"),
]
