"""
Drone-show engine  --  VERBORGEN voor de leerlingen.

Dit bestand bevat de "motor" van de drone-show: het venster, het tekenen van de
gloeiende lichtpunten en de vloeiende overgangen tussen scenes.

De leerlingen hoeven dit bestand NIET te begrijpen of aan te passen.
Zij gebruiken enkel deze eenvoudige commando's (zie show.py):

    zet_drone(nummer, x, y, kleur)   ->  plaats een drone op (x, y) met een kleur
    nieuwe_scene(duur=2.0)           ->  leg de huidige stand vast; de engine
                                         animeert vloeiend naar deze stand
    wacht(seconden)                  ->  houd de laatste scene even vast
    start_show()                     ->  toon de show

Wiskundige hulp (uit de math-bibliotheek) is meteen beschikbaar:
    pi, sin, cos, sqrt, tan, atan2, radians, degrees
"""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # geen pygame-banner in de uitvoer

from math import pi, sin, cos, sqrt, tan, atan2, radians, degrees

# numpy en pygame zijn enkel nodig voor de GRAFISCHE show. In een omgeving
# zonder die bibliotheken (bv. CodeRunner in Moodle) schakelt de engine
# automatisch over naar TEKSTMODUS, zodat exact dezelfde leerlingcode werkt.
#
# numpy staat LOS van pygame: de Matrix-class (hoofdstuk 5) gebruikt numpy als
# die er is, en valt anders terug op pure Python. Zo werken de matrix-oefeningen
# ook in CodeRunner, met of zonder numpy op de server.
try:
    import numpy as np
    _NUMPY = True
except ImportError:
    _NUMPY = False

try:
    import pygame
    _GRAFISCH = _NUMPY      # de grafische show vereist zowel numpy als pygame
except ImportError:
    _GRAFISCH = False

__all__ = [
    "zet_drone", "nieuwe_scene", "wacht", "start_show",
    "geef_drones", "aantal_scenes", "lees_drones", "schrijf_drones", "Matrix",
    "pi", "sin", "cos", "sqrt", "tan", "atan2", "radians", "degrees",
]

# ---------------------------------------------------------------------------
# Instellingen van het venster en de "wereld"
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1000, 750      # grootte van het venster in pixels
SCALE = 55                     # aantal pixels per wiskundige eenheid
FPS = 60                       # beelden per seconde

# Kleurnamen (Nederlands) -> RGB
KLEUREN = {
    "rood":    (255, 60, 60),
    "groen":   (60, 220, 90),
    "blauw":   (70, 120, 255),
    "geel":    (255, 220, 60),
    "cyaan":   (60, 230, 230),
    "magenta": (240, 70, 220),
    "oranje":  (255, 150, 40),
    "paars":   (170, 90, 240),
    "roze":    (255, 130, 190),
    "wit":     (255, 255, 255),
    "uit":     (0, 0, 0),
    "zwart":   (0, 0, 0),
}

# ---------------------------------------------------------------------------
# Interne toestand (de leerlingen zien dit niet)
# ---------------------------------------------------------------------------
_buffer = {}      # huidige stand die wordt opgebouwd: nummer -> (x, y, (r,g,b))
_keyframes = []   # lijst van vastgelegde scenes: [{"state":..., "duur":..., "hold":...}]

# Omgekeerde tabel (RGB -> naam) voor de tekstmodus
_NAMEN = {}
for _naam, _rgb in KLEUREN.items():
    _NAMEN.setdefault(_rgb, _naam)


def _naar_rgb(kleur):
    """Zet een kleurnaam of (r, g, b)-tuple om naar een RGB-tuple."""
    if isinstance(kleur, tuple):
        return kleur
    if kleur not in KLEUREN:
        raise ValueError(
            f"Onbekende kleur: {kleur!r}. Kies uit: {', '.join(KLEUREN)}"
        )
    return KLEUREN[kleur]


def _kleurnaam(rgb):
    """Geef de kleurnaam terug die bij een RGB-tuple hoort (voor de tekstmodus)."""
    return _NAMEN.get(tuple(rgb), str(tuple(rgb)))


