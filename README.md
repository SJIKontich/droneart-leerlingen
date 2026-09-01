# Drone-show — leerlingenrepo

Welkom! In deze repo vind je alles om lokaal aan de slag te gaan met de drone-show.

## Installatie (eenmalig)

1. **Clone deze repo** in PyCharm via *File → New Project from VCS* en plak de URL:
   ```
   https://github.com/SJIKontich/droneart-leerlingen.git
   ```
2. **Installeer pygame**: PyCharm toont automatisch een melding *"Package requirements not satisfied"* → klik **Install**.

Dat is alles. Je bent klaar om te starten.

## Aan de slag

Maak een nieuw bestand aan per hoofdstuk of per oefening, bijvoorbeeld `h1.py` of `h1-oef1.py`. Kijk in `voorbeeld.py` hoe je begint:

```python
from drone_engine import *

zet_drone(1, 0, 0, "rood")
nieuwe_scene()
start_show()
```

> **Let op:** geef je bestanden altijd een naam die begint met `mijn_` (bv. `mijn_h1.py`) of start met h0, h1, ....
> Zo worden ze nooit meegestuurd naar GitHub en kom je nooit in conflict met updates.

## Updates ontvangen

Als er een update is aan `drone_engine.py`, doe je in PyCharm:
*Git → Pull* (of de blauwe pijl rechtsboven)
