"""
Optimiseur v2 - Phase 4
=========================

Part de la formulation Dreux-Gorisse (core.formulation_assistant) plutot
que d'une recherche aleatoire a l'aveugle, et l'ajuste par perturbations
locales selon l'objectif choisi par l'utilisateur :

  - "cible"     : coller au plus pres a la resistance cible
  - "cout"      : minimiser le cout, resistance predite >= cible
  - "co2"       : minimiser l'empreinte CO2, resistance predite >= cible
  - "compromis" : minimiser une somme ponderee (cout + co2), meme contrainte

Toujours sans interface graphique.
"""

import random
from dataclasses import dataclass, field

from core.formulation_assistant import FormulationAssistant, FormulationVerification
from core.constraints import ConcreteConstraints
from core.cost_co2_data import evaluate_cost, evaluate_co2

OBJECTIFS_VALIDES = ("cible", "cout", "co2", "compromis")


@dataclass
class OptimizationResult:
    objective: str
    baseline: FormulationVerification
    best_mix: dict            # {cement, water, sand, gravel, superplasticizer, slag, silica_fume}
    predicted_strength: float
    target_strength: float
    cost: float
    co2: float
    recommendations: list = field(default_factory=list)

    def summary(self) -> str:
        lignes = [
            f"Objectif : {self.objective}",
            f"Resistance cible : {self.target_strength:.1f} MPa   "
            f"Resistance estimee : {self.predicted_strength:.1f} MPa",
            f"Cout relatif : {self.cost:.2f}   CO2 : {self.co2:.1f} kg/m3",
        ]
        lignes.extend(f"- {r}" for r in self.recommendations)
        return "\n".join(lignes)


class ConcreteOptimizerV2:

    def __init__(self, granulat_quality: str = "bonne", n_trials: int = 3000):
        self.assistant = FormulationAssistant(granulat_quality=granulat_quality)
        self.constraints = ConcreteConstraints()
        self.n_trials = n_trials

    # -------------------------------------------------------------
    def _mix_to_dict(self, values8, sp=0.0, slag=None, silica_fume=None):
        cement, s_, fa_, water, _, coarse, fine, age = values8
        return {
            "cement": cement,
            "water": water,
            "sand": fine,
            "gravel": coarse,
            "superplasticizer": sp,
            "slag": slag if slag is not None else s_,
            "silica_fume": silica_fume if silica_fume is not None else fa_,
        }

    def _score(self, objective, predicted, target, cost, co2, tolerance=2.0):
        if objective == "cible":
            return abs(predicted - target)

        # Pour cout / co2 / compromis : la resistance predite doit rester
        # au-dessus de la cible (moins la tolerance) ; sinon on penalise
        # fortement pour ecarter ces candidats.
        if predicted < target - tolerance:
            penalite = (target - tolerance - predicted) * 1000
        else:
            penalite = 0

        if objective == "cout":
            return cost + penalite
        if objective == "co2":
            return co2 + penalite
        if objective == "compromis":
            # normalisation grossiere pour ponderer cout et co2 a poids egal
            return (cost / 400) + (co2 / 300) + penalite
        raise ValueError(objective)

    # -------------------------------------------------------------
    def optimize(
        self,
        target_strength: float,
        dmax: float,
        cement_true_class: float = None,
        consistency_class: str = None,
        affaissement_cm: float = None,
        exposure_class: str = None,
        age: int = 28,
        objective: str = "cible",
    ) -> OptimizationResult:

        if objective not in OBJECTIFS_VALIDES:
            raise ValueError(f"Objectif invalide : {objective}. Choix : {OBJECTIFS_VALIDES}")

        baseline = self.assistant.propose_and_verify(
            target_strength=target_strength,
            dmax=dmax,
            consistency_class=consistency_class,
            affaissement_cm=affaissement_cm,
            cement_true_class=cement_true_class,
            exposure_class=exposure_class,
            age=age,
        )

        base_values = baseline.mix.as_predictor_values()
        base_dict = self._mix_to_dict(base_values)

        best_dict = dict(base_dict)
        best_predicted = baseline.predicted_strength
        best_cost = evaluate_cost(base_dict)
        best_co2 = evaluate_co2(base_dict)
        best_score = self._score(objective, best_predicted, target_strength, best_cost, best_co2)

        for _ in range(self.n_trials):
            candidate = dict(base_dict)

            # Perturbations locales autour de la baseline (pas une recherche
            # aveugle sur tout l'espace : on explore le voisinage physique
            # d'une formulation deja coherente).
            candidate["cement"] += random.uniform(-150, 30)
            candidate["water"] += random.uniform(-30, 15)
            candidate["sand"] += random.uniform(-40, 40)
            candidate["gravel"] += random.uniform(-40, 40)
            candidate["superplasticizer"] = max(
                0, candidate["superplasticizer"] + random.uniform(0, 6)
            )

            mix_values = [
                candidate["cement"], candidate["slag"], candidate["silica_fume"],
                candidate["water"], candidate["superplasticizer"],
                candidate["gravel"], candidate["sand"], age,
            ]

            valid, _errors = self.constraints.validate(mix_values[:8])
            if not valid:
                continue

            predicted = float(self.assistant.predictor.predict(mix_values))
            cost = evaluate_cost(candidate)
            co2 = evaluate_co2(candidate)
            score = self._score(objective, predicted, target_strength, cost, co2)

            if score < best_score:
                best_score = score
                best_dict = candidate
                best_predicted = predicted
                best_cost = cost
                best_co2 = co2

        recommandations = self._build_recommendations(base_dict, best_dict, best_predicted, target_strength)

        return OptimizationResult(
            objective=objective,
            baseline=baseline,
            best_mix=best_dict,
            predicted_strength=best_predicted,
            target_strength=target_strength,
            cost=best_cost,
            co2=best_co2,
            recommendations=recommandations,
        )

    # -------------------------------------------------------------
    def _build_recommendations(self, base_dict, best_dict, predicted, target):
        recs = []
        delta_eau = best_dict["water"] - base_dict["water"]
        delta_ciment = best_dict["cement"] - base_dict["cement"]
        delta_sp = best_dict["superplasticizer"] - base_dict["superplasticizer"]

        if abs(delta_eau) > 1:
            sens = "Reduire" if delta_eau < 0 else "Augmenter"
            recs.append(f"{sens} l'eau de {abs(delta_eau):.0f} kg/m3")
        if abs(delta_ciment) > 1:
            sens = "Augmenter" if delta_ciment > 0 else "Reduire"
            recs.append(f"{sens} le ciment de {abs(delta_ciment):.0f} kg/m3")
        if delta_sp > 0.5:
            recs.append(f"Ajouter {delta_sp:.1f} kg/m3 de superplastifiant")

        ec = best_dict["water"] / best_dict["cement"] if best_dict["cement"] else 0
        recs.append(f"Le rapport E/C devient {ec:.2f}")
        recs.append(f"Resistance estimee : {predicted:.1f} MPa (cible {target:.1f} MPa)")
        return recs


if __name__ == "__main__":
    opt = ConcreteOptimizerV2(granulat_quality="bonne", n_trials=3000)

    params = dict(
        target_strength=30, consistency_class="S3",
        cement_true_class=50.0, dmax=20,
    )

    for objectif in OBJECTIFS_VALIDES:
        result = opt.optimize(objective=objectif, **params)
        print("=" * 60)
        print(result.summary())
