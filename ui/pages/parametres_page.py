"""Page Parametres (frame integree, logique reprise de ui/settings_window.py)."""

import customtkinter as ctk


class ParametresPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(self, text="Parametres", font=("Arial", 24, "bold")).pack(pady=20)

        user = getattr(app, "current_user", None) or {}
        compte_frame = ctk.CTkFrame(self)
        compte_frame.pack(pady=(0, 20), padx=20, fill="x")

        ctk.CTkLabel(compte_frame, text="Mon compte", font=("Arial", 18, "bold")).pack(pady=(15, 5), padx=15, anchor="w")

        type_label = "Compte entreprise" if user.get("account_type") == "entreprise" else "Compte particulier"
        organisation = user.get("organisation")
        plan_text = "Plan Pro - offert pendant la periode de lancement" if user.get("plan_gratuit") else "Plan Pro"

        details = f"Compte : {user.get('contact', 'invite')}\n{type_label}"
        if organisation:
            details += f" ({organisation})"
        details += f"\n{plan_text}"

        ctk.CTkLabel(compte_frame, text=details, justify="left", font=("Arial", 14)).pack(pady=(0, 15), padx=15, anchor="w")

        if user.get("account_type") == "entreprise" and user.get("role") == "admin" and user.get("invite_code"):
            invite_frame = ctk.CTkFrame(compte_frame, fg_color=("#EAF7EE", "#1F3D2A"))
            invite_frame.pack(pady=(0, 15), padx=15, fill="x")
            ctk.CTkLabel(
                invite_frame, text="Code d'invitation a partager avec votre equipe",
                font=("Arial", 12), justify="left"
            ).pack(pady=(10, 0), padx=12, anchor="w")
            code_row = ctk.CTkFrame(invite_frame, fg_color="transparent")
            code_row.pack(pady=(2, 10), padx=12, fill="x")
            self.invite_code_entry = ctk.CTkEntry(code_row, width=160)
            self.invite_code_entry.insert(0, user["invite_code"])
            self.invite_code_entry.configure(state="readonly")
            self.invite_code_entry.pack(side="left")
            ctk.CTkButton(
                code_row, text="Copier", width=80, command=self._copy_invite_code
            ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            compte_frame, text="Deconnexion", fg_color="transparent", border_width=1,
            command=self.app.logout
        ).pack(pady=(0, 15), padx=15, anchor="w")

        ctk.CTkLabel(self, text="Mode d'apparence").pack()
        ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], command=self.change_mode).pack(pady=10)

        ctk.CTkLabel(self, text="Theme").pack()
        ctk.CTkOptionMenu(self, values=["blue", "green", "dark-blue"], command=self.change_theme).pack(pady=10)

        info = (
            "Smart Concrete Predictor\n\n"
            "Version : 2.0\n"
            "Auteur : Jules DEGNON\n\n"
            "Application de prediction et de formulation du beton,\n"
            "basee sur le Machine Learning et la methode Dreux-Gorisse."
        )
        ctk.CTkLabel(self, text=info, justify="left").pack(pady=20)

    def change_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def change_theme(self, theme):
        ctk.set_default_color_theme(theme)

    def _copy_invite_code(self):
        self.clipboard_clear()
        self.clipboard_append(self.invite_code_entry.get())
