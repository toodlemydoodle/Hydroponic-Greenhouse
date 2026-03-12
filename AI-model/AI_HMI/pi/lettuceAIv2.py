import base64
import json

import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from flask import Flask, jsonify

# set device to CPU as Raspberry Pi
device = torch.device("cpu")

# Load class index mapping from training
# {"0_FN": 0, "1_N": 1, "2_P": 2, "3_K": 3}
idx_to_class = {
    0: "0_FN",
    1: "1_N",
    2: "2_P",
    3: "3_K",
}
num_classes = len(idx_to_class)

# refine names for HMI display
Name_Labels = {
    "0_FN": "Healthy",
    "1_N": "Nitrogen Deficient",
    "2_P": "Phosphorus Deficient",
    "3_K": "Potassium Deficient",
}

# Build model architecture using MobileNetV2 for easier load on Raspberry Pi
model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, num_classes)

# Load trained model weights
state_dict = torch.load("lettuce_model.pth", map_location=device)
model.load_state_dict(state_dict)
model.eval()
model.to(device)

# Preprocessing (must match training!)
tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225],
    ),
])

#Capture frame from camera

def capture_frame():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not detected on /dev/video0")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Camera opened but failed to capture frame")

    return frame

# Run AI model on frame and return prediction results

def predict_npk_status(frame):
    # BGR -> RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    x = tf(pil_img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]

    # Get predicted class index
    pred_idx = int(torch.argmax(probs).item())
    class_folder = idx_to_class[pred_idx]         # e.g. "2_P"
    rename_labels = Name_Labels.get(class_folder, class_folder)

    # Convert all class probabilities to plain Python float dict
    probs_dict = {}
    for idx, p in enumerate(probs):
        folder_name = idx_to_class[idx]           # e.g. "1_N"
        probs_dict[folder_name] = float(p.item())

    print(f"Prediction: idx={pred_idx}, class={class_folder}, label={rename_labels}")
    print("Probabilities:", probs_dict)

    is_healthy = (class_folder == "0_FN")

    return {
        "pred_idx": pred_idx,
        "class_folder": class_folder,
        "label": rename_labels,
        "is_healthy": is_healthy,
        "probs": probs_dict,
    }

# Flask app for serving AI predictions
app = Flask(__name__)

@app.route("/check_lettuce", methods=["GET"])
def check_lettuce():
    try:
        # Capture frame from camera
        frame = capture_frame()

        # Run AI on the frame
        result = predict_npk_status(frame)
        label = result["label"]
        is_healthy = result["is_healthy"]

        # Simple status message for HMI
        if is_healthy:
            msg = "OK: Lettuce appears healthy."
        else:
            msg = f"WARNING: {label}."

        # Encode frame as JPEG for HMI
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("Failed to encode JPEG from camera frame")

        image_b64 = base64.b64encode(buffer).decode("ascii")

        # Return everything in one JSON response
        return jsonify({
            "status": label,                     
            "is_healthy": is_healthy,           
            "message": msg,
            "pred_idx": result["pred_idx"],
            "class_folder": result["class_folder"],
            "probs": result["probs"],           
            "image_b64": image_b64,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("AI server running on port 6000...")
    app.run(host="0.0.0.0", port=6000)
