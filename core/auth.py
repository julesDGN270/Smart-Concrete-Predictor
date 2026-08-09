"""
Gestion des comptes (particulier / entreprise) - core/auth.py
================================================================

Utilise la meme base SQLite que core/database.py (history/concrete_history.db).
Partage entre la version bureau (customtkinter) et la version web (Flask) :
aucune des deux ne doit dupliquer cette logique.

Regles de compte
-----------------
- Un compte est identifie par une adresse email OU un numero de telephone
  (colonne "contact"), jamais par un pseudo libre.
- Une meme adresse/numero ne peut correspondre qu'a UN SEUL compte
  (contrainte UNIQUE en base + verification explicite avant creation).
- A l'inscription, un code de verification a 6 chiffres est genere et doit
  etre envoye au contact (voir core/notifications.py). Le compte reste
  "non verifie" (is_verified=0) et ne peut pas se connecter tant que le
  code n'a pas ete valide.
- Chaque code expire 10 minutes apres sa generation (EXPIRY_SECONDS).

Comptes entreprise
------------------
Une entreprise est une equipe partagee : plusieurs comptes peuvent
rejoindre la meme entreprise (table companies) via un code d'invitation
genere a la creation. Le createur devient "admin" (seul a pouvoir
supprimer l'historique partage), les suivants qui rejoignent avec le
code sont "membre".
"""

import sqlite3
import os
import re
import time
import hashlib
import hmac
import secrets
import string
from datetime import datetime

DB_PATH = os.path.join("history", "concrete_history.db")

ACCOUNT_TYPES = ("particulier", "entreprise")
ROLES = ("admin", "membre")

EXPIRY_SECONDS = 10 * 60  # 10 minutes

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 ]{7,14}$")


def detect_contact_type(contact):
    contact = (contact or "").strip()
    if EMAIL_RE.match(contact):
        return "email"
    if PHONE_RE.match(contact):
        return "telephone"
    return None


def _generate_invite_code(length=7):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_verification_code():
    return "".join(secrets.choice(string.digits) for _ in range(6))


