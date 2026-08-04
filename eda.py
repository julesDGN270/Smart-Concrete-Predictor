import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("Concrete_Data.csv")
print(df.columns)

plt.figure(figsize=(8, 5))
sns.histplot(df["concrete_compressive_strength"], bins=30, kde=True)
plt.title("Distribution de la resistance du beton")
plt.xlabel("Resistance(MPa)")
plt.ylabel("Nombre d'echantillons")
plt.show()

df.hist(figsize=(12, 10), bins=30)
plt.suptitle("Distribution des variables du beton")
plt.show()

plt.figure(figsize=(10, 8))
correlation = df.corr()
sns.heatmap(correlation, annot=True, cmap="coolwarm")
plt.title("Matrice de correlation")
plt.show()

plt.figure(figsize=(7, 5))
sns.scatterplot(data=df, x="cement", y="concrete_compressive_strength")
plt.title("Influence du ciment sur la resistance")
plt.xlabel("Ciment (kg/m^3)")
plt.ylabel("Resistance (MPa)")
plt.show()
