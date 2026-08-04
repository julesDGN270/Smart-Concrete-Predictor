"""
Tableau de bord Smart Concrete Predictor v2.0
================================================

Ossature principale : barre laterale + zone de contenu dynamique +
barre d'etat, remplacant progressivement l'ancienne fenetre unique
(ui/main_window.py, conservee telle quelle pour compatibilite).
"""

import customtkinter as ctk
from datetime import datetime

from ui.pages.accueil_page import AccueilPage
from ui.pages.formulation_page import FormulationIAPage
from ui.pages.historique_page import HistoriquePage
from ui.pages.analyse_page import AnalysePage
from ui.pages.parametres_page import ParametresPage

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class DashboardApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Smart Concrete Predictor v2.0")
        self.geometry("1150x750")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============== Barre laterale ==============
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(
            self.sidebar, text="SMART\nCONCRETE\nPREDICTOR",
            font=("Arial", 22, "bold")
        ).pack(pady=30)

        self.nav_buttons = {}
        menu = [
            ("accueil", "Accueil"),
            ("analyse", "Analyse"),
            ("historique", "Historique"),
            ("formulation", "Formulation IA"),
            ("parametres", "Parametres"),
        ]
        for key, text in menu:
            btn = ctk.CTkButton(
                self.sidebar, text=text, width=180,
                command=lambda k=key: self.show_page(k)
            )
            btn.pack(pady=8)
            self.nav_buttons[key] = btn

        # ============== Zone de contenu ==============
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.pages["accueil"] = AccueilPage(self.content, self)
        self.pages["formulation"] = FormulationIAPage(self.content, self)
        self.pages["historique"] = HistoriquePage(self.content, self)
        self.pages["analyse"] = AnalysePage(self.content, self)
        self.pages["parametres"] = ParametresPage(self.content, self)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # ============== Barre d'etat ==============
        self.status_bar = ctk.CTkLabel(
            self, text="", anchor="w", font=("Arial", 12),
            fg_color="transparent"
        )
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=5)

        self.set_status("Modele charge OK")
        self.show_page("accueil")

    def show_page(self, key):
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()
        page.tkraise()
        maj = datetime.now().strftime("%d/%m/%Y %H:%M")
        for k, btn in self.nav_buttons.items():
            btn.configure(fg_color=("#3B8ED0" if k == key else "#1F6AA5"))
        self._last_page = key

    def set_status(self, message):
        maj = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.status_bar.configure(text=f"Modele charge OK      |      {message}      |      Derniere MAJ : {maj}")