class Auth:

    def __init__(self, db_path=DB_PATH):
        os.makedirs("history", exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_code TEXT UNIQUE NOT NULL,
                created_at TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT UNIQUE NOT NULL,
                contact_type TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                account_type TEXT NOT NULL DEFAULT 'particulier',
                organisation TEXT,
                plan TEXT NOT NULL DEFAULT 'pro',
                plan_gratuit INTEGER NOT NULL DEFAULT 1,
                company_id INTEGER,
                role TEXT,
                is_verified INTEGER NOT NULL DEFAULT 0,
                verification_code TEXT,
                verification_expires_at REAL,
                created_at TEXT
            )
        """)
        self.connection.commit()

        # Migration douce si une ancienne base "username" existe encore.
        self.cursor.execute("PRAGMA table_info(users)")
        existing_cols = [row[1] for row in self.cursor.fetchall()]
        for col, ddl in (
            ("is_verified", "ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0"),
            ("verification_code", "ALTER TABLE users ADD COLUMN verification_code TEXT"),
            ("verification_expires_at", "ALTER TABLE users ADD COLUMN verification_expires_at REAL"),
        ):
            if col not in existing_cols:
                self.cursor.execute(ddl)
                self.connection.commit()

    @staticmethod
    def _hash_password(password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
        )
        return digest.hex(), salt

    # ---------------------------------------------------------------
    # Entreprises
    # ---------------------------------------------------------------

    def create_company(self, name):
        name = (name or "").strip()
        if not name:
            return None, None, "Nom d'entreprise requis."

        for _ in range(5):
            code = _generate_invite_code()
            self.cursor.execute("SELECT id FROM companies WHERE invite_code=?", (code,))
            if not self.cursor.fetchone():
                break
        else:
            return None, None, "Impossible de generer un code, reessayez."

        self.cursor.execute("""
            INSERT INTO companies(name, invite_code, created_at)
            VALUES (?,?,?)
        """, (name, code, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        self.connection.commit()
        return self.cursor.lastrowid, code, None

    def find_company_by_code(self, invite_code):
        self.cursor.execute(
            "SELECT id, name, invite_code FROM companies WHERE invite_code=?",
            ((invite_code or "").strip().upper(),)
        )
        row = self.cursor.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "invite_code": row[2]}

    # ---------------------------------------------------------------
    # Inscription / verification
    # ---------------------------------------------------------------

    def register(self, contact, password, account_type="particulier",
                 company_mode=None, company_name=None, invite_code=None):
        """Cree un compte non verifie et renvoie (user_id, code, error).

        Le code retourne doit etre transmis par l'appelant via
        core/notifications.py (email ou SMS) ; il n'est jamais envoye
        automatiquement par cette methode, pour garder la logique de
        compte independante du canal d'envoi.
        """
        contact = (contact or "").strip()
        contact_type = detect_contact_type(contact)
        if contact_type is None:
            return None, None, "Adresse email ou numero de telephone invalide."
        if not password:
            return None, None, "Mot de passe requis."
        if account_type not in ACCOUNT_TYPES:
            account_type = "particulier"

        self.cursor.execute("SELECT id FROM users WHERE contact=?", (contact,))
        if self.cursor.fetchone():
            return None, None, "Un compte existe deja avec cette adresse ou ce numero."

        company_id = None
        organisation = None
        role = None

        if account_type == "entreprise":
            if company_mode == "creer":
                company_id, code, error = self.create_company(company_name)
                if error:
                    return None, None, error
                organisation = (company_name or "").strip()
                role = "admin"
            elif company_mode == "rejoindre":
                company = self.find_company_by_code(invite_code)
                if not company:
                    return None, None, "Code d'invitation invalide."
                company_id = company["id"]
                organisation = company["name"]
                role = "membre"
            else:
                return None, None, "Precisez si vous creez ou rejoignez une entreprise."

        password_hash, salt = self._hash_password(password)
        verification_code = _generate_verification_code()
        expires_at = time.time() + EXPIRY_SECONDS

        self.cursor.execute("""
            INSERT INTO users(
                contact, contact_type, password_hash, salt, account_type,
                organisation, plan, plan_gratuit, company_id, role,
                is_verified, verification_code, verification_expires_at, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            contact, contact_type, password_hash, salt, account_type, organisation,
            "pro", 1, company_id, role,
            0, verification_code, expires_at,
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        ))
        self.connection.commit()
        return self.cursor.lastrowid, verification_code, None

    def resend_code(self, contact):
        contact = (contact or "").strip()
        self.cursor.execute(
            "SELECT id, is_verified FROM users WHERE contact=?", (contact,)
        )
        row = self.cursor.fetchone()
        if not row:
            return None, "Compte introuvable."
        if row[1]:
            return None, "Ce compte est deja verifie."

        verification_code = _generate_verification_code()
        expires_at = time.time() + EXPIRY_SECONDS
        self.cursor.execute(
            "UPDATE users SET verification_code=?, verification_expires_at=? WHERE id=?",
            (verification_code, expires_at, row[0])
        )
        self.connection.commit()
        return verification_code, None

    def verify_account(self, contact, code):
        contact = (contact or "").strip()
        code = (code or "").strip()
        self.cursor.execute(
            "SELECT id, is_verified, verification_code, verification_expires_at FROM users WHERE contact=?",
            (contact,)
        )
        row = self.cursor.fetchone()
        if not row:
            return False, "Compte introuvable."

        user_id, is_verified, stored_code, expires_at = row
        if is_verified:
            return True, None
        if not stored_code or not hmac.compare_digest(stored_code, code):
            return False, "Code de verification incorrect."
        if expires_at is None or time.time() > expires_at:
            return False, "Ce code a expire (validite 10 minutes). Demandez-en un nouveau."

        self.cursor.execute(
            "UPDATE users SET is_verified=1, verification_code=NULL, verification_expires_at=NULL WHERE id=?",
            (user_id,)
        )
        self.connection.commit()
        return True, None

    # ---------------------------------------------------------------
    # Connexion
    # ---------------------------------------------------------------

    def login(self, contact, password):
        contact = (contact or "").strip()
        self.cursor.execute("""
            SELECT id, contact, password_hash, salt, account_type,
                   organisation, plan, plan_gratuit, company_id, role, is_verified
            FROM users WHERE contact=?
        """, (contact,))
        row = self.cursor.fetchone()
        if not row:
            return None, "Compte introuvable."

        (user_id, contact_val, password_hash, salt, account_type, organisation,
         plan, plan_gratuit, company_id, role, is_verified) = row

        check_hash, _ = self._hash_password(password or "", salt)
        if not hmac.compare_digest(check_hash, password_hash):
            return None, "Mot de passe incorrect."

        if not is_verified:
            return None, "Compte non verifie. Entrez le code recu pour l'activer."

        invite_code = None
        if company_id is not None:
            self.cursor.execute("SELECT invite_code FROM companies WHERE id=?", (company_id,))
            code_row = self.cursor.fetchone()
            invite_code = code_row[0] if code_row else None

        user = {
            "id": user_id,
            "contact": contact_val,
            "account_type": account_type,
            "organisation": organisation,
            "plan": plan,
            "plan_gratuit": bool(plan_gratuit),
            "company_id": company_id,
            "role": role,
            "invite_code": invite_code,
        }
        return user, None

    def get_user(self, user_id):
        """Recharge un compte deja verifie a partir de son id (utile pour
        une session web : on ne veut pas re-demander le mot de passe a
        chaque requete)."""
        self.cursor.execute("""
            SELECT id, contact, account_type, organisation, plan,
                   plan_gratuit, company_id, role, is_verified
            FROM users WHERE id=?
        """, (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        (uid, contact, account_type, organisation, plan,
         plan_gratuit, company_id, role, is_verified) = row
        if not is_verified:
            return None

        invite_code = None
        if company_id is not None:
            self.cursor.execute("SELECT invite_code FROM companies WHERE id=?", (company_id,))
            code_row = self.cursor.fetchone()
            invite_code = code_row[0] if code_row else None

        return {
            "id": uid,
            "contact": contact,
            "account_type": account_type,
            "organisation": organisation,
            "plan": plan,
            "plan_gratuit": bool(plan_gratuit),
            "company_id": company_id,
            "role": role,
            "invite_code": invite_code,
        }

    def close(self):
        self.connection.close()
