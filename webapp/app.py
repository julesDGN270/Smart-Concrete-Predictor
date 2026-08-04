"""
Smart Concrete Predictor - version web (Flask)
=================================================

Reutilise directement les modules core.* (aucune duplication de logique
metier) : seule l'interface change par rapport a la version desktop.

Lancement local :
    python webapp/app.py
(depuis la racine du projet, pour que "core" soit importable)

Deploiement : voir DEPLOY_WEB.md
"""

import os
import sys

# Permet d'importer core.* meme si ce script est lance depuis webapp/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request

from core.predictor import ConcretePredictor
from core.formulation_assistant import FormulationAssistant

app = Flask(__name__)

predictor = ConcretePredictor()
assistant = FormulationAssistant()


@app.route("/", methods=["GET", "POST"])
def predict_page():
    prediction = None
    error = None
    form_values = None

    if request.method == "POST":
        form_values = request.form
        try:
            values = [
                float(request.form["cement"]),
                float(request.form.get("slag") or 0),
                float(request.form.get("fly_ash") or 0),
                float(request.form["water"]),
                float(request.form.get("superplasticizer") or 0),
                float(request.form["coarse"]),
                float(request.form["fine"]),
                float(request.form["age"]),
            ]
            prediction = float(predictor.predict(values))
        except (ValueError, KeyError):
            error = "Merci de renseigner des valeurs numeriques valides pour tous les champs obligatoires."

    return render_template(
        "index.html", active="predict",
        prediction=prediction, error=error, form_values=form_values,
    )


@app.route("/formulation", methods=["GET", "POST"])
def formulation_page():
    result = None
    error = None
    form_values = None

    if request.method == "POST":
        form_values = request.form
        try:
            sigma = request.form.get("cement_true_class", "").strip()
            affaissement = request.form.get("affaissement_cm", "").strip()
            exposure = request.form.get("exposure_class", "").strip()

            result = assistant.propose_and_verify(
                target_strength=float(request.form["target_strength"]),
                dmax=float(request.form["dmax"]),
                affaissement_cm=float(affaissement) if affaissement else None,
                cement_true_class=float(sigma) if sigma else None,
                sand_fineness_modulus=float(request.form.get("sand_fineness_modulus") or 2.5),
                exposure_class=exposure or None,
                granulat_quality=request.form.get("granulat_quality") or "bonne",
            )
        except (ValueError, KeyError) as e:
            error = f"Parametres invalides : {e}"
        except Exception as e:
            error = f"Erreur lors du calcul : {e}"

    return render_template(
        "formulation.html", active="formulation",
        result=result, error=error, form_values=form_values,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
