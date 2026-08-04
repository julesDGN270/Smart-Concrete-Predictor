import customtkinter as ctk
from core.predictor import ConcretePredictor
from core.database import Database
from ui.history_window import HistoryWindow
from ui.analysis_window import AnalysisWindow
from utils.report_generator import ReportGenerator
from ui.settings_window import SettingsWindow
from tkinter import messagebox
from core.optimizer import ConcreteOptimizer


# Configuration de CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Modèle IA
        self.predictor = ConcretePredictor()
        self.db = Database()
        self.report = ReportGenerator()
        self.optimizer = ConcreteOptimizer(self.predictor)

        # Fenêtre
        self.title("Smart Concrete Predictor")
        self.geometry("1000x650")
        self.resizable(False, False)

        # =============================
        # Layout principal
        # =============================

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =============================
        # Barre latérale
        # =============================

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)

        self.sidebar.grid(row=0, column=0, sticky="ns")

        title = ctk.CTkLabel(
            self.sidebar, text="SMART\nCONCRETE\nPREDICTOR", font=("Arial", 24, "bold")
        )

        title.pack(pady=30)

        menu = [
            ("🏠 Accueil", None),
            ("📊 Analyse", self.open_analysis),
            ("📜 Historique", self.open_history),
            ("📄 Rapport", self.generate_report),
            ("⚙ Paramètres", self.open_settings),
        ]

        for text, command in menu:
            btn = ctk.CTkButton(self.sidebar, text=text, width=180, command=command)
            btn.pack(pady=8)

        self.main = ctk.CTkFrame(self)

        self.main.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        titre = ctk.CTkLabel(
            self.main,
            text="Prédiction de la résistance du béton",
            font=("Arial", 22, "bold"),
        )

        titre.pack(pady=20)

        labels = [
            "Ciment (kg/m³)",
            "Laitier (kg/m³)",
            "Cendres volantes (kg/m³)",
            "Eau (kg/m³)",
            "Superplastifiant (kg/m³)",
            "Granulats grossiers (kg/m³)",
            "Granulats fins (kg/m³)",
            "Âge (jours)",
        ]

        self.entries = []

        for label in labels:

            ctk.CTkLabel(self.main, text=label).pack(pady=(5, 0))

            entry = ctk.CTkEntry(self.main, width=250)

            entry.pack()

            self.entries.append(entry)

        buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")

        buttons_frame.pack(pady=20)

        predict_btn = ctk.CTkButton(
            buttons_frame, text="Prédire", command=self.predict, width=120
        )

        predict_btn.grid(row=0, column=0, padx=10)

        reset_btn = ctk.CTkButton(
            buttons_frame, text="Réinitialiser", command=self.reset, width=120
        )

        reset_btn.grid(row=0, column=1, padx=10)

        # =============================
        # Carte Résultat
        # =============================

        result_frame = ctk.CTkFrame(self.main, width=500, height=120)

        result_frame.pack(fill="x", padx=20, pady=20)

        self.result = ctk.CTkLabel(
            result_frame, text="Résistance : -- MPa", font=("Arial", 22, "bold")
        )

        self.result.pack(pady=(20, 5))

        self.quality = ctk.CTkLabel(
            result_frame, text="Qualité : --", font=("Arial", 18)
        )

        self.quality.pack()
        

    # ==========================================
    # Fonction de prédiction
    # ==========================================

    def predict(self):

        try:

            values = [float(entry.get()) for entry in self.entries]

            prediction = self.predictor.predict(values)
            self.last_values = values
            self.last_prediction = prediction
            self.db.insert(values, prediction)

            if prediction >= 50:
                quality = "⭐⭐⭐⭐⭐ Excellente"

            elif prediction >= 40:
                quality = "⭐⭐⭐⭐ Bonne"

            elif prediction >= 30:
                quality = "⭐⭐⭐ Moyenne"

            else:
                quality = "⭐⭐ Faible"

            self.result.configure(text=f"Résistance : {prediction:.2f} MPa")

            self.quality.configure(text=f"Qualité : {quality}")

        except ValueError:

            self.result.configure(text="Veuillez entrer uniquement des nombres.")

            self.quality.configure(text="")

    def reset(self):

        for entry in self.entries:
            entry.delete(0, "end")

        self.result.configure(text="Résistance : -- MPa")

        self.quality.configure(text="Qualité : --")

    def open_history(self):
        HistoryWindow(self)
        
        
    def open_analysis(self):
        AnalysisWindow(self)
        
    def generate_report(self):

        try:

            if not hasattr(self, "last_prediction"):

                messagebox.showwarning(
                    "Rapport",
                    "Veuillez effectuer une prédiction avant de générer un rapport."
                )

                return

            filename = self.report.generate(
                self.last_values,
                self.last_prediction
            )

            messagebox.showinfo(
                "Rapport",
                f"Rapport généré avec succès !\n\n{filename}"
            )

        except Exception as e:

            messagebox.showerror(
                "Erreur",
                str(e)
            )
            
    def open_settings(self):
        SettingsWindow(self)
