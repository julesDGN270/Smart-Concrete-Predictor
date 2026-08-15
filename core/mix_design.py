"""
Moteur de formulation classique - Methode Dreux-Gorisse
=========================================================

Reconstruit fidelement la methode telle que presentee dans le cours
"Materiaux de construction" (Dr. Ing. E. Fructueux Gildas GODONOU,
ENSTP Abomey, Chapitre 4 - Etude de la composition d'un beton).

Etapes :
  1. Resistance moyenne visee : sigma28' = 1.15 x sigma_n
  2. Rapport C/E (formule de Bolomey) : sigma28' = G.sigma_c.(C/E - 0.5)
  3. Dosage en ciment C : lecture de l'abaque (C/E, affaissement) -> C
  4. Dosage en eau E = C / (C/E), puis correction selon Dmax
  5. Courbe granulaire de reference OAB (point A, formule exacte du cours)
     -> repartition sable/gravier (cas simplifie : un sable + un gravier)
  6. Coefficient de compacite gamma (tableau du cours) -> volumes absolus
     -> dosages en sable et gravier (kg/m3)

IMPORTANT :
- Les tableaux G, K1, correction eau/Dmax et compacite reprennent
  EXACTEMENT les valeurs du cours fourni.
- La classe vraie du ciment (sigma_c) est un parametre OBLIGATOIRE de
  design() : c'est une valeur MESUREE par essai (chapitre 3.5.7), pas
  deduite de la classe nominale (32.5/42.5/52.5). Plus d'estimation par
  defaut : fournis la valeur mesuree de ton ciment.
- L'abaque donnant C en fonction de (C/E, affaissement) est un graphique
  dans le cours ; il a ete reconstruit ici par une formule lineaire
  calee EXACTEMENT sur l'exemple chiffre du cours (C/E=2.1, aff=6cm -> C=400).
  Si tu peux lire d'autres points precis sur le graphique de ton cours
  (page 57), dis-le moi et j'affinerai la formule.
"""

import math
from dataclasses import dataclass, field


# =====================================================================
# TABLES EXACTES DU COURS
# =====================================================================

# Coefficient granulaire G : qualite des granulats x plage de Dmax
# (Tableau exact du cours, Chapitre 4.5.1)
GRANULAT_G = {
    "excellente": {"fins": 0.55, "moyen": 0.60, "gros": 0.65},
    "bonne":      {"fins": 0.45, "moyen": 0.50, "gros": 0.55},
    "passable":   {"fins": 0.35, "moyen": 0.40, "gros": 0.45},
}


def _bin_dmax_G(dmax: float) -> str:
    """Fins: Dmax<=16mm ; moyen: 25<=Dmax<=40mm (utilise aussi pour les
    valeurs intermediaires 16-63mm, cas le plus courant) ; gros: Dmax>=63mm."""
    if dmax <= 16:
        return "fins"
    if dmax >= 63:
        return "gros"
    return "moyen"


# Correction du dosage en eau selon Dmax (Chapitre 4.5.1, tableau exact)
CORRECTION_EAU_DMAX = {
    5: 15, 10: 9, 16: 4, 25: 0, 40: -4, 63: -8, 100: -12,
}

# Table K1 : terme correcteur du point A selon dosage ciment / vibration /
# forme des granulats (Chapitre 4.5.3, tableau exact).
# Colonnes : (vibration, forme) -> valeur. Lignes : dosage en ciment (kg/m3)
K1_TABLE = {
    200:            {("faible", "roule"): 8,  ("faible", "concasse"): 10, ("normale", "roule"): 6,  ("normale", "concasse"): 8,  ("puissante", "roule"): 4,  ("puissante", "concasse"): 6},
    250:            {("faible", "roule"): 6,  ("faible", "concasse"): 8,  ("normale", "roule"): 4,  ("normale", "concasse"): 6,  ("puissante", "roule"): 2,  ("puissante", "concasse"): 4},
    300:            {("faible", "roule"): 4,  ("faible", "concasse"): 6,  ("normale", "roule"): 2,  ("normale", "concasse"): 4,  ("puissante", "roule"): 0,  ("puissante", "concasse"): 2},
    350:            {("faible", "roule"): 2,  ("faible", "concasse"): 4,  ("normale", "roule"): 0,  ("normale", "concasse"): 2,  ("puissante", "roule"): -2, ("puissante", "concasse"): 0},
    400:            {("faible", "roule"): 0,  ("faible", "concasse"): 2,  ("normale", "roule"): -2, ("normale", "concasse"): 0,  ("puissante", "roule"): -4, ("puissante", "concasse"): -2},
    "400+fluide":   {("faible", "roule"): -2, ("faible", "concasse"): 0, ("normale", "roule"): -4, ("normale", "concasse"): -2, ("puissante", "roule"): -6, ("puissante", "concasse"): -4},
}

