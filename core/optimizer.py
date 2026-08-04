import random
from core.constraints import ConcreteConstraints


class ConcreteOptimizer:

    def __init__(self, predictor):
        self.predictor = predictor
        self.constraints = ConcreteConstraints()

    def optimize(self, target_strength, n_trials=5000):

        best_mix = None
        best_prediction = None
        best_error = float("inf")

        for _ in range(n_trials):

            mix = [
                random.uniform(250, 550),    # Cement
                random.uniform(0, 250),      # Slag
                random.uniform(0, 200),      # Fly Ash
                random.uniform(120, 220),    # Water
                random.uniform(0, 25),       # Superplasticizer
                random.uniform(800, 1200),   # Coarse Aggregate
                random.uniform(600, 1000),   # Fine Aggregate
                random.randint(1, 365)       # Age
            ]

            valid, errors = self.constraints.validate(mix)

            if not valid:
                continue

            prediction = self.predictor.predict(mix)

            error = abs(prediction - target_strength)

            if error < best_error:
                best_error = error
                best_mix = mix
                best_prediction = prediction

        return best_mix, best_prediction, best_error