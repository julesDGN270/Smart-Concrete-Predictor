"""
Donnees de cout et d'impact CO2 par materiau (indicatives)
=============================================================

ATTENTION - ces valeurs sont des ORDRES DE GRANDEUR indicatifs pour
demarrer l'optimisation, pas des donnees locales verifiees :

- COUT_RELATIF : unites monetaires RELATIVES arbitraires (pas des FCFA
  reels). A remplacer par tes prix locaux (ciment, sable, gravier,
  superplastifiant, laitier, fumee de silice au Benin) des que tu les as
  -> il suffit de changer les chiffres ci-dessous, le reste du code
  n'a pas besoin de changer.
- CO2_KG_PAR_KG : facteurs d'emission indicatifs issus de la litterature
  ACV generale (ordre de grandeur courant pour un CEM I ~0.85-0.95
  kgCO2eq/kg ciment). A affiner avec des facteurs d'emission locaux
  ou specifiques a ton fournisseur si tu les as.
"""

COUT_RELATIF = {
    "cement": 1.00,
    "water": 0.01,
    "sand": 0.05,
    "gravel": 0.06,
    "superplasticizer": 3.50,
    "slag": 0.35,
    "silica_fume": 1.80,
}

CO2_KG_PAR_KG = {
    "cement": 0.90,
    "water": 0.0003,
    "sand": 0.005,
    "gravel": 0.007,
    "superplasticizer": 1.50,
    "slag": 0.05,     # sous-produit industriel -> impact bien plus faible que le ciment
    "silica_fume": 0.03,
}


def evaluate_cost(mix_dict: dict) -> float:
    """mix_dict : {cement, water, sand, gravel, superplasticizer, slag, silica_fume} en kg/m3"""
    return sum(mix_dict.get(k, 0.0) * COUT_RELATIF.get(k, 0.0) for k in COUT_RELATIF)


def evaluate_co2(mix_dict: dict) -> float:
    return sum(mix_dict.get(k, 0.0) * CO2_KG_PAR_KG.get(k, 0.0) for k in CO2_KG_PAR_KG)
