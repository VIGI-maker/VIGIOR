# xR-AI.py
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
uploaded_file = st.file_uploader("Choisir une radiographie", type=["png","jpg","jpeg","dcm"])
if uploaded_file:
    # Afficher l'image uploadée
    image = Image.open(uploaded_file)
    st.image(image, caption="Radiographie uploadée", use_column_width=True)

    # --- Préparation pour Hugging Face Inference API ---
    model_id = "mediclinal/Fracture-Detection-YOLOv8"  # modèle pré-entraîné exemple

    # Convertir image en bytes
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    # Appel API Hugging Face
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model_id}",
        headers=headers,
        files={"file": img_bytes}
    )

    if response.status_code == 200:
        result = response.json()
        st.subheader("Résultat IA :")
        st.write(result)  # tu peux personnaliser pour afficher les coordonnées du rectangle, etc.
    else:
        st.error(f"Erreur API : {response.status_code}")
