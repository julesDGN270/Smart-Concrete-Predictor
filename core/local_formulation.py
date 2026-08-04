"""
Formulation a partir de materiaux locaux (Phase "materiaux locaux")
=====================================================================

Relie core.local_materials (profils ciment/sable/granulat/addition
locaux) a core.formulation_assistant : l'utilisateur choisit des
materiaux par leur nom local plutot que de saisir des parametres
techniques bruts, et le logiciel adapte automatiquement la formulation
(y compris la substitution partielle du ciment par une addition locale).
"""

from dataclasses import dataclass, field

from core.formulation_assistant import FormulationAssistant, FormulationVerification
from core.local_materials import CIMENTS_LOCAUX, SABLES_LOCAUX, GRANULATS_LOCAUX, ADDITIONS_LOCALES
from core.cost_co2_data import evaluate_cost, evaluate_co2, COUT_RELATIF, CO2_KG_PAR_KG


@dataclass
class LocalFormulationResult:
    verification: FormulationVerification
    cement_final: float
    addition_mass: float
    addition_label: str
    water_final: float
    predicted_strength_final: float
    cost: float
    co2: float
    materiaux_utilises: str
    warnings: list = field(default_factory=list)

    def summary(self) -> str:
        lignes = [
            self.materiaux_utilises,
            f"Ciment : {self.cement_final:.0f} kg/m3"
            + (f"  +  {self.addition_label} : {self.addition_mass:.0f} kg/m3" if self.addition_mass else ""),
            f"Eau : {self.water_final:.0f} L/m3",
            f"Resistance predite (apres addition) : {self.predicted_strength_final:.1f} MPa",
            f"Cout relatif : {self.cost:.2f}   CO2 : {self.co2:.1f} kg/m3",
        ]
        lignes.extend(f"!  {w}" for w in self.warnings)
        return "\n".join(lignes)


class LocalMaterialsFormulationAssistant:

    def __init__(self):
        self.assistant = FormulationAssistant()

    def propose(
        self,
        target_strength: float,
        dmax: float,
        cement_key: str,
        sable_key: str,
        granulat_key: str,
        addition_key: str = None,
        consistency_class: str = None,
        affaissement_cm: str = None,
        exposure_class: str = None,
        age: int = 28,
    ) -> LocalFormulationResult:

        if cement_key not in CIMENTS_LOCAUX:
            raise ValueError(f"Ciment local inconnu : {cement_key}. Choix : {list(CIMENTS_LOCAUX)}")
        if sable_key not in SABLES_LOCAUX:
            raise ValueError(f"Sable local inconnu : {sable_key}. Choix : {list(SABLES_LOCAUX)}")
        if granulat_key not in GRANULATS_LOCAUX:
            raise ValueError(f"Granulat local inconnu : {granulat_key}. Choix : {list(GRANULATS_LOCAUX)}")
        if addition_key is not None and addition_key not in ADDITIONS_LOCALES:
            raise ValueError(f"Addition locale inconnue : {addition_key}. Choix : {list(ADDITIONS_LOCALES)}")

        ciment_profil = CIMENTS_LOCAUX[cement_key]
        sable_profil = SABLES_LOCAUX[sable_key]
        granulat_profil = GRANULATS_LOCAUX[granulat_key]
        addition_profil = ADDITIONS_LOCALES[addition_key] if addition_key else None

        verif = self.assistant.propose_and_verify(
            target_strength=target_strength,
            dmax=dmax,
            cement_true_class=ciment_profil.true_class_mpa,
            consistency_class=consistency_class,
            affaissement_cm=affaissement_cm,
            sand_fineness_modulus=sable_profil.fineness_modulus,
            sable_forme=sable_profil.forme,
            gravier_forme=granulat_profil.forme,
            granulat_quality=granulat_profil.quality,
            exposure_class=exposure_class,
            age=age,
        )

        mix = verif.mix
        warnings = list(mix.warnings)

        # ---- Substitution partielle du ciment par l'addition locale ----
        if addition_profil:
            taux = addition_profil.taux_substitution
            addition_mass = mix.cement * taux
            cement_final = mix.cement - addition_mass
            water_final = mix.water * addition_profil.facteur_eau

            values = [
                round(cement_final, 1), 0.0, round(addition_mass, 1),
                round(water_final, 1), 0.0,
                round(mix.gravel, 1), round(mix.sand, 1), mix.age,
            ]
            predicted_final = float(self.assistant.predictor.predict(values))
            warnings.append(
                f"{addition_profil.label} substitue a {taux*100:.0f}% du ciment "
                f"(valeurs de substitution/impact indicatives, non mesurees "
                f"localement - {addition_profil.note})"
            )
        else:
            addition_mass = 0.0
            cement_final = mix.cement
            water_final = mix.water
            predicted_final = verif.predicted_strength

        # ---- Cout / CO2 (materiaux + addition) --------------------------
        mix_dict = {
            "cement": cement_final, "water": water_final,
            "sand": mix.sand, "gravel": mix.gravel,
            "superplasticizer": 0.0, "slag": 0.0, "silica_fume": 0.0,
        }
        cost = evaluate_cost(mix_dict)
        co2 = evaluate_co2(mix_dict)
        if addition_profil:
            cost += addition_mass * addition_profil.cout_relatif
            co2 += addition_mass * addition_profil.co2_kg_par_kg

        materiaux_utilises = (
            f"Ciment : {ciment_profil.label} | Sable : {sable_profil.label} | "
            f"Granulat : {granulat_profil.label}"
            + (f" | Addition : {addition_profil.label}" if addition_profil else "")
        )

        return LocalFormulationResult(
            verification=verif,
            cement_final=cement_final,
            addition_mass=addition_mass,
            addition_label=addition_profil.label if addition_profil else "",
            water_final=water_final,
            predicted_strength_final=predicted_final,
            cost=cost,
            co2=co2,
            materiaux_utilises=materiaux_utilises,
            warnings=warnings,
        )


if __name__ == "__main__":
    assistant = LocalMaterialsFormulationAssistant()

    result = assistant.propose(
        target_strength=30,
        dmax=20,
        cement_key="cem2_425_local",
        sable_key="sable_riviere",
        granulat_key="granite_concasse",
        addition_key="cendre_balle_riz",
        consistency_class="S3",
    )

    print(result.summary())
