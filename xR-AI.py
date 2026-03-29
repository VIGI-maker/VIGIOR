import streamlit as st
import torch
import torchvision.transforms as transforms
from PIL import Image
import torchvision.models as models

# Title
st.title("🦴 VIGIOR - Détection de fracture sur radiographie")

st.write("Upload une radiographie pour détecter une fracture (prototype IA).")

# Load model
@st.cache_resource
def load_model():
    model = models.resnet18(pretrained=True)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)  # 2 classes
    model.eval()
    return model

model = load_model()

# Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
])

# Upload image
uploaded_file = st.file_uploader("Choisir une radiographie", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)

    st.image(image, caption="Radiographie uploadée", use_column_width=True)

    img = transform(image).unsqueeze(0)

    # Fake prediction (car modèle non entraîné)
    with torch.no_grad():
        outputs = model(img)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        confidence = torch.max(probs).item()
        predicted = torch.argmax(probs, dim=1).item()

    if predicted == 1:
        st.error(f"⚠️ Fracture suspectée (confiance: {confidence:.2f})")
    else:
        st.success(f"✅ Pas de fracture détectée (confiance: {confidence:.2f})")

    st.info("⚠️ Prototype IA - non validé cliniquement")
