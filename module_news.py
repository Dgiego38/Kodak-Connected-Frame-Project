import datetime
import os
import time
import feedparser
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- COMPATIBILITÉ PILLOW (< 9.0.0 ET >= 9.0.0) ---
if not hasattr(Image, "Resampling"):

    class Resampling:
        LANCZOS = Image.LANCZOS
        BICUBIC = Image.BICUBIC
        BILINEAR = Image.BILINEAR
        NEAREST = Image.NEAREST

    Image.Resampling = Resampling

LANCZOS_FILTER = getattr(Image, "Resampling", Image).LANCZOS

# --- CONFIGURATION DE BASE ---
DAYS_FR = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
]
MONTHS_FR = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


# --- CHARGEMENT DES POLICES ---
def load_fonts(scale=2):
    font_paths = [
        "font.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(13 * scale))
            except Exception:
                continue
    return ImageFont.load_default()


def draw_centered_text(draw, cx, y, text, font, fill):
    try:
        w = draw.textlength(text, font=font)
    except AttributeError:
        try:
            w = font.getlength(text)
        except AttributeError:
            w, _ = font.getsize(text)

    x = cx - (w / 2)
    draw.text((x, y), text, fill=fill, font=font)


# --- GÉNÉRATION DE L'IMAGE NEWS ---
def generate_image():
    """Récupère un flux RSS d'actualités et génère l'image (480x768) pour le Kodak."""
    now = datetime.datetime.now()
    day_name = DAYS_FR[now.weekday()]
    month_name = MONTHS_FR[now.month]
    date_str = f"{day_name} {now.day} {month_name} • {now.strftime('%H:%M')}"

    image_name = f"news_{int(time.time())}.jpg"

    scale = 2
    width, height = 480 * scale, 768 * scale
    cx = width / 2

    OFFSET_Y = -15 * scale
    font_date = load_fonts(scale)
    font_body = load_fonts(scale)
    TEXT_COLOR = (255, 255, 255)

    # --- RÉCUPÉRATION DES INFOS (Flux RSS) ---
    rss_url = "https://www.franceinfo.fr/titres.rss"
    news_titles = []

    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:5]:
            news_titles.append(entry.title)
    except Exception as e:
        print(f"Erreur de lecture du flux RSS : {e}")
        news_titles = ["Impossible de charger les actualités"]

    if not news_titles:
        news_titles = ["Aucune actualité disponible"]

    # 1. Création du fond uni pour les news
    bg_img = Image.new("RGB", (width, height), (30, 41, 59))
    draw = ImageDraw.Draw(bg_img)

    # 2. En-tête (Date / Heure)
    draw_centered_text(
        draw, cx, (30 * scale) + OFFSET_Y, date_str, font_date, TEXT_COLOR
    )

    # Titre de la section
    draw_centered_text(
        draw, cx, (80 * scale) + OFFSET_Y, "• ACTUALITÉS •", font_date, (200, 200, 255)
    )

    # 3. Affichage des titres
    start_y = 140 * scale
    line_spacing = 45 * scale

    for i, title in enumerate(news_titles[:4]):
        if len(title) > 55:
            title = title[:52] + "..."

        draw_centered_text(
            draw, cx, start_y + (i * line_spacing), title, font_body, TEXT_COLOR
        )

    # 4. Sécurité anti-bug Kodak : redimensionnement et rognage net du bas
    safe_img = bg_img.resize((480, 772), resample=LANCZOS_FILTER)
    img_final = safe_img.crop((0, 0, 480, 768))

    # --- NETTOYAGE DES ANCIENNES IMAGES NEWS ---
    for old_file in os.listdir("."):
        if old_file.startswith("news_") and old_file.endswith(".jpg"):
            if old_file != image_name:  # On ne supprime pas celle qu'on vient de créer
                try:
                    os.remove(old_file)
                except Exception:
                    pass

    # Sauvegarde de la nouvelle image
    img_final.save(
        image_name, "JPEG", quality=95, optimize=True, subsampling=0
    )

    return image_name