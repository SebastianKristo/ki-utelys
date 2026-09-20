# KI Utelys 1.1.0

## Tidene bommet med over en time

Kortet sa at lyset ville tennes 18:39 og slukkes 05:32. Sebastian så på kamera at det
ikke var mørkt nok før rundt 20:00, og lyst igjen 06:29.

Terskelen var ikke problemet. 18:39 svarer til solhøyde **+5,18°** — sola sto godt over
horisonten. Terskelen på −4° inntreffer 19:53, som er det han observerte.

Feilen lå i utregningen av **når** terskelen nås. Den antok at solmidnatt er klokka
00:00, og manglet to ting:

**Lengdegraden.** Oslo ligger på 10,75° øst, mens tidssonen regnes fra 15° øst. Det
alene er 17 minutter.

**Tidsligningen.** Jorda går ikke jevnt rundt sola, og aksen står skrått. Sola kommer
opptil 16 minutter for tidlig i slutten av oktober og 14 minutter for sent i midten av
februar.

Til sammen ble det over en time på feil side.

### Regnet fram i stedet for utledet

Vi leter oss nå minutt for minutt gjennom døgnet i stedet for å regne buen direkte. Det
er 1440 utregninger i stedet for én, og fortsatt under et millisekund — men vi slipper å
anta noe om når solmidnatt inntreffer.

Lengdegraden hentes fra Home Assistants egen posisjon, som breddegraden. Tidssonen tas
fra datoen, så sommertid følger med av seg selv.

### Etter rettelsen

| | Før | Nå | Observert |
| --- | --- | --- | --- |
| Tennes | 18:39 | **19:53** | ~20:00 |
| Slukkes | 05:32 | **06:30** | 06:29 |

### Tester

69 nå. Fire nye: tidspunktene mot Sebastians observasjon, at lengdegraden flytter
tidspunktet, at tidsligningen har riktig fortegn, og at midnattssol gir «ingen
kryssing» i stedet for et tall.

---

# KI Utelys 1.0.1

Ikon og dokumentasjon. Ingen endring i logikken.

## Ikon

Veggmontert utelampe med lyskjegle, og sola halvveis under horisonten — det er den
solhøyden integrasjonen måler.

`brand/` inneholder `icon.svg` for README-en, og `icon.png`, `icon@2x.png`, `logo.png`
og `logo@2x.png` i de størrelsene brands-repoet krever.

## Ikonet vises ikke i Home Assistant ennå

Det er verdt å si tydelig: **Home Assistant leser ikke ikoner fra integrasjonsmappa.**
Ikonet i Enheter og tjenester hentes fra `brands.home-assistant.io`, og for
egendefinerte integrasjoner må det sendes inn til `home-assistant/brands`.

Framgangsmåten står i README-en. Fram til pull requesten er godtatt viser HA et
standardikon — rent kosmetisk, integrasjonen virker likt.

---

# KI Utelys 1.0.0

Første utgave. Utelys som en fotocelle, tilpasset norske sommernetter: solhøyde med
hysterese, sommersperre som hopper over de lyse nettene, og skydekke som justerer
terskelen. 65 tester.