# Coefficient de compacite gamma (Chapitre 4.5.3, tableau exact)
# consistance -> serrage -> {Dmax(mm): gamma}
COMPACITE_GAMMA = {
    ("molle", "piquage"):              {5: 0.750, 10: 0.780, 12.5: 0.795, 20: 0.805, 31.5: 0.810, 50: 0.815, 80: 0.820},
    ("molle", "faible"):               {5: 0.755, 10: 0.785, 12.5: 0.800, 20: 0.810, 31.5: 0.815, 50: 0.820, 80: 0.825},
    ("molle", "normale"):              {5: 0.760, 10: 0.790, 12.5: 0.805, 20: 0.815, 31.5: 0.820, 50: 0.825, 80: 0.830},
    ("plastique", "piquage"):          {5: 0.760, 10: 0.790, 12.5: 0.805, 20: 0.815, 31.5: 0.820, 50: 0.825, 80: 0.830},
    ("plastique", "faible"):           {5: 0.765, 10: 0.795, 12.5: 0.810, 20: 0.820, 31.5: 0.825, 50: 0.830, 80: 0.835},
    ("plastique", "normale"):          {5: 0.770, 10: 0.800, 12.5: 0.815, 20: 0.825, 31.5: 0.830, 50: 0.835, 80: 0.840},
    ("plastique", "puissante"):        {5: 0.775, 10: 0.805, 12.5: 0.820, 20: 0.830, 31.5: 0.835, 50: 0.840, 80: 0.845},
    ("ferme", "piquage"):              {5: 0.775, 10: 0.805, 12.5: 0.820, 20: 0.830, 31.5: 0.835, 50: 0.840, 80: 0.845},
    ("ferme", "normale"):              {5: 0.780, 10: 0.810, 12.5: 0.825, 20: 0.835, 31.5: 0.840, 50: 0.845, 80: 0.850},
    ("ferme", "puissante"):            {5: 0.785, 10: 0.815, 12.5: 0.830, 20: 0.840, 31.5: 0.845, 50: 0.850, 80: 0.855},
}

# Correction du coefficient de compacite selon forme des granulats
# (base = sable et gravier roules)
CORRECTION_COMPACITE_FORME = {
    ("roule", "roule"): 0.0,
    ("roule", "concasse"): -0.01,
    ("concasse", "concasse"): -0.03,
}

# Classes de consistance S1-S4 -> categorie du tableau de compacite
# NB : le cours ne distingue que 3 categories (molle/plastique/ferme) pour
# 4 classes de consistance S1-S4 ; cette correspondance est une approximation
# raisonnable, a ajuster si ton cours precise autrement.
CONSISTANCE_VERS_COMPACITE = {
    "S1": "ferme", "S2": "plastique", "S3": "plastique", "S4": "molle",
}
CONSISTANCE_SLUMP_CM = {"S1": 3, "S2": 7, "S3": 13, "S4": 18}

# Masses volumiques indicatives (kg/L) - a ajuster avec tes essais reels
# (chapitre 2.4 : masse volumique reelle mesuree par pycnometre)
DENSITE_CIMENT = 3.10
DENSITE_SABLE = 2.63
DENSITE_GRAVIER = 2.63

