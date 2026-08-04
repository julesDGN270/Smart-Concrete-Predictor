"""
Exigences de durabilite simplifiees par classe d'exposition (NF EN 206/CN).

NB : ce tableau ne vient PAS du cours Dreux-Gorisse fourni (qui ne traite
pas des classes d'exposition) -- c'est une verification externe optionnelle,
a base de valeurs indicatives NF EN 206. A utiliser comme garde-fou
supplementaire, pas comme partie de la methode Dreux-Gorisse elle-meme.
"""

EXPOSITION_DURABILITE = {
    "X0":  {"c_min": 200, "ec_max": 0.70},
    "XC1": {"c_min": 260, "ec_max": 0.65},
    "XC2": {"c_min": 280, "ec_max": 0.60},
    "XC3": {"c_min": 280, "ec_max": 0.55},
    "XC4": {"c_min": 300, "ec_max": 0.55},
    "XF1": {"c_min": 300, "ec_max": 0.55},
    "XF2": {"c_min": 320, "ec_max": 0.50},
    "XF3": {"c_min": 320, "ec_max": 0.50},
    "XA1": {"c_min": 300, "ec_max": 0.55},
}
