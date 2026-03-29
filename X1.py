import streamlit as st
from PIL import Image, ImageDraw
import torch
import torchvision
import torchvision.transforms as T

st.title("🦴 VIGIOR - Détection automatique de fracture (IA)")

st.write("Upload une radiographie. Les zones suspectes sont encadrées.")

uploaded_file = st.file_uploader("Choisir une radiographie", type=["jpg","jpeg","png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Radiographie originale", use_column_width=True)

    # --- Chargement du modèle de détection d’objets ---
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    model.eval()

    transform = T.Compose([
        T.ToTensor()
    ])

    img_tensor = transform(image)

    with torch.no_grad():
        predictions = model([img_tensor])[0]

    boxes = predictions["boxes"]
    scores = predictions["scores"]

    threshold = 0.5

    draw = ImageDraw.Draw(image)

    detected = 0
    for box, score in zip(boxes, scores):
        if score > threshold:
            x1, y1, x2, y2 = box
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
            detected +=1

    st.image(image, caption="Zones suspectes", use_column_width=True)

    if detected > 0:
        st.warning(f"⚠️ {detected} zone(s) suspecte(s) détectée(s)")
    else:
        st.success("✅ Aucune zone suspecte détectée.")

    st.info("⚠️ Prototype IA : nécessite entraînement spécifique fractures pour précision clinique.")