def _fmt(getal):
    """Formatteer een getal op 2 decimalen, zonder lelijke '-0.00'."""
    afgerond = round(getal, 2) + 0.0
    return f"{afgerond:.2f}"


# ---------------------------------------------------------------------------
# De commando's voor de leerlingen
# ---------------------------------------------------------------------------
def zet_drone(nummer, x, y, kleur="wit"):
    """Plaats drone `nummer` op positie (x, y) met de gegeven kleur."""
    _buffer[nummer] = (float(x), float(y), _naar_rgb(kleur))


def nieuwe_scene(duur=2.0):
    """Leg de huidige stand van alle drones vast als een nieuwe scene.

    De engine animeert nadien vloeiend van de vorige scene naar deze scene
    over `duur` seconden.
    """
    _keyframes.append({
        "state": dict(_buffer),   # een kopie van de huidige stand
        "duur": float(duur),
        "hold": 0.0,
    })


def wacht(seconden):
    """Houd de laatst vastgelegde scene `seconden` lang stil op het scherm."""
    if not _keyframes:
        raise RuntimeError("wacht() kan pas na een nieuwe_scene().")
    _keyframes[-1]["hold"] += float(seconden)


def geef_drones():
    """Geef de huidige stand van de drones terug.

    Een lijst van tuples (nummer, x, y, kleur), gesorteerd op nummer.
    Handig om in testcode te controleren waar elke drone staat.
    """
    resultaat = []
    for nummer in sorted(_buffer):
        x, y, rgb = _buffer[nummer]
        resultaat.append((nummer, round(x, 2) + 0.0, round(y, 2) + 0.0, _kleurnaam(rgb)))
    return resultaat


def aantal_scenes():
    """Geef het aantal vastgelegde scenes terug (telt elke `nieuwe_scene()`).

    Handig in testcode om te controleren dat een show uit het juiste aantal
    scenes bestaat. Is er nog geen enkele scene vastgelegd, dan telt de huidige
    stand als 1 (net zoals `start_show()` ze dan toont).
    """
    return len(_keyframes) if _keyframes else 1


# ---------------------------------------------------------------------------
# Data van buitenaf (hoofdstuk 7)  --  CSV inlezen / wegschrijven
#
# Een drone-show wordt vaak niet "in code" getekend, maar uit een bestand
# geladen (de ontwerper is niet altijd de programmeur). Deze twee helpers
# verbergen het bestand-gedoe (openen, regels lezen, tekst -> getal, regeleinde
# wegknippen), zodat de leerlingcode een eenvoudige for-lus blijft:
#
#     drones = lees_drones("hart.csv")
#     for drone in drones:
#         nummer, x, y, kleur = drone
#         zet_drone(nummer, x, y, kleur)
# ---------------------------------------------------------------------------
def lees_drones(bestandsnaam):
    """Lees een formatie uit een CSV-bestand.

    Het bestand heeft per drone één regel met drie waarden, gescheiden door
    komma's:  x,y,kleur   (bijvoorbeeld  3,0,rood ).

    Geeft een lijst van tuples (nummer, x, y, kleur) terug, in dezelfde volgorde
    als de regels in het bestand. `nummer` is de regelvolgorde (0, 1, 2, ...),
    `x` en `y` zijn floats en `kleur` is een opgekuiste kleurnaam (string).
    Dit is dezelfde vorm als geef_drones(), zodat de leerlingcode een eenvoudige
    for-lus blijft.

    Een eventuele headerregel (x,y,kleur), lege regels en regels die met '#'
    beginnen, worden overgeslagen.
    """
    resultaat = []
    nummer = 0
    with open(bestandsnaam) as bestand:
        for regel in bestand:
            regel = regel.strip()
            if not regel or regel.startswith("#"):
                continue
            delen = regel.split(",")
            if len(delen) < 3:
                continue
            try:
                x = float(delen[0].strip())
                y = float(delen[1].strip())
            except ValueError:
                continue          # bv. een headerregel: "x,y,kleur"
            kleur = delen[2].strip()
            resultaat.append((nummer, x, y, kleur))
            nummer += 1
    return resultaat


