import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from flask import Flask, jsonify, Response

# ========================
# Model Setup
# ========================

device = torch.device("cpu")

# MobilenetV2 (2 classes: ok=0, needs_water=1)
model = models.mobilenet_v2(weights=None)
model.classifier[1] = nn.Linear(model.last_channel, 2)

state_dict = torch.load("lettuce_model.pth", map_location=device)
model.load_state_dict(state_dict)
model.eval()
model.to(device)

tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# ========================
# Camera Capture
# ========================

def capture_frame():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not detected on /dev/video0")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Camera opened but could not capture frame")

    return frame


def predict_needs_water(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    x = tf(pil_img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
    
    p_needs = float(probs[1].item())
    print("p(needs_water) =", p_needs)
    return p_needs


# ========================
# Flask Server
# ========================

app = Flask(__name__)

@app.route("/check_lettuce", methods=["GET"])
def check_lettuce():
    try:
        frame = capture_frame()
        p = predict_needs_water(frame)

        needs = p > 0.50
        msg = "WARNING: Lettuce likely needs water" if needs else "OK: Water level looks fine"

        return jsonify({
            "needs_water": needs,
            "probability": p,
            "message": msg,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/snapshot.jpg", methods=["GET"])
def snapshot():
    
    #Returns a JPEG snapshot directly from the camera.
    try:
        frame = capture_frame()

        # uncomment to save last snapshot for debugging
        # cv2.imwrite("last_snapshot.jpg", frame)

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("Failed to encode JPEG")

        return Response(buffer.tobytes(), mimetype="image/jpeg")

    except Exception as e:
        return Response(f"Error: {e}", status=500, mimetype="text/plain")


if __name__ == "__main__":
    print("AI server running on port 6000...")
    app.run(host="0.0.0.0", port=6000)