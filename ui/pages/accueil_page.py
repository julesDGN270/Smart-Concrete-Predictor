"""Page Accueil : prediction directe (reprend la logique de main_window.py,
adaptee en frame integree au tableau de bord).

Mise en page sur deux colonnes + conteneur defilant, pour que les boutons
Predire/Reinitialiser et la carte resultat restent toujours visibles
quelle que soit la taille de la fenetre."""

import customtkinter as ctk
<<<<<<< HEAD
from tkinter import messagebox
=======
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d
from core.predictor import ConcretePredictor
from core.database import Database


class AccueilPage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.predictor = ConcretePredictor()
        self.db = Database()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            scroll, text="Prediction de la resistance du beton",
            font=("Arial", 22, "bold")
        ).pack(pady=20)

        labels = [
            "Ciment (kg/m3)", "Laitier (kg/m3)", "Cendres volantes (kg/m3)", "Eau (kg/m3)",
            "Superplastifiant (kg/m3)", "Granulats grossiers (kg/m3)", "Granulats fins (kg/m3)", "Age (jours)",
        ]

        form = ctk.CTkFrame(scroll, fg_color="transparent")
        form.pack(pady=10)
        col1 = ctk.CTkFrame(form, fg_color="transparent")
        col1.grid(row=0, column=0, padx=20)
        col2 = ctk.CTkFrame(form, fg_color="transparent")
        col2.grid(row=0, column=1, padx=20)

        self.entries = []
        for i, label in enumerate(labels):
            target_col = col1 if i < 4 else col2
            ctk.CTkLabel(target_col, text=label).pack(pady=(5, 0))
            entry = ctk.CTkEntry(target_col, width=220)
            entry.pack()
            self.entries.append(entry)

        buttons_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        buttons_frame.pack(pady=20)
        ctk.CTkButton(buttons_frame, text="Predire", command=self.predict, width=120).grid(row=0, column=0, padx=10)
        ctk.CTkButton(buttons_frame, text="Reinitialiser", command=self.reset, width=120).grid(row=0, column=1, padx=10)

        result_frame = ctk.CTkFrame(scroll, width=500, height=120)
        result_frame.pack(fill="x", padx=20, pady=20)
        self.result = ctk.CTkLabel(result_frame, text="Resistance : -- MPa", font=("Arial", 22, "bold"))
        self.result.pack(pady=(20, 5))
        self.quality = ctk.CTkLabel(result_frame, text="Qualite : --", font=("Arial", 18))
        self.quality.pack()

    def predict(self):
        try:
            values = [float(entry.get()) for entry in self.entries]
<<<<<<< HEAD
        except ValueError:
            self.result.configure(text="Veuillez entrer uniquement des nombres.")
            self.quality.configure(text="")
            return

        try:
            prediction = self.predictor.predict(values)
            self.app.last_prediction_values = values
            self.app.last_prediction = prediction
=======
            prediction = self.predictor.predict(values)
            self.app.last_prediction_values = values
            self.app.last_prediction = prediction
            self.db.insert(values, prediction)
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d

            if prediction >= 50:
                quality = "Excellente"
            elif prediction >= 40:
                quality = "Bonne"
            elif prediction >= 30:
                quality = "Moyenne"
            else:
                quality = "Faible"

            self.result.configure(text=f"Resistance : {prediction:.2f} MPa")
            self.quality.configure(text=f"Qualite : {quality}")
            self.app.set_status(f"Derniere prediction : {prediction:.2f} MPa")
<<<<<<< HEAD

            self.db.insert(
                values, prediction,
                user_id=self.app.current_user["id"],
                company_id=self.app.current_user.get("company_id"),
            )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"La prediction a echoue ou n'a pas pu etre enregistree dans l'historique :\n{e}"
            )
=======
        except ValueError:
            self.result.configure(text="Veuillez entrer uniquement des nombres.")
            self.quality.configure(text="")
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d

    def reset(self):
        for entry in self.entries:
            entry.delete(0, "end")
        self.result.configure(text="Resistance : -- MPa")
        self.quality.configure(text="Qualite : --")
