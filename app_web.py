"""
Smart Concrete Predictor - version web (Flask)
================================================

Reutilise directement les modules de core/ (auth, database, notifications,
predictor) : la logique metier est strictement identique a la version
bureau, seule l'interface change.

Lancement local :
    pip install -r requirements-web.txt
    python app_web.py

Deploiement (Render, etc.) :
    Procfile -> web: gunicorn app_web:app
    Variables d'environnement a definir :
      SCP_SECRET_KEY        (obligatoire en production)
      SCP_SMTP_HOST / SCP_SMTP_USER / SCP_SMTP_PASSWORD / SCP_SMTP_FROM
      SCP_SMTP_PORT (optionnel, 587 par defaut)

Note base de donnees : SQLite (history/concrete_history.db) convient pour
la phase de lancement mais son fichier n'est pas persistant sur la plupart
des hebergeurs gratuits (systeme de fichiers ephemere) : chaque redeploiement
peut effacer les comptes/l'historique. Pour une mise en production durable,
prevoir une base geree (ex. Postgres, souvent offerte par Render).
"""

import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)

from core.auth import Auth, detect_contact_type
from core.notifications import send_verification_code
from core.database import Database
from core.predictor import ConcretePredictor

app = Flask(__name__, template_folder="web_templates", static_folder="web_static")
app.secret_key = os.environ.get("SCP_SECRET_KEY", "dev-key-a-changer-en-production")

_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = ConcretePredictor()
    return _predictor


FIELDS = [
    ("cement", "Ciment (kg/m3)"),
    ("slag", "Laitier (kg/m3)"),
    ("fly_ash", "Cendres volantes (kg/m3)"),
    ("water", "Eau (kg/m3)"),
    ("superplasticizer", "Superplastifiant (kg/m3)"),
    ("coarse", "Gros granulats (kg/m3)"),
    ("fine", "Granulats fins (kg/m3)"),
    ("age", "Age (jours)"),
]


# ----------------------------------------------------------------------
# Authentification
# ----------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if not session.get("user_id"):
        return None
    auth = Auth()
    user = auth.get_user(session["user_id"])
    auth.close()
    return user


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        contact = request.form.get("contact", "")
        password = request.form.get("password", "")
        account_type = request.form.get("account_type", "particulier")
        company_mode = request.form.get("company_mode")
        company_name = request.form.get("company_name")
        invite_code = request.form.get("invite_code")

        auth = Auth()
        user_id, code, error = auth.register(
            contact, password, account_type,
            company_mode=company_mode, company_name=company_name, invite_code=invite_code,
        )
        if error:
            auth.close()
            flash(error, "error")
            return render_template("register.html")

        contact_type = detect_contact_type(contact.strip())
        sent, send_error = send_verification_code(contact.strip(), contact_type, code)
        auth.close()
        if not sent:
            flash(f"Compte cree mais l'envoi du code a echoue ({send_error}).", "error")
        else:
            flash("Un code de verification a 6 chiffres vous a ete envoye (valable 10 minutes).", "success")

        session["pending_contact"] = contact.strip()
        return redirect(url_for("verify"))

    return render_template("register.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():
    contact = session.get("pending_contact")
    if not contact:
        return redirect(url_for("register"))

    if request.method == "POST":
        code = request.form.get("code", "")
        auth = Auth()
        ok, error = auth.verify_account(contact, code)
        auth.close()
        if not ok:
            flash(error, "error")
            return render_template("verify.html", contact=contact)

        session.pop("pending_contact", None)
        flash("Compte confirme, vous pouvez vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("verify.html", contact=contact)


@app.route("/resend-code", methods=["POST"])
def resend_code():
    contact = session.get("pending_contact")
    if not contact:
        return redirect(url_for("register"))

    auth = Auth()
    code, error = auth.resend_code(contact)
    if error:
        auth.close()
        flash(error, "error")
        return redirect(url_for("verify"))

    contact_type = detect_contact_type(contact)
    sent, send_error = send_verification_code(contact, contact_type, code)
    auth.close()
    if not sent:
        flash(f"Echec de l'envoi ({send_error}).", "error")
    else:
        flash("Nouveau code envoye (valable 10 minutes).", "success")
    return redirect(url_for("verify"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        contact = request.form.get("contact", "")
        password = request.form.get("password", "")
        auth = Auth()
        user, error = auth.login(contact, password)
        auth.close()

        if error:
            if "non verifie" in error:
                session["pending_contact"] = contact.strip()
                flash("Compte non verifie. Entrez le code recu.", "error")
                return redirect(url_for("verify"))
            flash(error, "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------------------------------------------------
# Tableau de bord / prediction
# ----------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    user = current_user()
    prediction = None

    if request.method == "POST":
        try:
            values = [float(request.form.get(key, 0)) for key, _ in FIELDS]
        except ValueError:
            flash("Merci de saisir des valeurs numeriques valides.", "error")
            return render_template("dashboard.html", fields=FIELDS, prediction=None)

        prediction = round(float(get_predictor().predict(values)), 2)

        db = Database()
        db.insert(
            values, prediction,
            user_id=user["id"], company_id=user.get("company_id"),
        )

    return render_template("dashboard.html", fields=FIELDS, prediction=prediction)


# ----------------------------------------------------------------------
# Historique
# ----------------------------------------------------------------------

@app.route("/historique")
@login_required
def historique():
    user = current_user()
    db = Database()
    rows = db.get_all(user_id=user["id"], company_id=user.get("company_id"))
    can_delete = user["account_type"] != "entreprise" or user["role"] == "admin"
    return render_template("historique.html", rows=rows, can_delete=can_delete)


@app.route("/historique/supprimer/<int:pred_id>", methods=["POST"])
@login_required
def supprimer_prediction(pred_id):
    user = current_user()
    can_delete = user["account_type"] != "entreprise" or user["role"] == "admin"
    if not can_delete:
        flash("Seul l'administrateur de l'entreprise peut supprimer une prediction.", "error")
        return redirect(url_for("historique"))

    db = Database()
    db.delete(pred_id)
    flash("Prediction supprimee.", "success")
    return redirect(url_for("historique"))


# ----------------------------------------------------------------------
# Analyse
# ----------------------------------------------------------------------

@app.route("/analyse")
@login_required
def analyse():
    user = current_user()
    db = Database()
    rows = db.get_all(user_id=user["id"], company_id=user.get("company_id"))

    stats = None
    chart_labels = []
    chart_values = []
    if rows:
        predictions = [r[10] for r in rows]  # colonne "prediction"
        stats = {
            "count": len(predictions),
            "avg": round(sum(predictions) / len(predictions), 2),
            "min": round(min(predictions), 2),
            "max": round(max(predictions), 2),
        }
        recent = rows[:20][::-1]
        chart_labels = [r[1] for r in recent]   # date
        chart_values = [r[10] for r in recent]  # prediction

    return render_template(
        "analyse.html", stats=stats, chart_labels=chart_labels, chart_values=chart_values
    )


# ----------------------------------------------------------------------
# Compte
# ----------------------------------------------------------------------

@app.route("/compte")
@login_required
def compte():
    user = current_user()
    return render_template("compte.html", user=user)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
