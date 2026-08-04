import pandas as pd

df = pd.read_csv("Concrete_Data.csv")
print(df.head())
print("Dimensions : ", df.shape)
print("Informations : ", df.info())
print("Statistiques : ", df.describe())
print("Valeurs manquantes     ", df.isnull().sum())
