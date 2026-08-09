import joblib

class ConcretePredictor:

    def __init__(self):
        self.model = joblib.load("best_concrete_model.pkl")

    def predict(self, values):
        return self.model.predict([values])[0]