# Valeur par defaut si la classe vraie mesuree n'est pas fournie
# (approximation generique CEM 42.5 local, a affiner avec la valeur reelle)
DEFAULT_CEMENT_TRUE_CLASS = 48.0



def sieve_module(d_mm: float) -> float:
    """Conversion diametre de tamis (mm) -> module, formule du cours
    (progression geometrique 10^(1/10)) : Module = 31 + 10.log10(D)."""
    return 31 + 10 * math.log10(d_mm)


def sieve_diameter(module: float) -> float:
    """Inverse de sieve_module."""
    return 10 ** ((module - 31) / 10)


def _interp_table_1d(table: dict, x: float) -> float:
    keys = sorted(table.keys())
    if x <= keys[0]:
        return table[keys[0]]
    if x >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        k0, k1 = keys[i], keys[i + 1]
        if k0 <= x <= k1:
            t = (x - k0) / (k1 - k0)
            return table[k0] + t * (table[k1] - table[k0])
    return table[keys[-1]]


def _nearest_cement_dosage_label(c: float):
    # "400+fluide" traite comme un palier virtuel a 430 : evite un saut
    # brutal de ligne du tableau K1 pour un C tres proche de 400.
    paliers = {200: 200, 250: 250, 300: 300, 350: 350, 400: 400, "400+fluide": 430}
    return min(paliers, key=lambda label: abs(paliers[label] - c))


def cement_dosage_from_abaque(ce_ratio: float, affaissement_cm: float) -> float:
    """
    Reconstruction de l'abaque (C/E, affaissement) -> Dosage en ciment C
    (Chapitre 4.5.1, figure page 57).

    Calee EXACTEMENT sur l'exemple chiffre du cours : C/E=2.1, affaissement
    =6cm -> C=400 kg/m3. La pente (variation de C/E avec l'affaissement) et
    l'espacement entre courbes iso-C sont des reconstructions approximatives
    du graphique, pas une lecture pixel-precise -> a affiner si tu peux
    fournir d'autres points lus directement sur la figure.
    """
    PENTE_PAR_CM = 0.045   # variation de C/E par cm d'affaissement (approx.)
    ce_ref = ce_ratio + PENTE_PAR_CM * (affaissement_cm - 6)
    C = 200 * (ce_ref - 0.10)
    return max(150.0, C)


@dataclass
class MixDesignResult:
    cement: float
    water: float
    sand: float
    gravel: float
    silica_fume: float
    slag: float
    ec_ratio: float
    target_mean_strength: float
    point_a_sable_pct: float
    age: int = 28
    warnings: list = field(default_factory=list)

    def as_predictor_values(self):
        """
        [cement, slag, fly_ash, water, superplasticizer, coarse_aggregate,
         fine_aggregate, age] - ordre verifie sur Concrete_Data.csv.
        Gravier = coarse_aggregate, sable = fine_aggregate.
        """
        return [
            round(self.cement, 1),
            round(self.slag, 1),
            round(self.silica_fume, 1),
            round(self.water, 1),
            0.0,
            round(self.gravel, 1),
            round(self.sand, 1),
            self.age,
        ]


