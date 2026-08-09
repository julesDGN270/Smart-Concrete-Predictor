"""Fenetre de connexion / creation de compte.

Affichee avant le tableau de bord : tant qu'aucun compte verifie n'est
authentifie, le reste de l'application (predictions, historique,
analyse) n'est pas accessible. Chaque compte (particulier ou
entreprise) beneficie du plan Pro offert gratuitement pendant la
phase de lancement (voir core/auth.py).

Les comptes sont identifies par une adresse email ou un numero de
telephone (jamais un pseudo libre) et doivent etre confirmes par un
code a 6 chiffres valable 10 minutes (voir core/notifications.py).

Un compte entreprise peut soit creer une nouvelle equipe (l'utilisateur
devient alors admin et recoit un code d'invitation a partager), soit
rejoindre une equipe existante avec ce code (statut membre).
"""

import customtkinter as ctk
from tkinter import messagebox
from core.auth import Auth
from core.notifications import send_verification_code

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class LoginWindow(ctk.CTk):

    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.auth = Auth()
        self.pending_contact = None  # contact en attente de verification

        self.title("Smart Concrete Predictor - Connexion")
        self.geometry("440x700")
        self.resizable(False, False)

        ctk.CTkLabel(
            self, text="SMART CONCRETE\nPREDICTOR",
            font=("Arial", 22, "bold"), justify="center"
        ).pack(pady=(25, 8))
        ctk.CTkLabel(
            self, text="Plan Pro offert pendant le lancement",
            font=("Arial", 12), text_color="#2FA84F"
        ).pack(pady=(0, 15))

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self._build_tabs_view()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Vue principale : connexion / creation de compte
    # ------------------------------------------------------------------

    def _build_tabs_view(self):
        self._clear_container()

        self.tabs = ctk.CTkTabview(self.container, width=380, height=560)
        self.tabs.pack(pady=10)
        self.tab_login = self.tabs.add("Connexion")
        self.tab_register = self.tabs.add("Creer un compte")

        self._build_login_tab()
        self._build_register_tab()

    def _build_login_tab(self):
        tab = self.tab_login
        ctk.CTkLabel(tab, text="Email ou numero de telephone").pack(pady=(20, 0))
        self.login_contact = ctk.CTkEntry(tab, width=290, placeholder_text="ex: jules@mail.com ou +22990000000")
        self.login_contact.pack(pady=(5, 10))
        self.login_password = ctk.CTkEntry(tab, width=290, placeholder_text="Mot de passe", show="*")
        self.login_password.pack(pady=10)
        ctk.CTkButton(tab, text="Se connecter", width=200, command=self.handle_login).pack(pady=20)
        self.login_password.bind("<Return>", lambda e: self.handle_login())

    def handle_login(self):
        contact = self.login_contact.get()
        password = self.login_password.get()
        user, error = self.auth.login(contact, password)
        if error:
            if "non verifie" in error:
                if messagebox.askyesno(
                    "Compte non verifie",
                    "Ce compte n'a pas encore ete confirme. Voulez-vous saisir le code recu maintenant ?"
                ):
                    self._show_verification_view(contact)
                return
            messagebox.showerror("Connexion", error)
            return
        self._complete(user)

    # ------------------------------------------------------------------
    # Onglet creation de compte
    # ------------------------------------------------------------------

    def _build_register_tab(self):
        tab = self.tab_register

        ctk.CTkLabel(tab, text="Type de compte").pack(pady=(15, 0))
        self.reg_account_type = ctk.CTkOptionMenu(
            tab, values=["particulier", "entreprise"], command=self._on_account_type_change
        )
        self.reg_account_type.pack(pady=(0, 10))

        # ---- Bloc specifique entreprise (cree dynamiquement) ----
        self.company_frame = ctk.CTkFrame(tab, fg_color="transparent")

        self.company_mode = ctk.CTkSegmentedButton(
            self.company_frame,
            values=["Creer une entreprise", "Rejoindre une entreprise"],
            command=self._on_company_mode_change,
        )
        self.company_mode.set("Creer une entreprise")
        self.company_mode.pack(pady=(5, 10))

        self.company_name_entry = ctk.CTkEntry(
            self.company_frame, width=290, placeholder_text="Nom de l'entreprise"
        )
        self.invite_code_entry = ctk.CTkEntry(
            self.company_frame, width=290, placeholder_text="Code d'invitation recu"
        )
        self.company_name_entry.pack(pady=6)

        # ---- Champs communs ----
        ctk.CTkLabel(tab, text="Email ou numero de telephone").pack(pady=(5, 0))
        self.reg_contact = ctk.CTkEntry(tab, width=290, placeholder_text="ex: jules@mail.com ou +22990000000")
        self.reg_password = ctk.CTkEntry(tab, width=290, placeholder_text="Mot de passe", show="*")
        self.register_button = ctk.CTkButton(tab, text="Creer le compte", width=200, command=self.handle_register)

        self.reg_contact.pack(pady=8)
        self.reg_password.pack(pady=8)
        self.register_button.pack(pady=20)

    def _on_account_type_change(self, value):
        if value == "entreprise":
            self.company_frame.pack(before=self.reg_contact, pady=5)
        else:
            self.company_frame.pack_forget()

    def _on_company_mode_change(self, value):
        if value == "Creer une entreprise":
            self.invite_code_entry.pack_forget()
            self.company_name_entry.pack(pady=6)
        else:
            self.company_name_entry.pack_forget()
            self.invite_code_entry.pack(pady=6)

    def handle_register(self):
        contact = self.reg_contact.get()
        password = self.reg_password.get()
        account_type = self.reg_account_type.get()

        company_mode = None
        company_name = None
        invite_code = None

        if account_type == "entreprise":
            if self.company_mode.get() == "Creer une entreprise":
                company_mode = "creer"
                company_name = self.company_name_entry.get()
            else:
                company_mode = "rejoindre"
                invite_code = self.invite_code_entry.get()

        user_id, code, error = self.auth.register(
            contact, password, account_type,
            company_mode=company_mode, company_name=company_name, invite_code=invite_code,
        )
        if error:
            messagebox.showerror("Creation de compte", error)
            return

        from core.auth import detect_contact_type
        contact_type = detect_contact_type(contact)
        sent, send_error = send_verification_code(contact.strip(), contact_type, code)
        if not sent:
            messagebox.showwarning(
                "Envoi du code",
                f"Le compte a ete cree mais l'envoi du code a echoue ({send_error}).\n"
                f"Verifiez la configuration d'envoi (voir core/notifications.py)."
            )

        messagebox.showinfo(
            "Verification requise",
            "Un code a 6 chiffres vient de vous etre envoye (valable 10 minutes)."
        )
        self._show_verification_view(contact.strip())

    # ------------------------------------------------------------------
    # Vue de verification du code
    # ------------------------------------------------------------------

    def _show_verification_view(self, contact):
        self.pending_contact = contact
        self._clear_container()

        ctk.CTkLabel(
            self.container, text="Verification du compte",
            font=("Arial", 18, "bold")
        ).pack(pady=(30, 5))
        ctk.CTkLabel(
            self.container, text=f"Code envoye a : {contact}\nValable 10 minutes.",
            font=("Arial", 12), justify="center"
        ).pack(pady=(0, 20))

        self.code_entry = ctk.CTkEntry(self.container, width=200, placeholder_text="Code a 6 chiffres")
        self.code_entry.pack(pady=10)
        self.code_entry.bind("<Return>", lambda e: self.handle_verify())

        ctk.CTkButton(self.container, text="Valider", width=200, command=self.handle_verify).pack(pady=15)
        ctk.CTkButton(
            self.container, text="Renvoyer le code", fg_color="transparent", border_width=1,
            command=self.handle_resend
        ).pack(pady=5)
        ctk.CTkButton(
            self.container, text="Retour", fg_color="transparent", border_width=1,
            command=self._build_tabs_view
        ).pack(pady=5)

    def handle_verify(self):
        code = self.code_entry.get()
        ok, error = self.auth.verify_account(self.pending_contact, code)
        if not ok:
            messagebox.showerror("Verification", error)
            return
        messagebox.showinfo("Compte verifie", "Votre compte est confirme, vous pouvez maintenant vous connecter.")
        self._build_tabs_view()

    def handle_resend(self):
        from core.auth import detect_contact_type
        code, error = self.auth.resend_code(self.pending_contact)
        if error:
            messagebox.showerror("Renvoi du code", error)
            return
        contact_type = detect_contact_type(self.pending_contact)
        sent, send_error = send_verification_code(self.pending_contact, contact_type, code)
        if not sent:
            messagebox.showwarning("Envoi du code", f"Echec de l'envoi ({send_error}).")
            return
        messagebox.showinfo("Code renvoye", "Un nouveau code vient d'etre envoye (valable 10 minutes).")

    # ------------------------------------------------------------------

    def _complete(self, user):
        self.auth.close()
        self.destroy()
        self.on_success(user)

    def _on_close(self):
        self.auth.close()
        self.destroy()


def show_login(on_success):
    """Point d'entree pratique : cree et lance la fenetre de connexion."""
    window = LoginWindow(on_success)
    window.mainloop()
