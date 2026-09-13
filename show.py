# =====================================================================
#  DRONE-SHOW  --  het eindproduct
#
#  Scenes:  startgrid op de grond
#            -> cirkel
#            -> hart
#            -> ster die ronddraait (met een rotatiematrix)
#            -> gezicht met knipperende ogen
#            -> landing terug op de grond
#
#  Dit is het soort code dat de leerlingen zelf schrijven:
#  enkel for-lussen en wiskunde, geen zelfgemaakte functies, geen while.
# =====================================================================
from drone_engine import *
import numpy as np

aantal = 48
kolommen = 12

# ---------------------------------------------------------------------
# Scene 1: alle drones netjes in een rooster op de grond
# ---------------------------------------------------------------------
for i in range(aantal):
    kolom = i % kolommen
    rij = i // kolommen
    x = kolom - 5.5          # rooster horizontaal centreren
    y = -4 + rij             # onderaan = "de grond"
    zet_drone(i, x, y, "blauw")
nieuwe_scene()
wacht(1.5)

# ---------------------------------------------------------------------
# Scene 2: een cirkel  (goniometrie: x = r*cos, y = r*sin)
# ---------------------------------------------------------------------
straal = 3
for i in range(aantal):
    hoek = i * 2 * pi / aantal
    x = straal * cos(hoek)
    y = straal * sin(hoek)
    zet_drone(i, x, y, "cyaan")
nieuwe_scene(duur=2.5)
wacht(1.5)

# ---------------------------------------------------------------------
# Scene 3: een hart  (parametervergelijking van een hartkromme)
# ---------------------------------------------------------------------
for i in range(aantal):
    t = i * 2 * pi / aantal
    x = 16 * sin(t) ** 3
    y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
    zet_drone(i, 0.18 * x, 0.18 * y + 0.3, "roze")
nieuwe_scene(duur=2.5)
wacht(1.5)

# ---------------------------------------------------------------------
# Scene 4: een ster, die daarna ronddraait
#   - eerst de basisvorm van de ster opbouwen
#   - dan in stapjes draaien met een ROTATIEMATRIX (wiskunde!)
# ---------------------------------------------------------------------
basis_x = []
basis_y = []
for i in range(aantal):
    hoek = i * 2 * pi / aantal
    r = 2.2 + 0.9 * cos(5 * hoek)     # 5 "pieken" -> stervorm
    basis_x.append(r * cos(hoek))
    basis_y.append(r * sin(hoek))
    zet_drone(i, basis_x[i], basis_y[i], "magenta")
nieuwe_scene(duur=2.5)
wacht(0.6)

# De ster ronddraaien: elke drone vermenigvuldigen met de rotatiematrix
#   [ cos a   -sin a ]
#   [ sin a    cos a ]
for stap in range(1, 31):
    a = stap * (2 * pi / 30)
    R = np.array([[cos(a), -sin(a)],
                  [sin(a),  cos(a)]])
    for i in range(aantal):
        punt = np.array([basis_x[i], basis_y[i]])
        gedraaid = R @ punt           # matrixvermenigvuldiging (numpy)
        zet_drone(i, gedraaid[0], gedraaid[1], "magenta")
    nieuwe_scene(duur=0.12)
wacht(0.5)

# ---------------------------------------------------------------------
# Scene 5: een gezicht
#   - drones 0..31  : rand van het hoofd (een cirkel)
#   - drones 32, 33 : de twee ogen
#   - drones 34..47 : de mond (een glimlach)
# ---------------------------------------------------------------------
for i in range(32):
    hoek = i * 2 * pi / 32
    x = 3 * cos(hoek)
    y = 0.5 + 3 * sin(hoek)
    zet_drone(i, x, y, "geel")

zet_drone(32, -1.1, 1.3, "wit")
zet_drone(33, 1.1, 1.3, "wit")

for i in range(14):
    hoek = pi + i * pi / 13       # onderste helft van een cirkel = glimlach
    x = 1.4 * cos(hoek)
    y = -0.8 + 0.9 * sin(hoek)
    zet_drone(34 + i, x, y, "rood")
nieuwe_scene(duur=2.5)
wacht(1.0)

# De ogen knipperen: even uit en terug aan (2 keer)
for knip in range(2):
    zet_drone(32, -1.1, 1.3, "uit")
    zet_drone(33, 1.1, 1.3, "uit")
    nieuwe_scene(duur=0.12)
    wacht(0.12)

    zet_drone(32, -1.1, 1.3, "wit")
    zet_drone(33, 1.1, 1.3, "wit")
    nieuwe_scene(duur=0.12)
    wacht(0.8)

# ---------------------------------------------------------------------
# Scene 6: landing -- de drones dalen terug naar de grond
# ---------------------------------------------------------------------
for i in range(aantal):
    kolom = i % kolommen
    rij = i // kolommen
    zet_drone(i, kolom - 5.5, -4 + rij, "blauw")
nieuwe_scene(duur=3.0)
wacht(1.5)

# ---------------------------------------------------------------------
start_show()
