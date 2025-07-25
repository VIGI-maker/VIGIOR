# app.py

import streamlit as st
import joblib
import numpy as np

# Charger le modèle
model = joblib.load("model_loges.pkl")

# Titre de l'app
st.title("🧠 VIGIOR — Prédiction du syndrome de loges")

st.write("Remplissez les informations du patient pour estimer le risque de syndrome de loges après fracture du plateau tibial.")

# Interface utilisateur
age = st.slider("Âge", 10, 90, 35)
sexe = st.radio("Sexe", ["H", "F"])
energie = st.radio("Type de traumatisme", ["haute", "basse"])
pression_diast = st.slider("Pression diastolique", 40, 120, 80)
fracture_type = st.selectbox("Type de fracture", ["Schatzker I", "II", "III", "IV", "V", "VI"])
nb_fragments = st.slider("Nombre de fragments osseux", 1, 10, 3)
largeur = st.slider("Largeur de l’hématome (en mm)", 0, 100, 25)
ratio_muscle_graisse = st.slider("Ratio muscle/graisse", 0.1, 5.0, 1.5)

# Convertir les inputs
sexe_val = 1 if sexe == "H" else 0
energie_val = 1 if energie == "haute" else 0
fracture_code = {"Schatzker I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5}[fracture_type]

# Créer un tableau pour le modèle
X_input = np.array([[age, sexe_val, energie_val, pression_diast, fracture_code, nb_fragments, largeur, ratio_muscle_graisse]])

# Prédire
if st.button("📊 Estimer le risque"):
    prediction = model.predict_proba(X_input)[0][1]  # proba de classe 1 = SdL
    pourcentage = round(prediction * 100, 2)
    st.success(f"🩺 Risque estimé de syndrome de loges : **{pourcentage}%**")

    if pourcentage > 50:
        st.warning("⚠️ Risque élevé — surveillance clinique renforcée recommandée.")
    else:
        st.info("✅ Risque faible — continuer la surveillance standard.")