def schrijf_drones(bestandsnaam):
    """Schrijf de huidige dronestand weg naar een CSV-bestand.

    Schrijft per drone één regel  x,y,kleur  (gesorteerd op nummer), zodat het
    bestand later weer met lees_drones() ingelezen kan worden. Handig om een
    zelfgemaakte of bewerkte formatie te bewaren (de uitvoer-kant van data).
    """
    with open(bestandsnaam, "w") as bestand:
        for nummer in sorted(_buffer):
            x, y, rgb = _buffer[nummer]
            bestand.write(f"{_fmt(x)},{_fmt(y)},{_kleurnaam(rgb)}\n")


# ---------------------------------------------------------------------------
# Matrix  --  een eenvoudige matrix voor hoofdstuk 5 (transformaties)
#
# Bedoeld om de leerlingen een matrix te laten benaderen als "een rooster van
# getallen met rijen en kolommen". Ze bouwen er een matrix mee op (setRij /
# setKolom), lezen ze uit (getRij / getKolom) en vermenigvuldigen ze met de
# operator @ (R @ P), net zoals in de wiskunde. De zware rekenkundige
# bibliotheek (numpy) zit verborgen; is numpy er niet, dan rekent de class in
# pure Python verder. Zo werkt dezelfde leerlingcode overal.
# ---------------------------------------------------------------------------
class Matrix:
    """Een matrix met `rijen` rijen en `kolommen` kolommen.

        M = Matrix(2, 5)          # nulmatrix: 2 rijen, 5 kolommen
        M = Matrix([[1, 2], [3, 4]])   # rechtstreeks uit een lijst van rijen

    Methodes voor de leerlingen:
        M.getRij(i)        -> de i-de rij als lijst
        M.setRij(i, lijst) -> zet de i-de rij
        M.getKolom(j)      -> de j-de kolom als lijst
        M.setKolom(j, lijst)-> zet de j-de kolom
        R @ P              -> matrixproduct (een nieuwe Matrix)
        print(M)           -> nette weergave (handig om te controleren)
    """

    def __init__(self, rijen, kolommen=None):
        if kolommen is None:
            # rijen is een lijst van rijen (een lijst van lijsten)
            self._data = [[float(w) for w in rij] for rij in rijen]
            self.rijen = len(self._data)
            self.kolommen = len(self._data[0]) if self._data else 0
        else:
            self.rijen = int(rijen)
            self.kolommen = int(kolommen)
            self._data = [[0.0] * self.kolommen for _ in range(self.rijen)]

    def getRij(self, i):
        """Geef rij `i` terug als een (nieuwe) lijst."""
        return list(self._data[i])

    def setRij(self, i, waarden):
        """Zet rij `i` op `waarden` (een lijst met `kolommen` getallen)."""
        waarden = list(waarden)
        if len(waarden) != self.kolommen:
            raise ValueError(
                f"setRij: rij {i} heeft {self.kolommen} waarden nodig, "
                f"maar je gaf er {len(waarden)}."
            )
        self._data[i] = [float(w) for w in waarden]

    def getKolom(self, j):
        """Geef kolom `j` terug als een (nieuwe) lijst (bv. [x, y] voor drone j)."""
        return [self._data[r][j] for r in range(self.rijen)]

    def setKolom(self, j, waarden):
        """Zet kolom `j` op `waarden` (een lijst met `rijen` getallen)."""
        waarden = list(waarden)
        if len(waarden) != self.rijen:
            raise ValueError(
                f"setKolom: kolom {j} heeft {self.rijen} waarden nodig, "
                f"maar je gaf er {len(waarden)}."
            )
        for r in range(self.rijen):
            self._data[r][j] = float(waarden[r])

    def __matmul__(self, andere):
        """Matrixproduct  self @ andere  -> een nieuwe Matrix."""
        if not isinstance(andere, Matrix):
            return NotImplemented
        if self.kolommen != andere.rijen:
            raise ValueError(
                f"Kan {self.rijen}x{self.kolommen} niet vermenigvuldigen met "
                f"{andere.rijen}x{andere.kolommen}: het aantal kolommen links "
                f"moet gelijk zijn aan het aantal rijen rechts."
            )
        if _NUMPY:
            product = np.array(self._data) @ np.array(andere._data)
            return Matrix(product.tolist())
        # Pure-Python-terugval (numpy ontbreekt, bv. op een kale server).
        uit = Matrix(self.rijen, andere.kolommen)
        for i in range(self.rijen):
            for j in range(andere.kolommen):
                som = 0.0
                for k in range(self.kolommen):
                    som += self._data[i][k] * andere._data[k][j]
                uit._data[i][j] = som
        return uit

    def __repr__(self):
        regels = []
        for rij in self._data:
            regels.append("[" + "  ".join(f"{round(w, 2) + 0.0:6.2f}" for w in rij) + " ]")
        return "\n".join(regels)


