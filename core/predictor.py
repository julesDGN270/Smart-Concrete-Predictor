<<<<<<< HEAD
import joblib

class ConcretePredictor:

    def __init__(self):
        self.model = joblib.load("best_concrete_model.pkl")
=======
import sys
import os
import joblib


def resource_path(relative_path):
    """
    Resout un chemin de ressource qu'on soit en execution normale
    (python app_v2.py) ou dans un executable PyInstaller (--onefile),
    ou les fichiers sont extraits dans un dossier temporaire
    (sys._MEIPASS) different du repertoire courant.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class ConcretePredictor:

    def __init__(self):
        self.model = joblib.load(resource_path("best_concrete_model.pkl"))
>>>>>>> 1280d27de547dbc305e9f55dee04900c72692f4d

    def predict(self, values):
        return self.model.predict([values])[0]
