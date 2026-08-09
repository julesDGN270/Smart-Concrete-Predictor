"""
Envoi des codes de verification - core/notifications.py
=========================================================

Separe volontairement de core/auth.py : la logique de compte ne doit
pas dependre du canal d'envoi.

Email : utilise smtplib (aucune dependance externe) avec les identifiants
fournis par variables d'environnement :
    SCP_SMTP_HOST, SCP_SMTP_PORT, SCP_SMTP_USER, SCP_SMTP_PASSWORD,
    SCP_SMTP_FROM (adresse expediteur affichee)

SMS : nécessite un fournisseur payant (Twilio, Vonage, etc.), non inclus
ici. La fonction send_sms_code() est prete a etre branchee dessus des
que vous aurez un compte chez l'un de ces prestataires (voir le TODO
dans le code).

Mode demo : si aucun SMTP n'est configure (variables absentes), le code
est simplement affiche dans la console/les logs au lieu d'echouer,
pour que l'inscription reste testable pendant le developpement.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger("smart_concrete_predictor.notifications")
logging.basicConfig(level=logging.INFO)


def _smtp_configured():
    return all(
        os.environ.get(var)
        for var in ("SCP_SMTP_HOST", "SCP_SMTP_USER", "SCP_SMTP_PASSWORD")
    )


def send_email_code(to_address, code):
    subject = "Smart Concrete Predictor - Code de verification"
    body = (
        f"Votre code de verification est : {code}\n\n"
        f"Ce code expire dans 10 minutes.\n"
        f"Si vous n'etes pas a l'origine de cette demande, ignorez ce message."
    )

    if not _smtp_configured():
        logger.info("[MODE DEMO - SMTP non configure] Code pour %s : %s", to_address, code)
        return True, None

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
        logger.error("Echec envoi email a %s : %s", to_address, exc)
        return False, str(exc)


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
