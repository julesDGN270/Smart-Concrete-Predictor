"""Page Historique (frame integree, logique reprise de ui/history_window.py)."""

import customtkinter as ctk
from tkinter import ttk, messagebox
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from core.database import Database
import matplotlib.pyplot as plt

COLUMNS = [
    "ID", "Date", "Cement", "Slag", "Fly Ash", "Water",
    "Superplasticizer", "Coarse Aggregate", "Fine Aggregate",
    "Age", "Prediction", "Source",
]


class HistoriquePage(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.df = None
        self.db = Database()

        ctk.CTkLabel(self, text="Historique des predictions", font=("Arial", 24, "bold")).pack(pady=15)

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=20)

        self.search_entry = ctk.CTkEntry(top_frame, width=300, placeholder_text="Rechercher...")
        self.search_entry.pack(side="left", padx=10, pady=10)

        ctk.CTkButton(top_frame, text="Rechercher", command=self.search).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Actualiser", command=self.load_data).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Supprimer", fg_color="red", hover_color="#AA0000", command=self.delete_selected).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Exporter Excel", command=self.export_excel).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Exporter PDF", command=self.export_pdf).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Graphique", command=self.show_graph).pack(side="left", padx=5)
        ctk.CTkButton(top_frame, text="Histogramme", command=self.show_histogram).pack(side="left", padx=5)

        self.tree = ttk.Treeview(self)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.stats = ctk.CTkLabel(self, text="", font=("Arial", 16))
        self.stats.pack(pady=10)

        self.load_data()

    def load_data(self):
        rows = self.db.get_all()
        self.df = pd.DataFrame(rows, columns=COLUMNS)
        self.show_dataframe(self.df)

    def show_dataframe(self, dataframe):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(dataframe.columns)
        self.tree["show"] = "headings"
        for col in dataframe.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        for row in dataframe.values:
            self.tree.insert("", "end", values=list(row))

        if len(dataframe) == 0:
            self.stats.configure(text="Aucune donnee.")
            return

        moyenne = dataframe["Prediction"].mean()
        maximum = dataframe["Prediction"].max()
        minimum = dataframe["Prediction"].min()
        self.stats.configure(
            text=(
                f"Nombre : {len(dataframe)}      Moyenne : {moyenne:.2f} MPa      "
                f"Max : {maximum:.2f} MPa      Min : {minimum:.2f} MPa"
            )
        )

    def search(self):
        text = self.search_entry.get().lower()
        if text == "":
            self.show_dataframe(self.df)
            return
        result = self.df[
            self.df.astype(str).apply(lambda x: x.str.lower()).apply(lambda x: x.str.contains(text)).any(axis=1)
        ]
        self.show_dataframe(result)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])["values"]
        if not messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cette prediction ?"):
            return
        self.db.delete(values[0])
        self.load_data()
        messagebox.showinfo("Suppression", "La prediction a ete supprimee avec succes.")

    def export_excel(self):
        self.df.to_excel("history/historique_predictions.xlsx", index=False)
        messagebox.showinfo("Export", "Exporte vers history/historique_predictions.xlsx")

    def export_pdf(self):
        file_path = "history/rapport_predictions.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Rapport des predictions de resistance du beton", styles["Title"]), Spacer(1, 20)]
        data = [list(self.df.columns)] + self.df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, None), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        elements.append(table)
        doc.build(elements)
        messagebox.showinfo("Export", f"Exporte vers {file_path}")

    def show_graph(self):
        if self.df is None or self.df.empty:
            return
        plt.figure(figsize=(8, 4))
        plt.plot(self.df["Date"], self.df["Prediction"], marker="o")
        plt.title("Evolution de la resistance du beton")
        plt.xlabel("Date")
        plt.ylabel("Resistance (MPa)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def show_histogram(self):
        if self.df is None or self.df.empty:
            return
        values = self.df["Prediction"].astype(float)
        plt.figure(figsize=(7, 4))
        plt.hist(values, bins=10)
        plt.title("Distribution des resistances du beton")
        plt.xlabel("Resistance (MPa)")
        plt.ylabel("Nombre de predictions")
        plt.grid(True)
        plt.show()
