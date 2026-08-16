"""
Envoi des codes de verification - core/notifications.py
=========================================================

Separe volontairement de core/auth.py : la logique de compte ne doit
pas dependre du canal d'envoi.

Email : deux methodes disponibles, essayees dans cet ordre :

  1. API HTTP de Brevo (recommandee) - passe par HTTPS (port 443), qui
     n'est quasiment jamais bloque par les hebergeurs cloud, contrairement
     au port SMTP 587 souvent restreint sur les offres gratuites (Render
     free tier notamment). Variables :
       SCP_BREVO_API_KEY  (cle API v3, PAS la cle SMTP - a generer dans
                            Brevo > SMTP et API > onglet API Keys)
       SCP_SMTP_FROM      (adresse expediteur validee sur Brevo)

  2. SMTP classique (smtplib, aucune dependance externe) - utilise si
     SCP_BREVO_API_KEY n'est pas defini. Variables :
       SCP_SMTP_HOST, SCP_SMTP_PORT, SCP_SMTP_USER, SCP_SMTP_PASSWORD,
       SCP_SMTP_FROM

SMS : nécessite un fournisseur payant (Twilio, Vonage, etc.), non inclus
ici. La fonction send_sms_code() est prete a etre branchee dessus des
que vous aurez un compte chez l'un de ces prestataires (voir le TODO
dans le code).

Mode demo : si aucune des deux methodes email n'est configuree, le code
est simplement affiche dans la console/les logs au lieu d'echouer,
pour que l'inscription reste testable pendant le developpement.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger("smart_concrete_predictor.notifications")
logging.basicConfig(level=logging.INFO)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _brevo_api_configured():
    return bool(os.environ.get("SCP_BREVO_API_KEY"))


def _smtp_configured():
    return all(
        os.environ.get(var)
        for var in ("SCP_SMTP_HOST", "SCP_SMTP_USER", "SCP_SMTP_PASSWORD")
    )


def _send_email_via_brevo_api(to_address, subject, body):
    import requests

    api_key = os.environ["SCP_BREVO_API_KEY"]
    sender = os.environ.get("SCP_SMTP_FROM")
    if not sender:
        return False, "SCP_SMTP_FROM manquant (adresse expediteur validee sur Brevo)."

    payload = {
        "sender": {"email": sender},
        "to": [{"email": to_address}],
        "subject": subject,
        "textContent": body,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=15)
        if response.status_code in (200, 201):
            return True, None
        return False, f"Brevo API a repondu {response.status_code} : {response.text[:300]}"
    except Exception as exc:
        logger.error("Echec envoi email (API Brevo) a %s : %s", to_address, exc)
        return False, str(exc)


def _send_email_via_smtp(to_address, subject, body):
    host = os.environ["SCP_SMTP_HOST"]
    port = int(os.environ.get("SCP_SMTP_PORT", "587"))
    user = os.environ["SCP_SMTP_USER"]
    password = os.environ["SCP_SMTP_PASSWORD"]
    sender = os.environ.get("SCP_SMTP_FROM", user)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [to_address], msg.as_string())
        return True, None
    except Exception as exc:
        logger.error("Echec envoi email (SMTP) a %s : %s", to_address, exc)
        return False, str(exc)


def send_email_code(to_address, code):
    subject = "Smart Concrete Predictor - Code de verification"
    body = (
        f"Votre code de verification est : {code}\n\n"
        f"Ce code expire dans 10 minutes.\n"
        f"Si vous n'etes pas a l'origine de cette demande, ignorez ce message."
    )

    if _brevo_api_configured():
        return _send_email_via_brevo_api(to_address, subject, body)

    if _smtp_configured():
        return _send_email_via_smtp(to_address, subject, body)

    logger.info("[MODE DEMO - aucun envoi configure] Code pour %s : %s", to_address, code)
    return True, None


def send_sms_code(to_number, code):
    """A brancher sur un fournisseur SMS (Twilio, Vonage...).

    TODO : une fois un compte cree chez un prestataire, remplacer ce
    corps par l'appel a son API (ex. client Twilio `messages.create`).
    En attendant, le code est journalise en mode demo pour ne pas
    bloquer les tests.
    """
    provider_configured = bool(os.environ.get("SCP_SMS_API_KEY"))

    if not provider_configured:
        logger.info("[MODE DEMO - SMS non configure] Code pour %s : %s", to_number, code)
        return True, None

    # Exemple d'integration Twilio (a completer avec vos identifiants) :
    #
    # from twilio.rest import Client
    # client = Client(os.environ["SCP_SMS_ACCOUNT_SID"], os.environ["SCP_SMS_API_KEY"])
    # client.messages.create(
    #     body=f"Smart Concrete Predictor - code : {code} (valable 10 min)",
    #     from_=os.environ["SCP_SMS_FROM_NUMBER"],
    #     to=to_number,
    # )

    logger.warning("Fournisseur SMS configure mais integration non implementee.")
    return False, "Integration SMS non implementee - voir TODO dans core/notifications.py"


def send_verification_code(contact, contact_type, code):
    if contact_type == "email":
        return send_email_code(contact, code)
    if contact_type == "telephone":
        return send_sms_code(contact, code)
    return False, "Type de contact inconnu."
