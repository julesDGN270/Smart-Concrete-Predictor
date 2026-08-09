class ConcreteConstraints:

    def __init__(self):

        self.min_cement = 250
        self.max_cement = 550

        self.min_water = 120
        self.max_water = 220

        self.min_superplasticizer = 0
        self.max_superplasticizer = 30

        self.min_age = 1
        self.max_age = 365

        self.min_w_c = 0.30
        self.max_w_c = 0.65

    def validate(self, mix):

        cement = mix[0]
        slag = mix[1]
        fly_ash = mix[2]
        water = mix[3]
        superplasticizer = mix[4]
        coarse = mix[5]
        fine = mix[6]
        age = mix[7]

        errors = []

        if not self.min_cement <= cement <= self.max_cement:
            errors.append(f"Ciment hors limites ({cement:.1f} kg/m³)")

        if not self.min_water <= water <= self.max_water:
            errors.append(f"Eau hors limites ({water:.1f} kg/m³)")

        if not self.min_superplasticizer <= superplasticizer <= self.max_superplasticizer:
            errors.append("Superplastifiant hors limites")

        if not self.min_age <= age <= self.max_age:
            errors.append("Âge invalide")

        ratio = water / cement

        if not self.min_w_c <= ratio <= self.max_w_c:
            errors.append(f"Rapport Eau/Ciment = {ratio:.2f}")

        if coarse <= 0:
            errors.append("Granulats grossiers invalides")

        if fine <= 0:
            errors.append("Granulats fins invalides")

        return len(errors) == 0, errors