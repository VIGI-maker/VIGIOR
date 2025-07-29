import streamlit as st
import pandas as pd
import uuid
import os

st.set_page_config(page_title="VIGIOR-H — Fractures Proximales de l’Humérus", layout="centered")
st.title("🦾 VIGIOR-H — Estimation des Risques et Conduite à Tenir")
st.write("Ce modèle permet d’estimer les risques de complications (nécrose, pseudarthrose, raideur) après fracture proximale de l’humérus, et suggère une stratégie thérapeutique.")

# --- Formulaire principal ---
with st.form("form_vigior_h"):
    age = st.number_input("Âge du patient", 18, 100, step=1)
    sexe = st.selectbox("Sexe", ["Homme", "Femme"])

    tabac = st.selectbox("Tabagisme", ["Non", "Oui"])
    pa = 0
    if tabac == "Oui":
        pa = st.number_input("Pack-years (PA)", 0.0, 100.0, step=0.5)

    diabete = st.selectbox("Diabète", ["Non", "Oui"])
    osteoporose = st.selectbox("Ostéoporose connue", ["Non", "Oui"])
    comorbidites = st.selectbox("Comorbidités majeures", ["Non", "Oui"])

    neer = st.selectbox("Type de fracture selon Neer", ["2 fragments", "3 fragments", "4 fragments"])
    deplacement = st.selectbox("Déplacement inter-fragmentaire ?", ["Non", "Oui"])
    ecart_mm = 0
    if deplacement == "Oui":
        ecart_mm = st.slider("Écart inter-fragmentaire (en mm)", 0, 20, 5)

    hsa = st.slider("Angle cervico-diaphysaire (HSA, en °)", 90, 160, 135)
    dominance = st.selectbox("Fracture du bras dominant", ["Non", "Oui"])
    mobilite = st.selectbox("Mobilité antérieure du patient", ["Normale", "Limitée"])

    traitement = st.selectbox("Traitement envisagé", ["Orthopédique", "Chirurgical"])

    submit = st.form_submit_button("Évaluer")

if submit:
    # --- Score simplifié basé sur les facteurs clés (pondérations arbitraires pour le prototype) ---
    score = 0
    if age > 70: score += 2
    if tabac == "Oui": score += 1 if pa < 20 else 2
    if diabete == "Oui": score += 1
    if osteoporose == "Oui": score += 1
    if comorbidites == "Oui": score += 1
    if neer == "3 fragments": score += 2
    elif neer == "4 fragments": score += 3
    if deplacement == "Oui" and ecart_mm >= 5: score += 2
    if hsa < 120: score += 2
    if mobilite == "Limitée": score += 1

    # Risques estimés (formules à ajuster avec modèle réel)
    risque_necrose = min(100, round(score * 5 + (2 if traitement == "Orthopédique" else -2), 1))
    risque_pseudo = min(100, round(score * 4 + (2 if traitement == "Orthopédique" else 0), 1))
    risque_raideur = min(100, round(score * 3 + (2 if mobilite == "Limitée" else 0), 1))

    # Recommandation
    if score >= 8:
        conduite = "\n- Prothèse céphalomédullaire ou inversée recommandée si âge >70 ans.\n- Réduction anatomique difficile à obtenir."
    elif 5 <= score < 8:
        conduite = "\n- Traitement chirurgical par ostéosynthèse si réduction possible.\n- Surveillance stricte post-opératoire."
    else:
        conduite = "\n- Traitement conservateur acceptable.\n- Bonne récupération fonctionnelle attendue."

    # Résultats
    code_patient = f"VIG-{str(uuid.uuid4())[:8].upper()}"
    st.success(f"🧠 Score global : {score}/15")
    st.info(f"📉 Risque de nécrose : {risque_necrose} %")
    st.info(f"🦴 Risque de pseudarthrose : {risque_pseudo} %")
    st.info(f"🤕 Risque de raideur : {risque_raideur} %")
    st.warning(f"🩺 Conduite suggérée : {conduite}")
    st.code(f"🆔 Code patient : {code_patient}", language='markdown')

    # --- Sauvegarde ---
    data = {
        'code_patient': code_patient,
        'age': age,
        'sexe': sexe,
        'tabac': tabac,
        'pa': pa,
        'diabete': diabete,
        'osteoporose': osteoporose,
        'comorbidites': comorbidites,
        'neer': neer,
        'deplacement': deplacement,
        'ecart_mm': ecart_mm,
        'hsa': hsa,
        'dominance': dominance,
        'mobilite': mobilite,
        'traitement': traitement,
        'score_total': score,
        'risque_necrose': risque_necrose,
        'risque_pseudo': risque_pseudo,
        'risque_raideur': risque_raideur,
        'recommandation': conduite
    }

    df_new = pd.DataFrame([data])
    if os.path.exists("vigior_humerus_database.csv"):
        df_old = pd.read_csv("vigior_humerus_database.csv")
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv("vigior_humerus_database.csv", index=False)

    st.success("✅ Données enregistrées avec succès.")
