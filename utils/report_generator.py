import os
from datetime import datetime

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)


class ReportGenerator:

    def __init__(self):
        os.makedirs("reports", exist_ok=True)

    def generate(self, values, prediction):

        filename = datetime.now().strftime(
            "reports/Rapport_%Y%m%d_%H%M%S.pdf"
        )

        pdf = SimpleDocTemplate(filename)

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                "<b>SMART CONCRETE PREDICTOR</b>",
                styles["Title"]
            )
        )

        elements.append(Spacer(1, 20))

        labels = [
            "Ciment",
            "Laitier",
            "Cendres volantes",
            "Eau",
            "Superplastifiant",
            "Granulats grossiers",
            "Granulats fins",
            "Âge"
        ]

        for label, value in zip(labels, values):

            elements.append(
                Paragraph(
                    f"<b>{label} :</b> {value}",
                    styles["BodyText"]
                )
            )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"<b>Résistance prédite :</b> {prediction:.2f} MPa",
                styles["Heading2"]
            )
        )

        if prediction >= 50:
            quality = "Excellente"
        elif prediction >= 40:
            quality = "Bonne"
        elif prediction >= 30:
            quality = "Moyenne"
        else:
            quality = "Faible"

        elements.append(
            Paragraph(
                f"<b>Qualité :</b> {quality}",
                styles["Heading2"]
            )
        )

        pdf.build(elements)

        return filename