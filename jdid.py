import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import os
import json

# --- Dossiers pour sauvegarder annotations ---
os.makedirs("annotated_images", exist_ok=True)
os.makedirs("annotations", exist_ok=True)

# --- Token Hugging Face ---
HF_API_KEY = st.secrets["HUGGINGFACE"]["HF_API_KEY"]
model_id = "dengs/Fracture-Detection-YOLOv8"  # modèle actif pour fractures

st.title("Détection de fracture - Radiographie")
st.write("Upload une radiographie, l'IA détecte la fracture, tu peux corriger si nécessaire.")

# --- Upload image ---
uploaded_file = st.file_uploader("Choisir une radiographie", type=["png","jpg","jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Radiographie uploadée", use_column_width=True)

    # --- Détection automatique via Hugging Face ---
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

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
            st.subheader("Résultat IA (coordonnées et score) :")
            st.json(result)
        else:
            st.warning(f"Erreur API : {response.status_code}. Vérifie le modèle ou le token.")

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur connexion API : {e}")

    # --- Correction / annotation manuelle ---
    st.subheader("Annotation manuelle si nécessaire :")
    x_min = st.number_input("x_min", value=0, min_value=0)
    y_min = st.number_input("y_min", value=0, min_value=0)
    x_max = st.number_input("x_max", value=image.width, min_value=0)
    y_max = st.number_input("y_max", value=image.height, min_value=0)

    if st.button("Sauvegarder annotation"):
        img_name = f"annotated_images/{uploaded_file.name}"
        image.save(img_name)
        ann_name = f"annotations/{uploaded_file.name}.json"
        with open(ann_name, "w") as f:
            json.dump({"bbox": [x_min, y_min, x_max, y_max]}, f)
        st.success(f"Annotation sauvegardée pour {uploaded_file.name}")
