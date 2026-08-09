import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

df = pd.read_csv("Concrete_Data.csv")
X = df.drop("concrete_compressive_strength", axis=1)
y = df["concrete_compressive_strength"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

models = {
    "Regression lineaire": LinearRegression(),
    "Arbre de décision": DecisionTreeRegressor(),
    "Forêt aléatoire": RandomForestRegressor(n_estimators=500, random_state=42
                                             ),
    "Gragient Boosting": GradientBoostingRegressor(
        n_estimators=500, learning_rate=0.03, random_state=42
    ),
    "XGBoost": XGBRegressor(
        n_estimators=1000, learning_rate=0.02, random_state=42
        ),
    "LightGBM": LGBMRegressor(
        n_estimators=1000, learning_rate=0.02, random_state=42
        ),
    "CatBoost": CatBoostRegressor(
        iterations=1000, learning_rate=0.03, verbose=0, random_state=42
    )
}
print("=" * 60)
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    print(f"MAE : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")
    print(f"R² : {r2:.4f}")
