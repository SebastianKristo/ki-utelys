# KI Utelys 1.0.0

Første utgave. Utelys som en fotocelle, tilpasset norske sommernetter.

## Hvorfor den finnes

Styring på solnedgang eller ren solhøyde tenner utelysene 22:45 i juni. Det er riktig
etter regelen og feil i praksis.

## Hva den gjør

**Solhøyde med hysterese.** På ved −4°, av ved −2,5°. To ulike verdier hindrer blafring
i tussmørket, og at den slår av litt senere enn den slo på er slik en fotocelle
oppfører seg.

**Sommersperre.** Blir den mørke perioden kortere enn kravet, hoppes natta over.
Standard er 5 timer, som gir av fra 23. mai til 20. juli i Oslo.

Tallet er ikke gjettet: ved midtsommer er sola under −4° i 3,45 timer, så et krav under
fire timer ville aldri slått inn. Det oppdaget jeg da jeg testet, etter å ha antatt noe
annet.

**Skydekke justerer terskelen** opptil 1,5° når en værentitet er satt opp. En overskyet
ettermiddag i oktober blir mørk rundt 20 minutter før solhøyden alene sier.

**Klokkegrenser:** senest på, tidligst av, og et morgenvindu.

**Breddegraden kommer fra Home Assistant**, så de tre stedene regnes hver for seg uten
oppsett. Strömstad får lengre mørke enn Toten.

## Entiteter

Tre brytere, tre tall og tre sensorer. Statussensoren gir begrunnelsen, ikke bare av
eller på.

## Tester

65 stykker, uten at Home Assistant må startes. Solgeometrien er sjekket mot fasit,
hele året kjøres gjennom, og Svalbard med midnattssol og mørketid gir riktig svar.

## Merk

Integrasjonen slår ikke av lys du har tent selv, og tar ikke hensyn til om noen er
hjemme — det siste hører hjemme i en automasjon som kan skru av `ki_utelys_auto`.
