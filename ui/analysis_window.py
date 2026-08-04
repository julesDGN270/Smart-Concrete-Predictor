import customtkinter as ctk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from core.database import Database


class AnalysisWindow(ctk.CTkToplevel):

    COLUMNS = [
        "ID", "Date", "Cement", "Slag", "Fly Ash", "Water",
        "Superplasticizer", "Coarse Aggregate", "Fine Aggregate",
        "Age", "Prediction", "Source"
    ]

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Analyse des prédictions")
        self.geometry("1100x700")

        self.db = Database()
        rows = self.db.get_all()
        self.df = pd.DataFrame(rows, columns=self.COLUMNS)

        title = ctk.CTkLabel(
            self,
            text="Analyse des prédictions",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=15)

        if self.df.empty:
            ctk.CTkLabel(
                self,
                text="Aucune prédiction enregistrée pour le moment.",
                font=("Arial", 16)
            ).pack(pady=40)
            return

        self.show_graph()
        self.show_statistics()

    def show_graph(self):

        fig, axs = plt.subplots(2, 2, figsize=(12, 8))

        # ========= Graphique 1 =========
        axs[0, 0].plot(
            self.df["Prediction"],
            marker="o"
        )
        axs[0, 0].set_title("Évolution des résistances")
        axs[0, 0].set_ylabel("MPa")

        # ========= Graphique 2 =========
        axs[0, 1].hist(
            self.df["Prediction"],
            bins=10
        )
        axs[0, 1].set_title("Distribution des résistances")
        axs[0, 1].set_xlabel("MPa")

        # ========= Graphique 3 =========
        quality = []

        for p in self.df["Prediction"]:

            if p >= 50:
                quality.append("Excellente")

            elif p >= 40:
                quality.append("Bonne")

            elif p >= 30:
                quality.append("Moyenne")

            else:
                quality.append("Faible")

        pd.Series(quality).value_counts().plot(
            kind="pie",
            autopct="%1.1f%%",
            ax=axs[1, 0]
        )

        axs[1, 0].set_ylabel("")
        axs[1, 0].set_title("Qualité du béton")

        # ========= Graphique 4 =========
        axs[1, 1].boxplot(self.df["Prediction"])
        axs[1, 1].set_title("Boîte à moustaches")
        axs[1, 1].set_ylabel("MPa")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(
            fig,
            master=self
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )
        
    def show_statistics(self):

        stats_frame = ctk.CTkFrame(self)

        stats_frame.pack(fill="x", padx=20, pady=10)

        total = len(self.df)
        moyenne = self.df["Prediction"].mean()
        mediane = self.df["Prediction"].median()
        minimum = self.df["Prediction"].min()
        maximum = self.df["Prediction"].max()
        ecart_type = self.df["Prediction"].std()

        texte = (
            f"Nombre de prédictions : {total}\n"
            f"Résistance moyenne : {moyenne:.2f} MPa\n"
            f"Médiane : {mediane:.2f} MPa\n"
            f"Écart-type : {ecart_type:.2f} MPa\n"
            f"Minimum : {minimum:.2f} MPa\n"
            f"Maximum : {maximum:.2f} MPa"
        )

        label = ctk.CTkLabel(
            stats_frame,
            text=texte,
            justify="left",
            font=("Arial", 15)
        )

        label.pack(anchor="w", padx=15, pady=15)