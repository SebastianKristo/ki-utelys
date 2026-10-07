# KI Utelys 1.2.0

## Lysene sto på hele tiden

Regelen «vi slår bare av det vi slo på» sto alene, og låste seg:

Et lys som noen tente for hånd — eller som sto på da Home Assistant startet på nytt — var
ikke «vårt». Om kvelden sa reglene «på», men lyset sto jo alt på, så vi tente ingenting
og tok det heller ikke. Om morgenen sa reglene «av», men det var ikke vårt, så det ble
stående. Døgn etter døgn. Minnet om hva som var vårt lå dessuten bare i arbeidsminnet,
så hver omstart gjorde alle lysene fremmede.

### Rettet

- **Overtakelse.** Sier reglene «på» og lyset står på, overtar automatikken det. Vi hadde
  tent det uansett, så vi skal også slukke det.
- **Manuelt er ikke evig.** Et lys noen andre har tent mens reglene sier av, får stå i
  inntil 12 timer. Etter det er det ikke et valg lenger, det er glemt — og det slukkes.
- **Lagres.** Hva som er vårt, og siden når et lys har stått på manuelt, lagres i
  `.storage/ki_utelys.<entry>` og overlever omstart.
- `sensor.ki_utelys_status` har fått attributtet `lys` med `vaart`, `manuell_siden` og
  `grunn` per lys, så man ser hvorfor et lys står som det står.

### Kontrollert

76 tester, 7 nye: avgjørelsen per lys som ren funksjon (overtakelse, slukking av vårt,
manuelt lys som står og så slukkes etter 12 t, hele døgnet som låste seg), og to tester i en
ekte Home Assistant-testinstans — et lys som sto på fra før blir overtatt om kvelden og
slukket om morgenen, og et manuelt tent lys slukkes etter 12 timer. Home Assistant 2025.12.5.
