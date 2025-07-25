# train_model_loges.py

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Charger les données
df = pd.read_csv("vigior_base_donnees.csv")

# Encodage simple des variables catégorielles
df["sexe"] = df["sexe"].map({"H": 1, "F": 0})
df["energie"] = df["energie"].map({"haute": 1, "basse": 0})
df["fracture_type"] = df["fracture_type"].astype('category').cat.codes

# Définir les variables
X = df.drop("SdL", axis=1)
y = df["SdL"]

# Séparer en jeu d'entraînement et test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraîner le modèle
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Sauvegarder le modèle
joblib.dump(model, "model_loges.pkl")
print("✅ Modèle entraîné et sauvegardé dans model_loges.pkl")
