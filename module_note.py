import datetime
import os
import time
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


# --- GÉNÉRATION DE L'IMAGE NOTE ---
def generate_image():
    """Lit un fichier note.txt et génère l'image (480x768) pour le Kodak."""
    now = datetime.datetime.now()
    day_name = DAYS_FR[now.weekday()]
    month_name = MONTHS_FR[now.month]
    date_str = f"{day_name} {now.day} {month_name} • {now.strftime('%H:%M')}"

    image_name = f"note_{int(time.time())}.jpg"

    scale = 2
    width, height = 480 * scale, 768 * scale
    cx = width / 2

    OFFSET_Y = -15 * scale
    font_date = load_fonts(scale)
    font_body = load_fonts(scale)
    TEXT_COLOR = (255, 255, 255)

    # --- RÉCUPÉRATION DU CONTENU DE LA NOTE ---
    note_lines = []
    note_path = "note.txt"

    if os.path.exists(note_path):
        try:
            with open(note_path, "r", encoding="utf-8") as f:
                content = f.read().splitlines()
                for line in content:
                    note_lines.append(line)
        except Exception as e:
            print(f"Erreur de lecture du fichier note.txt : {e}")
            note_lines = ["Erreur de lecture de la note"]

    if not note_lines:
        note_lines = ["Aucune note enregistrée."]

    # 1. Création du fond uni pour les notes (couleur légèrement différente pour varier, ex: bleu nuit/gris)
    bg_img = Image.new("RGB", (width, height), (33, 37, 41))
    draw = ImageDraw.Draw(bg_img)

    # 2. En-tête (Date / Heure)
    draw_centered_text(
        draw, cx, (30 * scale) + OFFSET_Y, date_str, font_date, TEXT_COLOR
    )

    # Titre de la section
    draw_centered_text(
        draw, cx, (80 * scale) + OFFSET_Y, "• NOTES •", font_date, (255, 200, 100)
    )

    # 3. Affichage des lignes de la note
    start_y = 140 * scale
    line_spacing = 40 * scale

    for i, line in enumerate(note_lines[:12]):  # Limité à 12 lignes max pour l'écran
        if len(line) > 55:
            line = line[:52] + "..."

        draw_centered_text(
            draw, cx, start_y + (i * line_spacing), line, font_body, TEXT_COLOR
        )

    # 4. Sécurité anti-bug Kodak : redimensionnement et rognage net du bas
    safe_img = bg_img.resize((480, 772), resample=LANCZOS_FILTER)
    img_final = safe_img.crop((0, 0, 480, 768))

    # --- NETTOYAGE DES ANCIENNES IMAGES NOTE ---
    for old_file in os.listdir("."):
        if old_file.startswith("note_") and old_file.endswith(".jpg"):
            if old_file != image_name:
                try:
                    os.remove(old_file)
                except Exception:
                    pass

    # Sauvegarde de la nouvelle image
    img_final.save(
        image_name, "JPEG", quality=95, optimize=True, subsampling=0
    )

    return image_name