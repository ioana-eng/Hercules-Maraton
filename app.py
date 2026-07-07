import os
import re
import logging
import requests
from flask import Flask, send_from_directory, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
# Copy static assets into this folder at build time, or serve from root.
# For simplicity we serve from the current working directory root.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO)


@app.route("/")
@app.route("/index.html")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/editie.html")
def editie():
    return send_from_directory(BASE_DIR, "editie.html")


@app.route("/cros.html")
def cros():
    return send_from_directory(BASE_DIR, "cros.html")


@app.route("/semimaraton.html")
def semimaraton():
    return send_from_directory(BASE_DIR, "semimaraton.html")


@app.route("/maraton.html")
def maraton():
    return send_from_directory(BASE_DIR, "maraton.html")


@app.route("/kids.html")
def kids():
    return send_from_directory(BASE_DIR, "kids.html")


@app.route("/declaratii.html")
def declaratii():
    return send_from_directory(BASE_DIR, "declaratii.html")


@app.route("/assets/<path:path>")
def assets(path):
    assets_dir = os.path.join(BASE_DIR, "assets")
    if path.lower().endswith(".gpx"):
        return send_from_directory(
            assets_dir,
            path,
            as_attachment=True,
            mimetype="application/gpx+xml",
        )
    return send_from_directory(assets_dir, path)


@app.route("/api/participants")
def participants():
    url = "https://racetime.ro/events/189/participants"
    try:
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        response.raise_for_status()
    except requests.RequestException as exc:
        app.logger.error("Failed to fetch participants: %s", exc)
        return jsonify({"error": "Nu s-a putut încărca lista de participanți."}), 502

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        return jsonify({"participants": [], "count": 0})

    tbody = table.find("tbody")
    if not tbody:
        return jsonify({"participants": [], "count": 0})

    rows = tbody.find_all("tr")
    participants_list = []

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        text = " ".join(cell.get_text(strip=True) for cell in cells)
        if "Nu au fost găsiți participanți" in text:
            continue

        if len(cells) >= 5:
            participants_list.append({
                "race": cells[0].get_text(strip=True),
                "last_name": cells[1].get_text(strip=True),
                "first_name": cells[2].get_text(strip=True),
                "city": cells[3].get_text(strip=True),
                "club": cells[4].get_text(strip=True),
                "status": cells[5].get_text(strip=True) if len(cells) > 5 else "",
            })
        else:
            participants_list.append({
                "race": "",
                "last_name": "",
                "first_name": text,
                "city": "",
                "club": "",
                "status": "",
            })

    return jsonify({"participants": participants_list, "count": len(participants_list)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
