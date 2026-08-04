"""Page Parametres (frame integree, logique reprise de ui/settings_window.py)."""

import customtkinter as ctk


class ParametresPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        ctk.CTkLabel(self, text="Parametres", font=("Arial", 24, "bold")).pack(pady=20)

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
