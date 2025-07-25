import streamlit as st

st.title("VIGIOR Simplifié - Prédiction du risque de syndrome de loge")

st.write("Entrez les paramètres pour estimer le risque et la prise en charge adaptée.")

# Paramètres
age = st.number_input("Âge du patient (années)", min_value=0, max_value=120, value=30)
sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
schatzker = st.selectbox("Classification de Schatzker", [1, 2, 3, 4, 5, 6])
n_fragments = st.number_input("Nombre de fragments osseux", min_value=1, max_value=10, value=3)
largeur_fracture_mm = st.number_input("Largeur de la fracture (mm)", min_value=1.0, max_value=100.0, value=15.0)
ratio_muscle_graisse = st.slider("Ratio muscle/graisse (%)", 0, 100, 60)

# Calcul de risque (formule fictive simplifiée inspirée des études)
score = 0

# Age
if age < 30:
    score += 1
elif age < 60:
    score += 2
else:
    score += 3

# Sexe
if sexe == "Masculin":
    score += 2
else:
    score += 1

# Schatzker
score += schatzker  # Plus élevé = plus risqué

# Nombre de fragments
if n_fragments <= 3:
    score += 1
elif n_fragments <= 6:
    score += 2
else:
    score += 3

# Largeur fracture
if largeur_fracture_mm < 10:
    score += 1
elif largeur_fracture_mm < 30:
    score += 2
else:
    score += 3

# Ratio muscle/graisse
if ratio_muscle_graisse > 70:
    score += 1
elif ratio_muscle_graisse > 40:
    score += 2
else:
    score += 3

# Normalisation du score max possible = 17
risque = min(score / 17, 1.0)

st.write(f"### Score de risque : {score} / 17")
st.write(f"### Risque estimé de syndrome de loge : {risque*100:.1f}%")

# Proposition de prise en charge
if risque < 0.3:
    prise_en_charge = "Surveillance simple avec contrôle clinique régulier."
elif risque < 0.6:
    prise_en_charge = "Fixateur externe recommandé avec surveillance renforcée."
else:
    prise_en_charge = "Fasciotomie urgente indiquée, prise en charge chirurgicale prioritaire."

st.write(f"### Prise en charge recommandée :")
st.info(prise_en_charge)

# Génération rapport
if st.button("Générer rapport"):
    rapport = f"""
    Rapport VIGIOR Simplifié
    
    Âge : {age} ans
    Sexe : {sexe}
    Classification de Schatzker : {schatzker}
    Nombre de fragments osseux : {n_fragments}
    Largeur fracture : {largeur_fracture_mm} mm
    Ratio muscle/graisse : {ratio_muscle_graisse}%
    
    Score de risque : {score} / 17
    Risque estimé : {risque*100:.1f}%
    
    Prise en charge recommandée : {prise_en_charge}
    """
    st.text_area("Rapport généré", rapport, height=300)
