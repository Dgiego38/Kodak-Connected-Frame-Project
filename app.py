from datetime import datetime
from email.utils import formatdate
import glob
import os
import time
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename

import module_meteo
import module_news
import module_photos
import module_note

app = Flask(__name__)

# --- DOSSIERS & CONFIGURATION ---
PHOTOS_DIR = "photos"
METEO_DIR = "meteo"
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(METEO_DIR, exist_ok=True)

# --- NETTOYAGE AU DÉMARRAGE ---
patterns = [
    "weather_*.jpg",
    "display_*.jpg",
    "note_*.jpg",
]

for pattern in patterns:
    for f in glob.glob(pattern):
        try:
            os.remove(f)
            print(f"[CLEANUP] Suppression de l'ancien fichier : {f}")
        except OSError:
            pass

CURRENT_MODULE = "photos"
CURRENT_NOTE = ""

# Charger la note existante au démarrage si le fichier existe
if os.path.exists("note.txt"):
    try:
        with open("note.txt", "r", encoding="utf-8") as f:
            CURRENT_NOTE = f.read()
    except Exception:
        pass

# Historique pour ne garder que les 3 dernières images générées sur le disque
IMAGE_HISTORY = []
MAX_HISTORY = 3

MODULE_TITLES = {
    "photos": "Galerie Photos",
    "meteo": "Météo",
    "news": "Actualités RSS",
    "note": "Note",
}


@app.route("/")
def index():
    return render_template("index.html")


# --- ROUTES COMPATIBLES AVEC LE FRONTEND ---


@app.route("/api/status", methods=["GET"])
def get_status():
    photos_list = (
        [
            f
            for f in os.listdir(PHOTOS_DIR)
            if f.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
            )
        ]
        if os.path.exists(PHOTOS_DIR)
        else []
    )

    mode_frontend = CURRENT_MODULE
    if mode_frontend == "photos":
        mode_frontend = "carrousel"
    elif mode_frontend == "news":
        mode_frontend = "actualites"

    return jsonify(
        {
            "mode": mode_frontend,
            "note_text": CURRENT_NOTE,
            "photos": photos_list,
        }
    )


@app.route("/api/config", methods=["POST"])
def set_config():
    global CURRENT_MODULE, CURRENT_NOTE
    data = request.get_json() or {}

    if "note_text" in data:
        CURRENT_NOTE = data["note_text"]
        try:
            with open("note.txt", "w", encoding="utf-8") as f:
                f.write(CURRENT_NOTE)
        except Exception as e:
            print(f"[ERREUR] Impossible d'écrire note.txt : {e}")

    if "mode" in data:
        mode = data["mode"]
        if mode == "carrousel":
            CURRENT_MODULE = "photos"
        elif mode == "actualites":
            CURRENT_MODULE = "news"
        elif mode in ["photos", "meteo", "news", "note"]:
            CURRENT_MODULE = mode

        print("\n" + "=" * 50)
        print(
            f"[ACTION] Changement de module vers : {CURRENT_MODULE.upper()}"
        )

        try:
            if CURRENT_MODULE == "meteo":
                print("[EXEC] Lancement de module_meteo.py...")
                try:
                    img_path = module_meteo.generate_image("meteo")
                except TypeError:
                    img_path = module_meteo.generate_image()
                print(f"[OK] Image météo générée : {img_path}")

            elif CURRENT_MODULE == "photos":
                print("[EXEC] Lancement de module_photos.py...")
                img_path = module_photos.generate_carrousel_image("photos")
                print(f"[OK] Image photo générée : {img_path}")

            elif CURRENT_MODULE == "note":
                print("[EXEC] Lancement de module_note.py...")
                img_path = module_note.generate_image()
                print(f"[OK] Image note générée : {img_path}")

            elif CURRENT_MODULE == "news":
                print("[EXEC] Lancement de module_news.py...")
                img_path = module_news.generate_image()
                print(f"[OK] Image news générée : {img_path}")

        except Exception as e:
            print(f"[ERREUR] Échec lors de la génération : {e}")

        print("=" * 50 + "\n")

    return jsonify(
        {"success": True, "mode": CURRENT_MODULE, "note": CURRENT_NOTE}
    )


@app.route("/api/upload", methods=["POST"])
def upload_photo():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier envoyé"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(PHOTOS_DIR, filename)
    file.save(save_path)
    print(f"[PHOTO] Téléversée : {filename}")
    return jsonify({"success": True, "filename": filename})


