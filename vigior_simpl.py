import streamlit as st

st.title("VIGIOR Simplifié - Prédiction de risque de complications")

st.write("Saisissez les paramètres cliniques pour estimer le risque de syndrome de loges ou d'infection.")

# Paramètres simplifiés inspirés des données cliniques
fracture_type = st.selectbox("Type de fracture", ["Fracture simple", "Fracture complexe", "Fracture ouverte"])
temps_entre_blessure_et_chirurgie = st.slider("Temps entre blessure et chirurgie (heures)", 0, 72, 24)
presence_edeme = st.radio("Présence d'œdème important ?", ["Non", "Oui"])
mobilite_membre = st.radio("Mobilité du membre affecté", ["Normale", "Limitée", "Immobile"])
douleur_intense = st.radio("Douleur intense hors norme ?", ["Non", "Oui"])
temperature_locale = st.radio("Température locale élevée ?", ["Non", "Oui"])

# Calcul de risque simplifié (coefficients fictifs inspirés de la littérature)
score = 0
if fracture_type == "Fracture complexe":
    score += 3
elif fracture_type == "Fracture ouverte":
    score += 5
else:
    score += 1

if temps_entre_blessure_et_chirurgie > 24:
    score += 2
elif temps_entre_blessure_et_chirurgie > 12:
    score += 1

if presence_edeme == "Oui":
    score += 2
if mobilite_membre == "Limitée":
    score += 1
elif mobilite_membre == "Immobile":
    score += 3
if douleur_intense == "Oui":
    score += 2
if temperature_locale == "Oui":
    score += 2

# Calcul risque en pourcentage (max score = 15)
risque = min(score / 15, 1.0)

st.write(f"### Score de risque : {score} / 15")
st.write(f"### Risque estimé : {risque*100:.1f}%")

if risque > 0.5:
    st.warning("⚠️ Risque élevé de complication. Surveillance rapprochée recommandée.")
else:
    st.success("Risque faible. Suivi standard conseillé.")

# Génération du rapport
if st.button("Générer rapport"):
    rapport = f"""
    Rapport VIGIOR Simplifié
    
    Type de fracture : {fracture_type}
    Temps entre blessure et chirurgie : {temps_entre_blessure_et_chirurgie} heures
    Présence d'œdème important : {presence_edeme}
    Mobilité du membre : {mobilite_membre}
    Douleur intense : {douleur_intense}
    Température locale élevée : {temperature_locale}
    
    Score de risque : {score} / 15
    Risque estimé : {risque*100:.1f}%
    
    Recommandation : {"Surveillance rapprochée recommandée" if risque > 0.5 else "Suivi standard conseillé"}
    """
    st.text_area("Rapport généré", rapport, height=250)
