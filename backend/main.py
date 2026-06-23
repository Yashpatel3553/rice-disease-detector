"""
RiceScan AI - Backend API
Serves predictions from your trained MobileNetV2 rice leaf disease model.
"""

import io
import os
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import tensorflow as tf

app = FastAPI(title="RiceScan AI API")

# Allow your frontend (Vercel/Netlify) to call this API.
# For production, replace "*" with your actual frontend URL, e.g.
# allow_origins=["https://your-site.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Configuration ----
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "mobilenet_rice.h5")
IMG_SIZE = (224, 224)  # MobileNetV2 default input size used in the notebook

# Class order MUST match the order Keras used during training.
# ImageDataGenerator sorts class folders alphabetically by default, so:
# Bacterialblight, Blast, Brownspot, Tungro
CLASS_NAMES = ["Bacterialblight", "Blast", "Brownspot", "Tungro"]

model = None


@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: model file not found at {MODEL_PATH}.")
        print("Place your exported .h5 model there before deploying.")
        return
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully from", MODEL_PATH)


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert uploaded bytes into a model-ready array."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)  # add batch dimension
    return arr


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "RiceScan AI API is live",
        "model_loaded": model is not None,
    }


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check server logs / model file path.",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        image_bytes = await file.read()
        processed = preprocess_image(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not process image: {e}")

    try:
        predictions = model.predict(processed)[0]  # shape: (4,)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    predicted_idx = int(np.argmax(predictions))
    predicted_class = CLASS_NAMES[predicted_idx]
    confidence = float(predictions[predicted_idx])

    all_probabilities = {
        CLASS_NAMES[i]: float(predictions[i]) for i in range(len(CLASS_NAMES))
    }

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "all_probabilities": all_probabilities,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
