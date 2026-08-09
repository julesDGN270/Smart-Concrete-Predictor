"""Page Analyse (frame integree, logique reprise de ui/analysis_window.py)."""

import customtkinter as ctk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from core.database import Database

COLUMNS = [
    "ID", "Date", "Cement", "Slag", "Fly Ash", "Water",
    "Superplasticizer", "Coarse Aggregate", "Fine Aggregate",
    "Age", "Prediction", "Source",
]


class AnalysePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.db = Database()
        self._built = False
        self._canvas_widget = None

    def refresh(self):
        """Reconstruit le contenu a chaque affichage (donnees a jour)."""
        for widget in self.winfo_children():
            widget.destroy()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")

<<<<<<< HEAD
        rows = self.db.get_all(
            user_id=self.app.current_user["id"],
            company_id=self.app.current_user.get("company_id"),
        )
=======
        rows = self.db.get_all()
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d
        df = pd.DataFrame(rows, columns=COLUMNS)

        ctk.CTkLabel(scroll, text="Analyse des predictions", font=("Arial", 24, "bold")).pack(pady=15)

        if df.empty:
            ctk.CTkLabel(scroll, text="Aucune prediction enregistree pour le moment.", font=("Arial", 16)).pack(pady=40)
            return

        fig, axs = plt.subplots(2, 2, figsize=(11, 6))
        axs[0, 0].plot(df["Prediction"], marker="o")
        axs[0, 0].set_title("Evolution des resistances")
        axs[0, 0].set_ylabel("MPa")

        axs[0, 1].hist(df["Prediction"], bins=10)
        axs[0, 1].set_title("Distribution des resistances")
        axs[0, 1].set_xlabel("MPa")

        quality = []
        for p in df["Prediction"]:
            if p >= 50:
                quality.append("Excellente")
            elif p >= 40:
                quality.append("Bonne")
            elif p >= 30:
                quality.append("Moyenne")
            else:
                quality.append("Faible")
        pd.Series(quality).value_counts().plot(kind="pie", autopct="%1.1f%%", ax=axs[1, 0])
        axs[1, 0].set_ylabel("")
        axs[1, 0].set_title("Qualite du beton")

        axs[1, 1].boxplot(df["Prediction"])
        axs[1, 1].set_title("Boite a moustaches")
        axs[1, 1].set_ylabel("MPa")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=scroll)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

        stats_frame = ctk.CTkFrame(scroll)
        stats_frame.pack(fill="x", padx=20, pady=10)

        total = len(df)
        moyenne = df["Prediction"].mean()
        mediane = df["Prediction"].median()
        minimum = df["Prediction"].min()
        maximum = df["Prediction"].max()
        ecart_type = df["Prediction"].std()

        texte = (
            f"Nombre de predictions : {total}\n"
            f"Resistance moyenne : {moyenne:.2f} MPa\n"
            f"Mediane : {mediane:.2f} MPa\n"
            f"Ecart-type : {ecart_type:.2f} MPa\n"
            f"Minimum : {minimum:.2f} MPa\n"
            f"Maximum : {maximum:.2f} MPa"
        )
        ctk.CTkLabel(stats_frame, text=texte, justify="left", font=("Arial", 14)).pack(anchor="w", padx=15, pady=15)
