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


@app.route("/editii.html")
def editii():
    return send_from_directory(BASE_DIR, "editii.html")


@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(BASE_DIR, "robots.txt", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    return send_from_directory(BASE_DIR, "sitemap.xml", mimetype="application/xml")


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


@app.route("/kit.html")
def kit():
    return send_from_directory(BASE_DIR, "kit.html")


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


def _get_text(element, default=""):
    return element.get_text(strip=True) if element else default


@app.route("/api/participants")
def participants():
    url = "https://racetime.ro/events/189/participants"
    try:
        response = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
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
            race_cell = cells[0]
            race_name = _get_text(race_cell.find("div", class_="font-semibold"))
            race_category = _get_text(race_cell.find("div", class_="text-xs"))

            city_cell = cells[3]
            country_el = city_cell.find("p", class_="text-xs")
            country = _get_text(country_el)
            if country_el:
                country_el.extract()
            city = _get_text(city_cell)

            participants_list.append({
                "race": race_name,
                "category": race_category,
                "last_name": cells[1].get_text(strip=True),
                "first_name": cells[2].get_text(strip=True),
                "city": city,
                "country": country,
                "club": cells[4].get_text(strip=True),
                "status": cells[5].get_text(strip=True) if len(cells) > 5 else "",
            })
        else:
            participants_list.append({
                "race": "",
                "category": "",
                "last_name": "",
                "first_name": text,
                "city": "",
                "country": "",
                "club": "",
                "status": "",
            })

    resp = jsonify({"participants": participants_list, "count": len(participants_list)})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
