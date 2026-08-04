import csv
import os
from datetime import datetime


class HistoryManager:

    def __init__(self):

        self.file = "history/predictions.csv"

        os.makedirs("history", exist_ok=True)

        if not os.path.exists(self.file):

            with open(self.file, "w", newline="", encoding="utf-8") as f:

                writer = csv.writer(f)

                writer.writerow([
                    "Date",
                    "Cement",
                    "Slag",
                    "Fly Ash",
                    "Water",
                    "Superplasticizer",
                    "Coarse Aggregate",
                    "Fine Aggregate",
                    "Age",
                    "Prediction"
                ])

    def save(self, values, prediction):

        with open(self.file, "a", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            writer.writerow([
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                *values,
                round(prediction, 2)
            ])
