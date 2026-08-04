"""
Assistant de formulation - Phase 2 : verification par le modele CatBoost
==========================================================================

Relie le moteur de formulation classique (Dreux-Gorisse, core/mix_design.py)
au modele CatBoost (core/predictor.py) : la formulation calculee
analytiquement est injectee dans le modele pour verifier la resistance
predite et mesurer l'ecart avec la resistance cible.

Toujours sans interface : ce module s'utilise et se teste seul,
en attendant l'integration dans le tableau de bord.
"""

from dataclasses import dataclass, field

from core.mix_design import DreuxGorisseMixDesign, MixDesignResult
from core.predictor import ConcretePredictor

TOLERANCE_MPA = 2.0


@dataclass
class FormulationVerification:
    mix: MixDesignResult
    target_strength: float
    predicted_strength: float
    error: float
    error_pct: float
    conforme: bool

    def summary(self) -> str:
        statut = "conforme" if self.conforme else "a ajuster"
        signe = "+" if self.error >= 0 else ""
        return (
            f"Resistance cible : {self.target_strength:.1f} MPa\n"
            f"Resistance predite : {self.predicted_strength:.1f} MPa\n"
            f"Ecart : {signe}{self.error:.1f} MPa ({signe}{self.error_pct:.1f}%) "
            f"-> {statut}"
        )


class FormulationAssistant:

    def __init__(
        self,
        granulat_quality: str = "bonne",
        tolerance_mpa: float = TOLERANCE_MPA,
    ):
        self.mix_engine = DreuxGorisseMixDesign(granulat_quality=granulat_quality)
        self.predictor = ConcretePredictor()
        self.tolerance_mpa = tolerance_mpa

    def propose_and_verify(
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
        exposure_class: str = None,
        granulat_quality: str = None,
    ) -> FormulationVerification:

        mix = self.mix_engine.design(
            target_strength=target_strength,
            dmax=dmax,
            consistency_class=consistency_class,
            affaissement_cm=affaissement_cm,
            cement_true_class=cement_true_class,
            age=age,
            sand_fineness_modulus=sand_fineness_modulus,
            vibration=vibration,
            sable_forme=sable_forme,
            gravier_forme=gravier_forme,
            pompable=pompable,
            exposure_class=exposure_class,
            granulat_quality=granulat_quality,
        )

        predicted = float(self.predictor.predict(mix.as_predictor_values()))

        error = predicted - target_strength
        error_pct = (error / target_strength) * 100 if target_strength else 0.0
        conforme = abs(error) <= self.tolerance_mpa

        return FormulationVerification(
            mix=mix,
            target_strength=target_strength,
            predicted_strength=predicted,
            error=error,
            error_pct=error_pct,
            conforme=conforme,
        )


if __name__ == "__main__":
    assistant = FormulationAssistant(granulat_quality="bonne")

    cas = [
        dict(target_strength=25, consistency_class="S2", cement_true_class=44.0, dmax=20),
        dict(target_strength=30, consistency_class="S3", cement_true_class=50.0, dmax=20),
        dict(target_strength=40, consistency_class="S3", cement_true_class=50.0, dmax=12.5),
    ]

    for c in cas:
        verif = assistant.propose_and_verify(**c)
        print("=" * 60)
        print(c)
        print(verif.summary())
        m = verif.mix
        print(
            f"Mix : C={m.cement:.0f}  E={m.water:.0f}  S={m.sand:.0f}  "
            f"G={m.gravel:.0f}  E/C={m.ec_ratio:.3f}"
        )
        for w in m.warnings:
            print(f" !  {w}")
        print()
