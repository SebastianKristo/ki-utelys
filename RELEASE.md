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
