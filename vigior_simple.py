import streamlit as st

st.title("VIGIOR - Test minimal")

st.write("Bienvenue dans cette version simplifiée de VIGIOR.")

# Exemple simple : calculer un risque fictif selon deux paramètres

param1 = st.number_input("Entrez une valeur pour le paramètre 1", min_value=0, max_value=100, value=50)
param2 = st.number_input("Entrez une valeur pour le paramètre 2", min_value=0, max_value=100, value=50)

# Calcul fictif du risque
risque = (param1 * 0.6 + param2 * 0.4) / 100

st.write(f"Risque calculé : {risque:.2f}")

if risque > 0.5:
    st.warning("Attention : risque élevé !")
else:
    st.success("Risque faible.")

