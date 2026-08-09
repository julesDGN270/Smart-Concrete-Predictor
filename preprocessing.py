import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("Concrete_Data.csv")
X = df.drop("concrete_compressive_strength", axis=1)
y = df["concrete_compressive_strength"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print("Jeu d'entrainement : ", X_train.shape)
print("Jeu de test : ", X_test.shape)
print("Taille de y_train : ", y_train.shape)
print("Taille de y_test : ", y_test.shape)