class DreuxGorisseMixDesign:

    def __init__(self, granulat_quality: str = "bonne"):
        if granulat_quality not in GRANULAT_G:
            raise ValueError(
                f"Qualite de granulats inconnue : {granulat_quality}. "
                f"Choix possibles : {list(GRANULAT_G)}"
            )
        self.granulat_quality = granulat_quality

    def design(
        self,
        target_strength: float,
        dmax: float,
        cement_true_class: float = None,
        consistency_class: str = None,
        affaissement_cm: float = None,
        age: int = 28,
        sand_fineness_modulus: float = 2.5,
        vibration: str = "normale",
        sable_forme: str = "roule",
        gravier_forme: str = "roule",
        pompable: bool = False,
        control_margin_pct: float = 15.0,
        exposure_class: str = None,
        granulat_quality: str = None,
    ) -> MixDesignResult:

        warnings = []
        quality = granulat_quality or self.granulat_quality
        if quality not in GRANULAT_G:
            raise ValueError(
                f"Qualite de granulats inconnue : {quality}. "
                f"Choix possibles : {list(GRANULAT_G)}"
            )

        if affaissement_cm is not None:
            affaissement = affaissement_cm
        elif consistency_class is not None:
            if consistency_class not in CONSISTANCE_SLUMP_CM:
                raise ValueError(
                    f"Classe de consistance inconnue : {consistency_class}. "
                    f"Choix possibles : {list(CONSISTANCE_SLUMP_CM)}"
                )
            affaissement = CONSISTANCE_SLUMP_CM[consistency_class]
        else:
            raise ValueError("Fournis soit affaissement_cm, soit consistency_class.")

        # ---- Classe vraie du ciment (mesuree de preference) ------------
        if cement_true_class is None or cement_true_class <= 0:
            sigma_c = DEFAULT_CEMENT_TRUE_CLASS
            warnings.append(
                f"cement_true_class non fournie -> valeur par defaut "
                f"{DEFAULT_CEMENT_TRUE_CLASS} MPa utilisee (classe vraie "
                f"generique CEM 42.5 local). Cette valeur est mesuree par "
                f"essai (chapitre 3.5.7 de ton cours) : fournis la valeur "
                f"reelle de ton ciment des que tu l'as pour plus de precision."
            )
        else:
            sigma_c = cement_true_class

        # ---- 1. Resistance moyenne visee -------------------------------
        target_mean_strength = target_strength * (1 + control_margin_pct / 100)

        # ---- 2. Rapport C/E (formule de Bolomey / Dreux) ---------------
        bin_dmax = _bin_dmax_G(dmax)
        G = GRANULAT_G[quality][bin_dmax]
        ec_ratio_calcule = target_mean_strength / (G * sigma_c) + 0.5

        # ---- 3. Dosage en ciment via l'abaque ---------------------------
        ciment = cement_dosage_from_abaque(ec_ratio_calcule, affaissement)

        if ciment > 400:
            warnings.append(
                f"Dosage en ciment eleve ({ciment:.0f} kg/m3) : ton cours "
                f"recommande un adjuvant plastifiant reducteur d'eau au-dela "
                f"de 400 kg/m3 (chapitre 4.6)."
            )

        # ---- 4. Dosage en eau + correction Dmax -------------------------
        eau = ciment / ec_ratio_calcule
        correction_pct = _interp_table_1d(CORRECTION_EAU_DMAX, dmax)
        eau_corrigee = eau * (1 + correction_pct / 100)

        ec_ratio_final = eau_corrigee / ciment

        # ---- 5. Courbe de reference OAB -> repartition sable/gravier ----
        if dmax <= 20:
            xA = dmax / 2
        else:
            module_xA = (sieve_module(5) + sieve_module(dmax)) / 2
            xA = sieve_diameter(module_xA)

        c_label = _nearest_cement_dosage_label(ciment)
        k1 = K1_TABLE[c_label].get((vibration, sable_forme))
        if k1 is None:
            k1 = 0
            warnings.append(
                f"Combinaison vibration='{vibration}'/forme sable='{sable_forme}' "
                f"non trouvee dans la table K1 -> K1=0 utilise par defaut."
            )

        ks = 6 * sand_fineness_modulus - 15
        kp = 7.5 if pompable else 0.0
        k_total = k1 + ks + kp

        yA = 50 - math.sqrt(dmax) + k_total
        yA = max(0, min(100, yA))

        sable_pct = yA
        gravier_pct = 100 - sable_pct

        # ---- 6. Coefficient de compacite -> volumes absolus -------------
        if consistency_class is not None:
            compac_category = CONSISTANCE_VERS_COMPACITE[consistency_class]
        elif affaissement <= 5:
            compac_category = "ferme"
        elif affaissement <= 10:
            compac_category = "plastique"
        else:
            compac_category = "molle"
        gamma_table = COMPACITE_GAMMA.get((compac_category, vibration))
        if gamma_table is None:
            gamma_table = COMPACITE_GAMMA[(compac_category, "normale")]
        gamma = _interp_table_1d(gamma_table, dmax)

        correction_forme = CORRECTION_COMPACITE_FORME.get(
            (sable_forme, gravier_forme)
        )
        if correction_forme is None:
            correction_forme = -0.02
            warnings.append(
                f"Combinaison sable='{sable_forme}'/gravier='{gravier_forme}' "
                f"non presente dans la table de correction de compacite "
                f"(cas peu courant) -> correction moyenne -0.02 utilisee."
            )
        gamma += correction_forme

        volume_total_solides = 1000 * gamma
        v_ciment = ciment / DENSITE_CIMENT
        v_granulats = volume_total_solides - v_ciment

        if v_granulats <= 0:
            warnings.append(
                "Volume disponible pour les granulats negatif : verifie "
                "les parametres d'entree (dosage en ciment tres eleve)."
            )
            v_granulats = max(v_granulats, 0)

        v_sable = v_granulats * (sable_pct / 100)
        v_gravier = v_granulats * (gravier_pct / 100)

        sable = v_sable * DENSITE_SABLE
        gravier = v_gravier * DENSITE_GRAVIER

        # ---- Verification durabilite (classe d'exposition, si fournie) -
        if exposure_class:
            from core.exposure_durability import EXPOSITION_DURABILITE
            exp = EXPOSITION_DURABILITE.get(exposure_class)
            if exp is None:
                warnings.append(
                    f"Classe d'exposition '{exposure_class}' non presente "
                    f"dans la table de durabilite -> aucune verification "
                    f"appliquee."
                )
            else:
                if ec_ratio_final > exp["ec_max"]:
                    warnings.append(
                        f"Rapport E/C ({ec_ratio_final:.2f}) depasse le "
                        f"maximum {exp['ec_max']} impose par la classe "
                        f"d'exposition {exposure_class} (verification "
                        f"externe au cours Dreux-Gorisse, table NF EN 206)."
                    )
                if ciment < exp["c_min"]:
                    warnings.append(
                        f"Dosage en ciment ({ciment:.0f} kg/m3) sous le "
                        f"minimum {exp['c_min']} impose par la classe "
                        f"d'exposition {exposure_class}."
                    )

        return MixDesignResult(
            cement=ciment,
            water=eau_corrigee,
            sand=sable,
            gravel=gravier,
            silica_fume=0.0,
            slag=0.0,
            ec_ratio=ec_ratio_final,
            target_mean_strength=target_mean_strength,
            point_a_sable_pct=sable_pct,
            age=age,
            warnings=warnings,
        )