@app.route("/api/delete-photo", methods=["POST"])
def delete_photo():
    data = request.get_json() or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Nom de fichier manquant"}), 400

    filepath = os.path.join(PHOTOS_DIR, secure_filename(filename))
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"[PHOTO] Supprimée : {filename}")
        return jsonify({"success": True})
    return jsonify({"error": "Fichier introuvable"}), 404


@app.route("/photos/<filename>")
def serve_photo_file(filename):
    return send_from_directory(PHOTOS_DIR, secure_filename(filename))


@app.route("/preview.jpg")
def preview_jpg():
    return serve_image()


# --- ROUTES D'ORIGINE ET API MODULES ---


@app.route("/api/module", methods=["GET"])
def get_module():
    return jsonify({"current_module": CURRENT_MODULE})


@app.route("/api/module/<module_name>", methods=["POST"])
def set_module(module_name):
    global CURRENT_MODULE
    if module_name in ["photos", "meteo", "news", "note"]:
        CURRENT_MODULE = module_name

        print("\n" + "=" * 50)
        print(f"[ACTION] Changement de module vers : {module_name.upper()}")

        if module_name == "meteo":
            print("[EXEC] Lancement de module_meteo.py...")
            try:
                img_path = module_meteo.generate_image("meteo")
            except TypeError:
                img_path = module_meteo.generate_image()
            print(f"[OK] Image météo : {img_path}")

        elif module_name == "photos":
            print("[EXEC] Lancement de module_photos.py...")
            img_path = module_photos.generate_carrousel_image("photos")
            print(f"[OK] Image photo : {img_path}")

        elif module_name == "note":
            print("[EXEC] Lancement de module_note.py...")
            img_path = module_note.generate_image()
            print(f"[OK] Image note : {img_path}")

        elif module_name == "news":
            print("[EXEC] Lancement de module_news.py...")
            img_path = module_news.generate_image()
            print(f"[OK] Image news : {img_path}")

        print("=" * 50 + "\n")

        return jsonify({"success": True, "current_module": CURRENT_MODULE})

    return jsonify({"error": "Module inconnu"}), 400


# --- FLUX RSS AUTO-RAFRAÎCHISSANT POUR KODAK ---


@app.route("/feed.xml")
def serve_feed():
    now_ts = int(time.time())
    rfc822_date = formatdate(timeval=now_ts, localtime=False, usegmt=True)

    server_ip = "{{SERVER_IP}}"
    title = MODULE_TITLES.get(CURRENT_MODULE, "Flux Kodak")
    image_url = f"http://{server_ip}/display.jpg?v={now_ts}"

    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Flux Kodak</title>
    <link>http://{server_ip}/</link>
    <description>Flux Photo Kodak</description>
    <pubDate>{rfc822_date}</pubDate>
    <lastBuildDate>{rfc822_date}</lastBuildDate>
    <ttl>1</ttl>
    <item>
      <title>{title}</title>
      <link>{image_url}</link>
      <description>&lt;img src="{image_url}" /&gt;</description>
      <pubDate>{rfc822_date}</pubDate>
      <guid isPermaLink="false">kodak_item_{now_ts}</guid>
      <media:content url="{image_url}" type="image/jpeg" medium="image" />
      <media:thumbnail url="{image_url}" />
    </item>
  </channel>
</rss>"""

    return Response(
        xml_content.strip(),
        mimetype="application/rss+xml",
        headers={
            "Content-Type": "application/rss+xml; charset=utf-8",
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# --- ROUTE SERVEUR D'IMAGES DYNAMIQUE ---


@app.route("/<image_name>.jpg")
@app.route("/display.jpg")
def serve_image(image_name=None):
    generated_file = None

    if CURRENT_MODULE == "photos":
        generated_file = module_photos.generate_carrousel_image("photos")
    elif CURRENT_MODULE == "note":
        generated_file = module_note.generate_image()
    elif CURRENT_MODULE == "meteo":
        try:
            generated_file = module_meteo.generate_image("meteo")
        except TypeError:
            generated_file = module_meteo.generate_image()
    elif CURRENT_MODULE == "news":
        generated_file = module_news.generate_image()

    if generated_file and os.path.exists(generated_file):
        if generated_file not in IMAGE_HISTORY:
            IMAGE_HISTORY.append(generated_file)

        while len(IMAGE_HISTORY) > MAX_HISTORY:
            oldest_file = IMAGE_HISTORY.pop(0)
            if os.path.exists(oldest_file):
                try:
                    os.remove(oldest_file)
                except OSError:
                    pass

        with open(generated_file, "rb") as f:
            image_bytes = f.read()

        return Response(
            image_bytes,
            mimetype="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    return "Erreur lors de la génération de l'image", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)