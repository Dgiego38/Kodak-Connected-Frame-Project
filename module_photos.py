import datetime
import os
import random
import time
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

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


# --- GÉNÉRATION DE L'IMAGE CARROUSEL ---
def generate_carrousel_image(photo_dir="photos"):
    """Génère l'image carrousel épurée (480x768) corrigée contre les bandes vertes Kodak."""
    now = datetime.datetime.now()
    day_name = DAYS_FR[now.weekday()]
    month_name = MONTHS_FR[now.month]
    date_str = f"{day_name} {now.day} {month_name} • {now.strftime('%H:%M')}"

    image_name = f"display_{int(time.time())}.jpg"

    scale = 2
    width, height = 480 * scale, 768 * scale
    cx = width / 2

    # Ajustement vertical pour recentrer sur l'écran Kodak
    OFFSET_Y = -15 * scale

    font_date = load_fonts(scale)
    TEXT_COLOR = (255, 255, 255)

    # 1. Sélection de l'image
    os.makedirs(photo_dir, exist_ok=True)
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    photos = [
        f
        for f in os.listdir(photo_dir)
        if f.lower().endswith(valid_extensions)
    ]

    if not photos:
        bg_img = Image.new("RGB", (width, height), (30, 41, 59))
        draw = ImageDraw.Draw(bg_img)
        draw_centered_text(
            draw,
            cx,
            (height / 2) + OFFSET_Y,
            "Aucune photo disponible",
            font_date,
            TEXT_COLOR,
        )
        bg_img_resized = bg_img.resize((480, 768), resample=LANCZOS_FILTER)
        bg_img_resized.save(
            image_name, "JPEG", quality=95, optimize=True, subsampling=0
        )
        return image_name

    selected_photo = random.choice(photos)
    photo_path = os.path.join(photo_dir, selected_photo)

    try:
        source_img = Image.open(photo_path)
        if hasattr(ImageOps, "exif_transpose"):
            source_img = ImageOps.exif_transpose(source_img)
        source_img = source_img.convert("RGB")
    except Exception as e:
        print(f"Erreur ouverture image {selected_photo}: {e}")
        return generate_carrousel_image(photo_dir)

    # Orientation portrait forcée
    if source_img.width > source_img.height:
        source_img = source_img.rotate(270, expand=True)

    # 2. Arrière-plan flouté (Strict RGB)
    bg_img = ImageOps.fit(source_img, (width, height), method=LANCZOS_FILTER)
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=30 * scale))
    bg_img = Image.eval(bg_img, lambda p: int(p * 0.60))

    # 3. Photo centrale
    photo_max_w = width - (20 * scale)
    photo_max_h = height - (80 * scale)

    fg_img = source_img.copy()
    fg_img.thumbnail((photo_max_w, photo_max_h), LANCZOS_FILTER)

    fg_w, fg_h = fg_img.size
    fg_x = int((width - fg_w) / 2)
    fg_y = int((height - fg_h) / 2) + (10 * scale) + OFFSET_Y

    # Collage direct sur image RGB
    bg_img.paste(fg_img, (fg_x, fg_y))

    # 4. Dessin direct du texte sur l'image RGB (sans overlay transparent)
    draw = ImageDraw.Draw(bg_img)
    draw_centered_text(
        draw, cx, (20 * scale) + OFFSET_Y, date_str, font_date, TEXT_COLOR
    )

    # Redimensionnement et sauvegarde avec subsampling=0 (Fix bande verte)
    img_resized = bg_img.resize((480, 768), resample=LANCZOS_FILTER)
    img_resized.save(
        image_name, "JPEG", quality=95, optimize=True, subsampling=0
    )

    return image_name