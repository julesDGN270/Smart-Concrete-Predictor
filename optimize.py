from catboost import CatBoostRegressor
from sklearn.metrics import r2_score
import pandas as pd
from sklearn.model_selection import train_test_split
from catboost import CatBoostRegressor

df = pd.read_csv("Concrete_Data.csv")
X = df.drop("concrete_compressive_strength", axis=1)
y = df["concrete_compressive_strength"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

meilleur_score = -1
meilleur_modele = None
meilleur_parametres = None

iterations_list = [500, 1000, 1500]
depth_list = [4, 5, 6, 7, 8]
learning_rate_list = [0.01, 0.03, 0.05]
l2_leaf_reg_list = [1, 3, 5, 10]

for iterations in iterations_list:
    for depth in depth_list:
        for learning_rate in learning_rate_list:
            for l2_leaf_reg in l2_leaf_reg_list:
                model = CatBoostRegressor(
                    iterations=iterations,
                    depth=depth,
                    learning_rate=learning_rate,
                    l2_leaf_reg=l2_leaf_reg,
                    loss_function="RMSE",
                    verbose=0,
                    random_state=42,
                )
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                score = r2_score(y_test, y_pred)
                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_modele = model
                    meilleur_parametres = {
                        "iterations": iterations,
                        "depth": depth,
                        "learning_rate": learning_rate,
                        "l2_leaf_reg": l2_leaf_reg,
                    }

print("Meilleur R² : ", meilleur_score)
print("meilleur paramètres : ", meilleur_parametres)
