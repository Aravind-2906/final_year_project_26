import cv2
import numpy as np
import joblib
import os
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input

# ================= CONFIG ================= #
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "ultimate_glaucoma_model.pkl")

IMG_SIZE = 96

print("Loading trained model...")

# Load hybrid ML model
svm_model, rf_model, scaler, pca = joblib.load(MODEL_PATH)

# Load CNN model
cnn_model = EfficientNetB0(
    weights="imagenet",
    include_top=False,
    pooling="avg",
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

# ================= STRICT RETINA VALIDATION ================= #
def is_retina_image(img):

    if img is None:
        return False

    h, w, _ = img.shape

    # Resolution check
    if h < 200 or w < 200:
        return False

    # RGB dominance check
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    r, g, b = cv2.split(rgb)

    if np.mean(r) < np.mean(g) or np.mean(r) < np.mean(b):
        return False

    # Brightness pattern check (center vs border)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    center_region = gray[h//4:3*h//4, w//4:3*w//4]
    border_region = np.concatenate([
        gray[:h//4, :].flatten(),
        gray[3*h//4:, :].flatten(),
        gray[:, :w//4].flatten(),
        gray[:, 3*w//4:].flatten()
    ])

    if np.mean(center_region) <= np.mean(border_region):
        return False

    # Optic disc detection
    blur = cv2.GaussianBlur(gray, (9, 9), 1.5)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=50,
        param2=25,
        minRadius=20,
        maxRadius=120
    )

    if circles is None:
        return False

    return True


# ================= CDR CALCULATION ================= #
def calculate_cdr(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    blur = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=30,
        maxRadius=120
    )

    if circles is None:
        return None

    circles = np.uint16(np.around(circles))
    x, y, disc_r = circles[0][0]

    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return None

    largest = max(contours, key=cv2.contourArea)
    (cx, cy), cup_r = cv2.minEnclosingCircle(largest)

    if disc_r == 0:
        return None

    cdr = cup_r / disc_r
    return round(cdr, 3)


# ================= FEATURE EXTRACTION ================= #
def extract_features(img):

    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)

    features = cnn_model.predict(img, verbose=0)[0]
    return features


# ================= PREDICTION FOR WEB ================= #
def predict_for_web(img_path):

    if not os.path.exists(img_path):
        return {"status": "error", "message": "Image file not found"}

    img = cv2.imread(img_path)

    if img is None:
        return {"status": "error", "message": "Unable to read image"}

    # Retina validation
    if not is_retina_image(img):
        return {"status": "invalid", "message": "Not a retinal fundus image"}

    # CDR calculation
    cdr_value = calculate_cdr(img)

    # Feature extraction
    feat = extract_features(img)

    feat = scaler.transform([feat])
    feat = pca.transform(feat)

    svm_pred = svm_model.predict_proba(feat)
    rf_pred = rf_model.predict_proba(feat)

    final_pred = (svm_pred + rf_pred) / 2

    # Hybrid Decision Adjustment
    if cdr_value is not None:
        if cdr_value > 0.6:
            final_pred[0][0] += 0.05

    label = np.argmax(final_pred)
    confidence = np.max(final_pred) * 100

    return {
        "status": "success",
        "result": "Glaucoma" if label == 0 else "Normal",
        "confidence": round(float(confidence), 2),
        "cdr": float(cdr_value) if cdr_value is not None else None
    }