import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check_lettuce", methods=["GET"])
def check_lettuce():
    try:
        r = requests.get("http://172.20.10.5:6000/check_lettuce", timeout=5) #change IP accordingly
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)