# KI Utelys

Utelys som en fotocelle, tilpasset norske sommernetter.

Solhøyden avgjør, ikke klokka. Lysene går på når det begynner å bli mørkt — omtrent når
en lyspære med fotosensor ville slått seg på — og av når det lysner.

## Hvorfor ikke bare soloppgang og solnedgang

I Oslo kommer sola aldri lenger ned enn **−6,65°** ved midtsommer. Borgerlig tussmørke er
−6°, så det blir så vidt mørkt nok, i 3,45 timer rundt midnatt.

Styrer du på solnedgang, tennes lysene 22:45 i juni. Styrer du på solhøyde alene, skjer
det samme. Begge deler er riktig etter regelen og feil i praksis.

Derfor har integrasjonen en **sommersperre**: blir den mørke perioden kortere enn et
antall timer du setter, hoppes natta over.

| Krav til mørketid | Dager som hoppes over i Oslo |
| --- | --- |
| 1,5 t | ingen |
| 3 t | ingen |
| 4 t | 5. juni – 7. juli |
| **5 t (standard)** | **23. mai – 20. juli** |
| 6 t | 12. mai – 1. august |

Tallene er regnet ut, ikke gjettet. Under fire timer slår sperren aldri inn, fordi sola
faktisk ER under terskelen i 3,45 timer ved midtsommer.

## Hysterese

**På ved −4°, av ved −2,5°.** To ulike verdier hindrer at lyset blafrer rundt terskelen i
tussmørket, og at det slår av litt senere enn det slo på er nettopp slik en fotocelle
oppfører seg.

## Skydekke i stedet for lux-sensor

En overskyet ettermiddag i oktober blir mørk tidligere enn solhøyden sier. Peker du på en
værentitet med `cloud_coverage`, flyttes terskelen opptil 1,5° oppover ved fullt skydekke
— rundt 20 minutter tidligere.

Har du en ekte lux-sensor, er den bedre enn dette. Si fra, så legger vi den inn.

## Entiteter

**Brytere:** `ki_utelys_auto`, `ki_utelys_morgen`, `ki_utelys_kveld` — alle husker
stillingen over omstart.

**Tall:** `ki_utelys_terskel_paa`, `ki_utelys_terskel_av`, `ki_utelys_minst_morke`.

**Sensorer:** `ki_utelys_status` med begrunnelse, `ki_utelys_neste_paa` og
`ki_utelys_neste_av`.

Statussensoren sier ikke bare «av», men hvorfor — «lys sommernatt, hopper over» eller
«for sent på kvelden». Da ser du at automatikken lever i stedet for å lure.

## Tre steder

Installeres på hver instans. Breddegraden hentes fra Home Assistants egen posisjon, så
Toten (60,68°), Oslo (59,91°) og Strömstad (58,93°) får hver sin utregning uten at noe
må settes opp.

## Det den ikke gjør

**Slår ikke av lys du har tent selv.** Vi husker om det var vi som slo på, og rører det
ellers ikke.

**Tar ikke hensyn til om noen er hjemme.** Det er en annen beslutning, og den hører
hjemme i en annen automasjon som kan slå av `ki_utelys_auto`.

## Tester

65 stykker. Solgeometrien er sjekket mot fasit ved solverv og jevndøgn, hele året kjøres
gjennom uten unntak, og polare ytterpunkter — midnattssol og mørketid på Svalbard — gir
riktig svar i stedet for å kaste.
