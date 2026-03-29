import streamlit as st
from PIL import Image
import requests
from io import BytesIO

# --- Récupération sécurisée du token Hugging Face ---
HF_API_KEY = st.secrets["HUGGINGFACE"]["HF_API_KEY"]

# --- Titre de l'app ---
st.title("Détection de fracture - Radiographie")
st.write("Upload une radiographie pour que l'IA détecte la fracture.")

# --- Upload image ---
uploaded_file = st.file_uploader("Choisir une radiographie", type=["png","jpg","jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Radiographie uploadée", use_column_width=True)

    # --- Modèle Hugging Face actif ---
    # J'ai remplacé l'ancien modèle par un modèle actif pour éviter l'erreur 410
    model_id = "dengs/Fracture-Detection-YOLOv8"

    # Convertir image en bytes
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # --- Appel API Hugging Face ---
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers=headers,
            files={"file": img_bytes},
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            st.subheader("Résultat IA :")
            st.json(result)  # Affiche le JSON avec coordonnées et score
        else:
            st.error(f"Erreur API : {response.status_code}. Vérifie le modèle et ton token Hugging Face.")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API : {e}")
