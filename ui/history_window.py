import customtkinter as ctk
from tkinter import ttk
import pandas as pd
from tkinter import messagebox
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from core.database import Database
import matplotlib.pyplot as plt
import numpy as np


class HistoryWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Historique des prédictions")
        self.geometry("1200x650")

        self.df = None
        self.db = Database()

        # =========================
        # Titre
        # =========================

        title = ctk.CTkLabel(
            self, text="Historique des prédictions", font=("Arial", 24, "bold")
        )

        title.pack(pady=15)

        # =========================
        # Barre de recherche
        # =========================

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=20)

        self.search_entry = ctk.CTkEntry(
            top_frame, width=300, placeholder_text="Rechercher..."
        )

        self.search_entry.pack(side="left", padx=10, pady=10)

        search_btn = ctk.CTkButton(
            top_frame, text="Rechercher", command=self.search
            )

        search_btn.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(
            top_frame, text="Actualiser", command=self.load_data
        )

        refresh_btn.pack(side="left", padx=5)

        delete_btn = ctk.CTkButton(
            top_frame,
            text="Supprimer",
            fg_color="red",
            hover_color="#AA0000",
            command=self.delete_selected,
        )
        delete_btn.pack(side="left", padx=5)

        excel_btn = ctk.CTkButton(
            top_frame, text="Exporter Excel", command=self.export_excel
        )
        excel_btn.pack(side="left", padx=5)

        pdf_btn = ctk.CTkButton(
            top_frame, text="Exporter PDF", command=self.export_pdf
            )
        pdf_btn.pack(side="left", padx=5)

        graph_btn = ctk.CTkButton(
            top_frame, text="Graphiques", command=self.show_graph
            )
        graph_btn.pack(side="left", padx=5)
        
        stats_btn = ctk.CTkButton(
            top_frame,
            text="Statistiques",
            command=self.show_statistics
        )
        stats_btn.pack(side="left", padx=5)
        
        hist_btn = ctk.CTkButton(
            top_frame,
            text="Histogramme",
            command=self.show_histogram
        )
        hist_btn.pack(side="left", padx=5)

        # =========================
        # Tableau
        # =========================

        self.tree = ttk.Treeview(self)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # =========================
        # Statistiques
        # =========================

        self.stats = ctk.CTkLabel(self, text="", font=("Arial", 16))

        self.stats.pack(pady=10)

        self.load_data()

    # =============================

    def load_data(self):

        rows = self.db.get_all()

        columns = [
            "ID",
            "Date",
            "Cement",
            "Slag",
            "Fly Ash",
            "Water",
            "Superplasticizer",
            "Coarse Aggregate",
            "Fine Aggregate",
            "Age",
            "Prediction",
            "Source"
        ]

        self.df = pd.DataFrame(rows, columns=columns)

        self.show_dataframe(self.df)
    # =============================

    def show_dataframe(self, dataframe):

        self.tree.delete(*self.tree.get_children())

        self.tree["columns"] = list(dataframe.columns)

        self.tree["show"] = "headings"

        for col in dataframe.columns:

            self.tree.heading(col, text=col)

            self.tree.column(col, width=110, anchor="center")

        for row in dataframe.values:

            self.tree.insert("", "end", values=list(row))

        moyenne = dataframe["Prediction"].mean()

        maximum = dataframe["Prediction"].max()

        minimum = dataframe["Prediction"].min()

        total = len(dataframe)

        self.stats.configure(
            text=(
                f"Nombre : {total}      "
                f"Moyenne : {moyenne:.2f} MPa      "
                f"Max : {maximum:.2f} MPa      "
                f"Min : {minimum:.2f} MPa"
            )
        )

    # =============================

    def search(self):

        text = self.search_entry.get().lower()

        if text == "":

            self.show_dataframe(self.df)

            return

        result = self.df[
            self.df.astype(str)
            .apply(lambda x: x.str.lower())
            .apply(lambda x: x.str.contains(text))
            .any(axis=1)
        ]

        self.show_dataframe(result)

    def delete_selected(self):

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(selected[0])["values"]

        # Fenêtre de confirmation
        confirm = messagebox.askyesno(
            "Confirmation", "Voulez-vous vraiment supprimer cette prédiction ?"
        )

        # Si l'utilisateur clique sur Non
        if not confirm:
            return

        record_id = values[0]

        self.db.delete(record_id)

        self.load_data()

        messagebox.showinfo(
            "Suppression",
            "La prédiction a été supprimée avec succès."
        )

        # Message de succès
        messagebox.showinfo("Suppression", "La prédiction a été supprimée avec succès.")

    def export_excel(self):
        self.df.to_excel("history/historique_predictions.xlsx", index=False)

    def export_pdf(self):

        file_path = "history/rapport_predictions.pdf"

        doc = SimpleDocTemplate(file_path, pagesize=A4)

        elements = []

        styles = getSampleStyleSheet()

        title = Paragraph(
            "Rapport des prédictions de résistance du béton", styles["Title"]
        )

        elements.append(title)
        elements.append(Spacer(1, 20))

        data = [list(self.df.columns)]

        for row in self.df.values.tolist():
            data.append(row)

        table = Table(data)

        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, None),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )

        elements.append(table)

        doc.build(elements)
        
    def show_graph(self):

        if self.df.empty:
            return

        plt.figure(figsize=(8, 4))

        plt.plot(
            self.df["Date"],
            self.df["Prediction"],
            marker="o"
        )

        plt.title(
            "Évolution de la résistance du béton"
        )

        plt.xlabel("Date")

        plt.ylabel(
            "Résistance (MPa)"
        )

        plt.xticks(
            rotation=45
        )

        plt.tight_layout()

        plt.show()
        
    def show_statistics(self):

        if self.df.empty:
            return

        values = self.df["Prediction"].astype(float)


        moyenne = values.mean()

        maximum = values.max()

        minimum = values.min()

        ecart_type = values.std()


        print("===== Statistiques Béton =====")
        print(f"Moyenne : {moyenne:.2f} MPa")
        print(f"Maximum : {maximum:.2f} MPa")
        print(f"Minimum : {minimum:.2f} MPa")
        print(f"Écart-type : {ecart_type:.2f} MPa")

    def show_histogram(self):

        if self.df.empty:
            return

        values = self.df["Prediction"].astype(float)


        plt.figure(figsize=(7,4))

        plt.hist(
            values,
            bins=10
        )

        plt.title(
            "Distribution des résistances du béton"
        )

        plt.xlabel(
            "Résistance (MPa)"
        )

        plt.ylabel(
            "Nombre de prédictions"
        )


        plt.grid(True)

        plt.show()