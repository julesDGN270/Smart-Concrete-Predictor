"""
Module materiaux locaux (Afrique de l'Ouest / Benin)
=========================================================

Registre de profils de materiaux locaux courants, qui se traduisent
automatiquement en parametres du moteur Dreux-Gorisse (core.mix_design)
et en additions eventuelles (substitution partielle du ciment).

IMPORTANT : les valeurs numeriques ici (classe vraie ciment, module de
finesse sable, taux de substitution des additions, facteurs CO2) sont des
ORDRES DE GRANDEUR indicatifs issus de la litterature generale, PAS des
valeurs mesurees localement. Elles sont volontairement centralisees et
faciles a corriger : des que tu as des essais reels (chapitre 3.5.7 pour
le ciment, essais granulometriques pour le sable/gravier), remplace les
valeurs correspondantes ici.
"""

from dataclasses import dataclass


@dataclass
class CementProfile:
    label: str
    true_class_mpa: float          # classe vraie estimee (a verifier par essai)
    note: str = ""


@dataclass
class SandProfile:
    label: str
    forme: str                     # "roule" ou "concasse"
    fineness_modulus: float        # module de finesse Mf typique
    note: str = ""


@dataclass
class AggregateProfile:
    label: str
    quality: str                   # "excellente" / "bonne" / "passable"
    forme: str                     # "roule" ou "concasse"
    note: str = ""


@dataclass
class AdditionProfile:
    label: str
    taux_substitution: float       # fraction du ciment remplacee (0-1)
    facteur_eau: float             # multiplicateur applique a l'eau (1.0 = neutre)
    co2_kg_par_kg: float           # facteur CO2 indicatif (kg CO2eq / kg addition)
    cout_relatif: float            # cout relatif indicatif (meme echelle que cost_co2_data)
    note: str = ""


# ---------------------------------------------------------------------
# Ciments locaux courants (Benin / Afrique de l'Ouest)
# ---------------------------------------------------------------------
CIMENTS_LOCAUX = {
    "cem1_425_local":  CementProfile("CEM I 42.5 local", 48.0,
        "Ciment Portland courant. Classe vraie a verifier par essai."),
    "cem2_325_local":  CementProfile("CEM II 32.5 local", 38.0,
        "Ciment compose courant, dosage plus economique."),
    "cem2_425_local":  CementProfile("CEM II 42.5 local", 48.0,
        "Ciment compose, tres repandu sur les chantiers courants."),
}

# ---------------------------------------------------------------------
# Sables locaux
# ---------------------------------------------------------------------
SABLES_LOCAUX = {
    "sable_riviere":  SandProfile("Sable de riviere", "roule", 2.2,
        "Generalement plus fin et roule ; verifier proprete (Equivalent de Sable, chap. 2.3)."),
    "sable_carriere": SandProfile("Sable de carriere (concasse)", "concasse", 2.8,
        "Plus anguleux, souvent plus grossier ; ouvrabilite parfois plus faible."),
    "sable_lagunaire": SandProfile("Sable lagunaire/marin", "roule", 2.0,
        "Verifier teneur en sel/coquillages, propreté (E.S.) avant usage structurel."),
}

# ---------------------------------------------------------------------
# Granulats (gros) locaux
# ---------------------------------------------------------------------
GRANULATS_LOCAUX = {
    "granite_concasse": AggregateProfile("Granite concasse", "bonne", "concasse",
        "Tres courant au Benin (carrieres du Sud/Centre)."),
    "laterite_gravier": AggregateProfile("Gravier lateritique", "passable", "roule",
        "Usage courant en voirie/beton de proprete ; qualite variable, tester Los Angeles (chap. 2.7)."),
    "quartzite_concasse": AggregateProfile("Quartzite concasse", "excellente", "concasse",
        "Bonne durete, verifier coefficient Los Angeles reel."),
}

# ---------------------------------------------------------------------
# Additions locales (substitution partielle du ciment)
# ---------------------------------------------------------------------
ADDITIONS_LOCALES = {
    "cendre_balle_riz": AdditionProfile(
        "Cendre de balle de riz (RHA)", taux_substitution=0.10,
        facteur_eau=1.03, co2_kg_par_kg=0.05, cout_relatif=0.15,
        note="Pouzzolanique si bien calcinee (essai a controler). Sujet de recherche actif "
             "au Benin (valorisation de sous-produit agricole) : bon candidat pour ton memoire "
             "si tu veux mesurer un taux de substitution optimal."
    ),
    "pouzzolane_naturelle": AdditionProfile(
        "Pouzzolane naturelle", taux_substitution=0.15,
        facteur_eau=1.02, co2_kg_par_kg=0.08, cout_relatif=0.20,
        note="Disponibilite locale variable selon la region (origine volcanique)."
    ),
    "laitier": AdditionProfile(
        "Laitier de haut fourneau", taux_substitution=0.30,
        facteur_eau=0.98, co2_kg_par_kg=0.05, cout_relatif=0.35,
        note="Necessite un approvisionnement industriel (souvent importe)."
    ),
}


def resume_profil(cement_key=None, sable_key=None, granulat_key=None, addition_key=None) -> str:
    lignes = []
    if cement_key:
        c = CIMENTS_LOCAUX[cement_key]
        lignes.append(f"Ciment : {c.label} (classe vraie estimee {c.true_class_mpa} MPa) - {c.note}")
    if sable_key:
        s = SABLES_LOCAUX[sable_key]
        lignes.append(f"Sable : {s.label} (Mf~{s.fineness_modulus}, {s.forme}) - {s.note}")
    if granulat_key:
        g = GRANULATS_LOCAUX[granulat_key]
        lignes.append(f"Granulat : {g.label} (qualite {g.quality}, {g.forme}) - {g.note}")
    if addition_key:
        a = ADDITIONS_LOCALES[addition_key]
        lignes.append(f"Addition : {a.label} (substitution {a.taux_substitution*100:.0f}%) - {a.note}")
    return "\n".join(lignes)