# ---------------------------------------------------------------------------
# Tekenwerk
# ---------------------------------------------------------------------------
def _naar_scherm(x, y):
    """Reken wiskundige coordinaten om naar pixels (oorsprong in het midden)."""
    px = WIDTH / 2 + x * SCALE
    py = HEIGHT / 2 - y * SCALE     # y omkeren: wiskundig 'omhoog' = scherm 'omhoog'
    return px, py


def _maak_glow(grootte=70):
    """Maak een wit, radiaal vervagend gloed-sprite (voor het 'licht' van een drone)."""
    midden = (grootte - 1) / 2
    y, x = np.ogrid[0:grootte, 0:grootte]
    afstand = np.sqrt((x - midden) ** 2 + (y - midden) ** 2) / midden
    intensiteit = np.clip(1 - afstand, 0, 1) ** 1.7
    waarde = (intensiteit * 255).astype(np.uint8)
    arr = np.dstack([waarde, waarde, waarde])
    return pygame.surfarray.make_surface(arr)


def _lerp_state(a, b, t):
    """Tussenstand tussen scene a en scene b op fractie t (0..1)."""
    out = {}
    for i, (bx, by, bc) in b.items():
        ax, ay, ac = a.get(i, (bx, by, bc))
        x = ax + (bx - ax) * t
        y = ay + (by - ay) * t
        c = (
            ac[0] + (bc[0] - ac[0]) * t,
            ac[1] + (bc[1] - ac[1]) * t,
            ac[2] + (bc[2] - ac[2]) * t,
        )
        out[i] = (x, y, c)
    return out


def _bouw_phases():
    """Zet de keyframes om in een tijdlijn van fasen (bewegen / stilstaan)."""
    phases = []
    if not _keyframes:
        return phases
    eerste = _keyframes[0]["state"]
    # De eerste scene verschijnt meteen en blijft 'hold' staan.
    phases.append(("hold", max(_keyframes[0]["hold"], 0.01), eerste, eerste))
    for k in range(1, len(_keyframes)):
        vorige = _keyframes[k - 1]["state"]
        huidige = _keyframes[k]["state"]
        if _keyframes[k]["duur"] > 0:
            phases.append(("move", _keyframes[k]["duur"], vorige, huidige))
        if _keyframes[k]["hold"] > 0:
            phases.append(("hold", _keyframes[k]["hold"], huidige, huidige))
    return phases


def _state_op(phases, elapsed):
    """Bepaal de stand van alle drones op tijdstip `elapsed`."""
    for kind, duur, a, b in phases:
        if elapsed <= duur:
            t = 1.0 if duur == 0 else elapsed / duur
            return _lerp_state(a, b, t)
        elapsed -= duur
    # Voorbij het einde: toon de laatste stand.
    _, _, _, laatste = phases[-1]
    return laatste


def _teken_lichtpunt(scherm, glow, grootte, px, py, kleur, helderheid=1.0):
    """Teken het gloeiende licht van een drone (additief)."""
    r, g, b = kleur
    if r == 0 and g == 0 and b == 0:
        return                      # drone staat 'uit'
    tint = glow.copy()
    tint.fill(
        (int(r * helderheid), int(g * helderheid), int(b * helderheid)),
        special_flags=pygame.BLEND_RGB_MULT,
    )
    scherm.blit(
        tint,
        (px - grootte / 2, py - grootte / 2),
        special_flags=pygame.BLEND_RGB_ADD,
    )


