"""
Extraction depuis un texte libre -> formulation -> rapport
=============================================================

Analyse une description en francais (cahier des charges informel) pour
en extraire les parametres d'ingenieur, lance l'assistant de formulation
(materiaux locaux si mentionnes, sinon generique), et produit un rapport
texte pret a lire.

Approche volontairement basee sur des regles (regex/mots-cles), pas sur
un appel a un modele de langage externe : deterministe, sans dependance
reseau ni cle API, adapte a un outil de bureau autonome. Les tournures
non reconnues sont signalees plutot que devinees en silence.
"""

import re

from core.local_formulation import LocalMaterialsFormulationAssistant
from core.formulation_assistant import FormulationAssistant
from core.local_materials import CIMENTS_LOCAUX, SABLES_LOCAUX, GRANULATS_LOCAUX, ADDITIONS_LOCALES


def _find_float(pattern, text, default=None):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return default
    return float(m.group(1).replace(",", "."))


def _find_keyword(mots_cles: dict, text: str):
    """mots_cles : {cle_interne: [motifs a chercher]} -> renvoie la premiere cle trouvee."""
    text_l = text.lower()
    for cle, motifs in mots_cles.items():
        for motif in motifs:
            if motif in text_l:
                return cle
    return None


CIMENT_MOTIFS = {
    "cem1_425_local": ["cem i 42.5", "cem i 42,5", "cpj 42.5", "ciment 42.5"],
    "cem2_325_local": ["cem ii 32.5", "cem ii 32,5", "ciment 32.5"],
    "cem2_425_local": ["cem ii 42.5", "cem ii 42,5"],
}
SABLE_MOTIFS = {
    "sable_riviere": ["sable de riviere", "sable de rivière"],
    "sable_carriere": ["sable de carriere", "sable de carrière", "sable concasse"],
    "sable_lagunaire": ["sable lagunaire", "sable marin"],
}
GRANULAT_MOTIFS = {
    "granite_concasse": ["granite concasse", "granite concassé", "granite"],
    "laterite_gravier": ["laterite", "latérite"],
    "quartzite_concasse": ["quartzite"],
}
ADDITION_MOTIFS = {
    "cendre_balle_riz": ["cendre de balle de riz", "balle de riz", "rha"],
    "pouzzolane_naturelle": ["pouzzolane"],
    "laitier": ["laitier"],
}
CONSISTANCE_MOTIFS = {
    "S1": ["beton ferme", "béton ferme"],
    "S2": ["beton plastique", "béton plastique"],
    "S3": ["tres plastique", "très plastique"],
    "S4": ["beton fluide", "béton fluide", "fluide"],
}


def analyser_texte(description: str) -> dict:
    """Extrait les parametres reconnus depuis une description en francais.
    Renvoie un dict avec les valeurs trouvees et une liste 'non_reconnu'
    listant ce qui n'a pas pu etre extrait (a completer manuellement)."""

    non_reconnu = []

    target_strength = _find_float(r"(\d+(?:[.,]\d+)?)\s*mpa", description)
    if target_strength is None:
        non_reconnu.append("resistance cible (ex: '30 MPa')")

    dmax = _find_float(r"d\s*max\s*[:=]?\s*(\d+(?:[.,]\d+)?)", description)
    if dmax is None:
        dmax = _find_float(r"(\d+(?:[.,]\d+)?)\s*mm", description)
    if dmax is None:
        non_reconnu.append("Dmax (ex: 'Dmax 20mm' ou '20mm')")

    affaissement_cm = _find_float(r"affaissement\s*(?:de|:)?\s*(\d+(?:[.,]\d+)?)\s*cm", description)

    m_exposure = re.search(r"\b(X[CDFSA]\d)\b", description, re.IGNORECASE)
    exposure_class = m_exposure.group(1).upper() if m_exposure else None

    cement_key = _find_keyword(CIMENT_MOTIFS, description)
    sable_key = _find_keyword(SABLE_MOTIFS, description)
    granulat_key = _find_keyword(GRANULAT_MOTIFS, description)
    addition_key = _find_keyword(ADDITION_MOTIFS, description)
    consistency_class = _find_keyword(CONSISTANCE_MOTIFS, description)

    if not consistency_class and affaissement_cm is None:
        non_reconnu.append("consistance/affaissement (ex: 'affaissement de 7cm')")

    return dict(
        target_strength=target_strength,
        dmax=dmax,
        affaissement_cm=affaissement_cm,
        consistency_class=consistency_class,
        exposure_class=exposure_class,
        cement_key=cement_key,
        sable_key=sable_key,
        granulat_key=granulat_key,
        addition_key=addition_key,
        non_reconnu=non_reconnu,
    )