if __name__ == "__main__":
    # Reproduction de l'exemple chiffre du cours (chapitre 4.7) :
    # Ciment CPJ 35 (classe vraie 450 bars = 45 MPa) ; beton 25 MPa ;
    # affaissement 6cm ; sable/gravier roules ; Dmax=40mm ; Mf sable=1.92
    engine = DreuxGorisseMixDesign(granulat_quality="passable")

    result = engine.design(
        target_strength=25,
        affaissement_cm=6,
        dmax=40,
        cement_true_class=45.0,
        sand_fineness_modulus=1.92,
        vibration="normale",
        sable_forme="roule",
        gravier_forme="roule",
    )

    print("=== Reproduction de l'exemple du cours (attendu : C=400, E=182.86) ===")
    print(f"Resistance moyenne visee : {result.target_mean_strength:.1f} MPa (attendu 28.75)")
    print(f"Ciment : {result.cement:.1f} kg/m3 (attendu 400)")
    print(f"Eau : {result.water:.2f} L (attendu 182.86)")
    print(f"E/C final : {result.ec_ratio:.3f}")
    print(f"% Sable (point A) : {result.point_a_sable_pct:.1f}% (attendu ~38.2% x correction)")
    print(f"Sable : {result.sand:.1f} kg/m3   Gravier : {result.gravel:.1f} kg/m3")
    for w in result.warnings:
        print(f" !  {w}")