def _toon_tekst():
    """Tekstweergave van de show, voor omgevingen zonder scherm (bv. CodeRunner)."""
    scenes = _keyframes if _keyframes else [{"state": dict(_buffer)}]
    eind = scenes[-1]["state"]
    print(f"Aantal scenes: {len(scenes)}")
    print(f"Aantal drones: {len(eind)}")
    print("Eindstand:")
    for nummer in sorted(eind):
        x, y, rgb = eind[nummer]
        print(f"drone {nummer}: ({_fmt(x)}, {_fmt(y)}) {_kleurnaam(rgb)}")


def start_show(herhaal=True, sporen=False):
    """Toon de drone-show.

    Grafisch (met pygame) als dat kan; anders als tekst (bv. in CodeRunner).

    herhaal=True : de show speelt in een lus.
    sporen=True  : elke drone laat een vervagend lichtspoor na (handig om te
                   zien welke paden de drones vliegen en of ze kruisen).

    Sluit met de vensterknop of met de Escape-toets.
    """
    if not _keyframes:
        nieuwe_scene()   # niets vastgelegd? leg dan toch de huidige stand vast

    # Geen pygame/numpy beschikbaar (bv. Moodle/CodeRunner) -> tekstmodus.
    if not _GRAFISCH:
        _toon_tekst()
        return

    phases = _bouw_phases()
    totaal = sum(duur for _, duur, _, _ in phases)

    pygame.init()
    test = bool(os.environ.get("DRONE_TEST"))
    start_at = float(os.environ.get("DRONE_START", "0"))
    cap_every = int(os.environ.get("DRONE_CAP_EVERY", "18"))
    cap_max = int(os.environ.get("DRONE_CAP_MAX", "150"))

    # Geen scherm beschikbaar (bv. headless server met wel pygame) -> tekstmodus.
    try:
        scherm = pygame.display.set_mode((WIDTH, HEIGHT))
    except pygame.error:
        pygame.quit()
        _toon_tekst()
        return
    pygame.display.set_caption("Drone-show")
    klok = pygame.time.Clock()
    glow = _maak_glow()
    grootte = glow.get_width()

    SPOOR_LENGTE = 16
    geschiedenis = []

    elapsed = start_at
    frames = 0
    bezig = True
    while bezig:
        dt = (1 / 60.0) if test else klok.tick(FPS) / 1000.0
        elapsed += dt
        if herhaal and not test and totaal > 0 and elapsed > totaal:
            elapsed = elapsed % totaal

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                bezig = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                bezig = False

        scherm.fill((6, 8, 18))   # donkere nachtlucht

        state = _state_op(phases, elapsed)
        huidig = []
        for x, y, kleur in state.values():
            px, py = _naar_scherm(x, y)
            huidig.append((px, py, kleur))

        # lichtsporen: oudere standen vager tekenen
        if sporen:
            geschiedenis.append(huidig)
            if len(geschiedenis) > SPOOR_LENGTE:
                geschiedenis.pop(0)
            for laag, frame in enumerate(geschiedenis[:-1]):
                helderheid = (laag + 1) / len(geschiedenis) * 0.45
                for px, py, kleur in frame:
                    _teken_lichtpunt(scherm, glow, grootte, px, py, kleur, helderheid)

        # de drones zelf
        for px, py, (r, g, b) in huidig:
            _teken_lichtpunt(scherm, glow, grootte, px, py, (r, g, b))
            if (r, g, b) != (0, 0, 0):
                pygame.draw.circle(scherm, (int(r), int(g), int(b)), (px, py), 4)

        pygame.display.flip()

        if test and frames % cap_every == 0:
            pygame.image.save(scherm, f"/tmp/drone_frame_{frames:04d}.png")
        frames += 1
        if test and frames > cap_max:
            bezig = False

    pygame.quit()