def generer_rapport(description: str) -> str:
    """Pipeline complet : texte -> extraction -> formulation -> rapport."""

    params = analyser_texte(description)
    lignes = ["=== RAPPORT DE FORMULATION ===", "", "Description fournie :", description.strip(), ""]

    if params["target_strength"] is None or params["dmax"] is None:
        lignes.append(
            "Impossible de generer une formulation : parametres essentiels manquants."
        )
        lignes.append("A completer : " + "; ".join(params["non_reconnu"]))
        return "\n".join(lignes)

    utilise_materiaux_locaux = bool(params["cement_key"] or params["sable_key"] or params["granulat_key"])

    if utilise_materiaux_locaux:
        assistant = LocalMaterialsFormulationAssistant()
        result = assistant.propose(
            target_strength=params["target_strength"],
            dmax=params["dmax"],
            cement_key=params["cement_key"] or "cem2_425_local",
            sable_key=params["sable_key"] or "sable_riviere",
            granulat_key=params["granulat_key"] or "granite_concasse",
            addition_key=params["addition_key"],
            consistency_class=params["consistency_class"],
            affaissement_cm=params["affaissement_cm"],
            exposure_class=params["exposure_class"],
        )
        lignes.append("Parametres extraits :")
        lignes.append(f"- Resistance cible : {params['target_strength']} MPa")
        lignes.append(f"- Dmax : {params['dmax']} mm")
        if params["exposure_class"]:
            lignes.append(f"- Classe d'exposition : {params['exposure_class']}")
        lignes.append("")
        lignes.append(result.summary())
    else:
        assistant = FormulationAssistant()
        verif = assistant.propose_and_verify(
            target_strength=params["target_strength"],
            dmax=params["dmax"],
            consistency_class=params["consistency_class"],
            affaissement_cm=params["affaissement_cm"],
            exposure_class=params["exposure_class"],
        )
        lignes.append("Parametres extraits :")
        lignes.append(f"- Resistance cible : {params['target_strength']} MPa")
        lignes.append(f"- Dmax : {params['dmax']} mm")
        lignes.append("")
        lignes.append(verif.summary())
        m = verif.mix
        lignes.append(
            f"Mix : C={m.cement:.0f}  E={m.water:.0f}  S={m.sand:.0f}  "
            f"G={m.gravel:.0f}  E/C={m.ec_ratio:.3f}"
        )
        for w in m.warnings:
            lignes.append(f"!  {w}")

    if params["non_reconnu"]:
        lignes.append("")
        lignes.append(
            "Non reconnu dans le texte (valeurs par defaut utilisees) : "
            + "; ".join(params["non_reconnu"])
        )

    return "\n".join(lignes)


if __name__ == "__main__":
    exemples = [
        "Je veux un beton de 30 MPa, Dmax 20mm, classe d'exposition XC3, "
        "affaissement de 7cm, avec du sable de riviere, du granite concasse "
        "et de la cendre de balle de riz.",

        "Beton de 25 MPa, Dmax 12.5mm, tres plastique, ciment CEM I 42.5, "
        "sable de carriere.",

        "Je veux un beton solide pour ma dalle.",
    ]

    for ex in exemples:
        print(generer_rapport(ex))
        print("\n" + "=" * 70 + "\n")
