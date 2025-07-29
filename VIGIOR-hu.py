import streamlit as st

def calcul_risque(age, tabac_pa, nb_fragments, angle_hsa, deplacement):
    """
    Calculs simplifiés et fictifs des risques (%) basés sur les paramètres.
    En vrai, on utilisera un modèle statistique basé sur les données extraites.
    """
    risque_necrose = 0
    risque_pseudarthrose = 0
    risque_raideur = 0

    if age > 65:
        risque_necrose += 25
    if tabac_pa > 10:
        risque_necrose += 20
    if nb_fragments > 3:
        risque_necrose += 15
    if angle_hsa < 120 or angle_hsa > 150:
        risque_necrose += 15
    if deplacement > 5:
        risque_necrose += 10

    if age < 50:
        risque_pseudarthrose += 20
    if tabac_pa > 5:
        risque_pseudarthrose += 20
    if nb_fragments > 4:
        risque_pseudarthrose += 25
    if deplacement > 5:
        risque_pseudarthrose += 15

    if age > 60:
        risque_raideur += 30
    if deplacement > 5:
        risque_raideur += 20
    if nb_fragments > 3:
        risque_raideur += 20

    risque_necrose = min(risque_necrose, 90)
    risque_pseudarthrose = min(risque_pseudarthrose, 90)
    risque_raideur = min(risque_raideur, 90)

    return risque_necrose, risque_pseudarthrose, risque_raideur

def proposition_traitement(age, risque_necrose, risque_pseudarthrose, risque_raideur):
    seuil_arthroplastie = 50
    seuil_chirurgie = 30

    score_global = (risque_necrose + risque_pseudarthrose + risque_raideur) / 3

    if score_global >= seuil_arthroplastie or age > 75:
        traitement = "Traitement radical (arthroplastie primaire)"
        raison = (
            f"Compte tenu de l'âge du patient ({age} ans) et du profil de risque global "
            f"(nécrose estimée à {risque_necrose}%, pseudarthrose à {risque_pseudarthrose}%, raideur à {risque_raideur}%), "
            "une arthroplastie primaire est recommandée. Cette approche réduit les complications graves "
            "et améliore les résultats fonctionnels dans les cas à haut risque."
        )
    elif score_global >= seuil_chirurgie:
        traitement = "Réduction chirurgicale et ostéosynthèse"
        raison = (
            "Les risques modérés encouragent une prise en charge chirurgicale visant une réduction anatomique "
            "précise avec ostéosynthèse. Critères de bonne réduction : écart inter-fragmentaire < 3 mm, "
            "angulation HSA correcte (120-150°), stabilisation solide."
        )
    else:
        traitement = "Traitement orthopédique conservateur"
        raison = (
            "Les risques faibles et le profil patient permettent un traitement orthopédique avec surveillance "
            "clinique stricte et rééducation adaptée."
        )
    return traitement, raison

def main():
    st.title("VIGIOR - Estimation des risques de complications des fractures proximales de l'humérus")

    st.header("Entrée des données patient")
    age = st.number_input("Âge du patient (ans)", min_value=18, max_value=120, value=65)
    tabac_pa = st.number_input("Tabac (paquet-année)", min_value=0, max_value=100, value=0)
    nb_fragments = st.number_input("Nombre de fragments osseux", min_value=1, max_value=10, value=3)
    angle_hsa = st.number_input("Angle HSA (°)", min_value=90, max_value=180, value=135)
    deplacement = st.number_input("Écart inter-fragmentaire (mm)", min_value=0, max_value=50, value=0)

    if st.button("Évaluer le risque"):
        risque_necrose, risque_pseudarthrose, risque_raideur = calcul_risque(
            age, tabac_pa, nb_fragments, angle_hsa, deplacement)

        st.subheader("Risques estimés (%) selon traitement")
        st.markdown("**Traitement orthopédique conservateur :**")
        st.markdown(f"- Nécrose de la tête humérale : {risque_necrose}%")
        st.markdown(f"- Pseudarthrose : {risque_pseudarthrose}%")
        st.markdown(f"- Raideur fonctionnelle : {risque_raideur}%")

        st.markdown("**Réduction chirurgicale et ostéosynthèse :**")
        st.markdown(f"- Nécrose de la tête humérale : {max(risque_necrose - 15, 5)}%")
        st.markdown(f"- Pseudarthrose : {max(risque_pseudarthrose - 20, 5)}%")
        st.markdown(f"- Raideur fonctionnelle : {max(risque_raideur - 10, 5)}%")

        traitement, raison = proposition_traitement(age, risque_necrose, risque_pseudarthrose, risque_raideur)

        st.markdown("**Traitement radical (arthroplastie primaire) :**")
        st.markdown(raison)

        st.header("Proposition thérapeutique suggérée")
        st.success(f"{traitement}")

if __name__ == "__main__":
    main()
