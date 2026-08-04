import tkinter as tk
from tkinter import messagebox
import joblib


model = joblib.load("best_concrete_model.pkl")


def predict_strength():
    try:
        values = [
            float(cement.get()),
            float(slag.get()),
            float(flyash.get()),
            float(water.get()),
            float(superplasticizer.get()),
            float(coarse.get()),
            float(fine.get()),
            float(age.get()),
        ]
        prediction = model.predict([values])[0]
        result.config(
            text=f"Résistance estimée : {prediction:.2f} MPa", fg="blue"
            )    
    except ValueError:
        messagebox.showerror(
            "Erreur", "Veuillez saisir uniquement des nombres"
            )


root = tk.Tk()
root.title("Smart Concrete Predictor")
root.geometry("500x600")


def create_field(text):
    tk.Label(root, text=text).pack()
    entry = tk.Entry(root)
    entry.pack(pady=3)
    return entry


cement = create_field("Ciment (kg/m^3)")
slag = create_field("Laitier (kg/m^3)")
flyash = create_field("Cendres volantes (kg/m^3)")
water = create_field("Eau (kg/m^3)")
superplasticizer = create_field("Superplasticifiants (kg/m^3)")
coarse = create_field("Granulats fins (kg/m^3)")
fine = create_field("Granulats fins (kg/m^3)")
age = create_field("Âge (jours)")

tk.Button(
    root, text="Prédire", command=predict_strength, bg="green", fg="white"
    ).pack(pady=15)

result = tk.Label(root, text="", font=("Arial", 14))
result.pack()

root.mainloop()