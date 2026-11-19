
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path
import csv

app = Flask(__name__)

DATA_FILE = Path(__file__).parent / "distractions.csv"


@app.route("/distraction", methods=["POST"])
def distraction():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"status": "invalid data"}), 400

    if request.headers.get("Origin", "").startswith(
        ("http://", "https://")
    ):
        return jsonify({"status": "forbidden"}), 403

    if data.get("website") != "Instagram":
        return jsonify({"status": "invalid website"}), 400

    website = "Instagram"
    timestamp = datetime.now().isoformat(timespec="seconds")

    new_file = not DATA_FILE.exists()

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        if new_file:
            writer.writerow(["website", "timestamp"])

        writer.writerow([website, timestamp])

    print(f"Blocked {website} at {timestamp}")

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
