import datetime
import math
import os
import time
from PIL import Image, ImageDraw, ImageFont
import requests

# --- CONFIGURATION ---
LAT, LON = 48.669, 7.712  # Vendenheim

WEATHER_DESCRIPTIONS = {
    0: "Ciel dégagé",
    1: "Principalement dégagé",
    2: "Partiellement nuageux",
    3: "Couvert",
    45: "Brouillard",
    48: "Brouillard givrant",
    51: "Bruine légère",
    53: "Bruine modérée",
    55: "Bruine dense",
    61: "Pluie faible",
    63: "Pluie modérée",
    65: "Pluie forte",
    71: "Neige faible",
    73: "Neige modérée",
    75: "Neige forte",
    80: "Averses faibles",
    81: "Averses modérées",
    82: "Averses violentes",
    95: "Orage",
    96: "Orage avec grêle",
    99: "Orage fort avec grêle",
}

DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
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


def safe_iso_parse(iso_str):
    if not iso_str:
        return "--:--"
    try:
        iso_clean = iso_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(iso_clean).strftime("%H:%M")
    except Exception:
        return iso_str.split("T")[-1][:5] if "T" in iso_str else "--:--"


def fetch_weather_data():
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&current_weather=true"
        f"&hourly=relativehumidity_2m,apparent_temperature,precipitation_probability,uv_index,weathercode"
        f"&daily=sunrise,sunset,temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=auto"
    )
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        now = datetime.datetime.now()
        current_hour = now.hour

        temp = round(data["current_weather"]["temperature"])
        wind = round(data["current_weather"]["windspeed"])
        weathercode = data["current_weather"]["weathercode"]
        is_day = data["current_weather"].get("is_day", 1)

        humidity = data["hourly"]["relativehumidity_2m"][current_hour]
        feels_like = round(data["hourly"]["apparent_temperature"][current_hour])
        pop = data["hourly"]["precipitation_probability"][current_hour]
        uv = round(data["hourly"]["uv_index"][current_hour], 1)

        temp_max = round(data["daily"]["temperature_2m_max"][0])
        temp_min = round(data["daily"]["temperature_2m_min"][0])
        rain_sum = data["daily"]["precipitation_sum"][0]

        sunrise = safe_iso_parse(data["daily"]["sunrise"][0])
        sunset = safe_iso_parse(data["daily"]["sunset"][0])

        condition_text = WEATHER_DESCRIPTIONS.get(weathercode, "Météo variable")

        hourly_forecast = []
        for i in range(1, 5):
            target_hour = (current_hour + i) % 24
            h_temp = round(data["hourly"]["apparent_temperature"][target_hour])
            h_code = data["hourly"]["weathercode"][target_hour]
            hourly_forecast.append({
                "time": f"{target_hour}h",
                "temp": h_temp,
                "code": h_code,
            })

        return {
            "temp": temp,
            "feels_like": feels_like,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "wind": f"{wind} km/h",
            "humidity": f"{humidity}%",
            "pop": f"{pop}%",
            "rain_sum": f"{rain_sum} mm",
            "uv": uv,
            "sunrise": sunrise,
            "sunset": sunset,
            "code": weathercode,
            "condition": condition_text,
            "is_day": is_day,
            "hourly": hourly_forecast,
        }
    except Exception as e:
        print(f"Erreur API Météo : {e}")
        return {
            "temp": "--",
            "feels_like": "--",
            "temp_max": "--",
            "temp_min": "--",
            "wind": "-- km/h",
            "humidity": "--%",
            "pop": "--%",
            "rain_sum": "-- mm",
            "uv": "--",
            "sunrise": "--:--",
            "sunset": "--:--",
            "code": -1,
            "condition": "Indisponible",
            "is_day": 1,
            "hourly": [],
        }


def load_fonts(scale=2):
    font_paths = [
        "font.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    bold_paths = [
        "font-bold.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    def make_font(sizes, bold=False):
        paths = bold_paths if bold else font_paths
        for p in paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, int(sizes * scale))
                except Exception:
                    continue
        return ImageFont.load_default()

    return {
        "city": make_font(28, bold=True),
        "date": make_font(13, bold=False),
        "temp": make_font(84, bold=False),
        "subtemp": make_font(13, bold=True),
        "cond": make_font(16, bold=True),
        "card_title": make_font(11, bold=True),
        "info": make_font(13, bold=False),
        "info_bold": make_font(15, bold=True),
        "small": make_font(12, bold=False),
        "footer": make_font(10, bold=False),
    }


def draw_card(draw, box, radius, fill, outline=None, width=1):
    try:
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    except Exception:
        draw.rectangle(box, fill=fill, outline=outline)


def draw_weather_icon(draw, code, is_day, center_x, center_y, scale=2, icon_scale=1.0):
    cx, cy = center_x, center_y
    s = scale * icon_scale

    if code in [0, 1]:
        if is_day:
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x1 = cx + math.cos(rad) * 14 * s
                y1 = cy + math.sin(rad) * 14 * s
                x2 = cx + math.cos(rad) * 22 * s
                y2 = cy + math.sin(rad) * 22 * s
                draw.line([(x1, y1), (x2, y2)], fill=(250, 204, 21, 255), width=int(3 * s))
            draw.ellipse([cx - 10 * s, cy - 10 * s, cx + 10 * s, cy + 10 * s], fill=(250, 204, 21, 255))
        else:
            draw.ellipse([cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s], fill=(226, 232, 240, 255))
            draw.ellipse([cx - 4 * s, cy - 18 * s, cx + 18 * s, cy + 10 * s], fill=(30, 41, 59, 255))

    elif code == 2:
        if is_day:
            scx, scy = cx + 8 * s, cy - 8 * s
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x1 = scx + math.cos(rad) * 8 * s
                y1 = scy + math.sin(rad) * 8 * s
                x2 = scx + math.cos(rad) * 13 * s
                y2 = scy + math.sin(rad) * 13 * s
                draw.line([(x1, y1), (x2, y2)], fill=(250, 204, 21, 255), width=int(2 * s))
            draw.ellipse([scx - 6 * s, scy - 6 * s, scx + 6 * s, scy + 6 * s], fill=(250, 204, 21, 255))

        draw.ellipse([cx - 16 * s, cy - 3 * s, cx + 3 * s, cy + 13 * s], fill=(191, 219, 254, 255))
        draw.ellipse([cx - 6 * s, cy - 11 * s, cx + 14 * s, cy + 13 * s], fill=(255, 255, 255, 255))

    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
        draw.ellipse([cx - 16 * s, cy - 8 * s, cx + 6 * s, cy + 8 * s], fill=(148, 163, 184, 255))
        draw.ellipse([cx - 4 * s, cy - 14 * s, cx + 16 * s, cy + 8 * s], fill=(203, 213, 225, 255))
        for offset in [-6, 0, 6]:
            draw.line(
                [(cx + offset * s, cy + 10 * s), ((cx + offset - 2) * s, (cy + 18) * s)],
                fill=(96, 165, 250, 255),
                width=int(2 * s),
            )

    else:
        draw.ellipse([cx - 16 * s, cy - 8 * s, cx + 6 * s, cy + 8 * s], fill=(148, 163, 184, 255))
        draw.ellipse([cx - 4 * s, cy - 14 * s, cx + 16 * s, cy + 14 * s], fill=(203, 213, 225, 255))


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


def create_weather_image_portrait(data, folder=None):
    now = datetime.datetime.now()
    day_name = DAYS_FR[now.weekday()]
    month_name = MONTHS_FR[now.month]
    date_str = f"{day_name} {now.day} {month_name}"
    time_str = now.strftime("%H:%M")

    filename = f"weather_{now.strftime('%H%M%S')}.jpg"

    if folder:
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
    else:
        filepath = filename

    scale = 2
    width, height = 480 * scale, 768 * scale
    cx = width / 2

    margin = 20 * scale
    card_w = width - (margin * 2)

    is_day = data.get("is_day", 1)
    hour = now.hour

    if not is_day or hour < 6 or hour >= 22:
        top_color, bottom_color = (15, 23, 42), (30, 41, 59)
    elif 6 <= hour <= 8 or 19 <= hour <= 21:
        top_color, bottom_color = (79, 110, 138), (180, 110, 110)
    else:
        top_color, bottom_color = (56, 130, 195), (115, 175, 230)

    img = Image.new("RGBA", (width, height), top_color + (255,))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * (y / height))
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * (y / height))
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    fonts = load_fonts(scale)

    TEXT_PRIMARY = (255, 255, 255, 255)
    TEXT_SECONDARY = (255, 255, 255, 180)
    CARD_BG = (255, 255, 255, 38)
    CARD_BORDER = (255, 255, 255, 55)

    draw_centered_text(draw, cx, 32 * scale, "Vendenheim", fonts["city"], TEXT_PRIMARY)
    draw_centered_text(draw, cx, 66 * scale, f"{date_str} • {time_str}", fonts["date"], TEXT_SECONDARY)

    temp_val = f"{data['temp']}°" if isinstance(data["temp"], int) else "--°"
    draw_centered_text(draw, cx, 78 * scale, temp_val, fonts["temp"], TEXT_PRIMARY)
    draw_centered_text(draw, cx, 166 * scale, data["condition"], fonts["cond"], TEXT_PRIMARY)

    subtemp_str = (
        f"Ressenti {data['feels_like']}°  •  Max {data['temp_max']}°  Min {data['temp_min']}°"
        if isinstance(data["temp"], int) else ""
    )
    draw_centered_text(draw, cx, 188 * scale, subtemp_str, fonts["subtemp"], TEXT_SECONDARY)

    if data["hourly"]:
        box_y1, box_y2 = 216 * scale, 330 * scale
        draw_card(draw, [margin, box_y1, width - margin, box_y2], radius=22 * scale, fill=CARD_BG, outline=CARD_BORDER, width=int(1.5 * scale))

        col_width = card_w / 4
        for idx, item in enumerate(data["hourly"]):
            col_cx = margin + (col_width * idx) + (col_width / 2)
            draw_centered_text(draw, col_cx, box_y1 + 14 * scale, item["time"], fonts["small"], TEXT_SECONDARY)
            draw_weather_icon(draw, item["code"], 1, center_x=col_cx, center_y=box_y1 + 54 * scale, scale=scale, icon_scale=0.75)
            draw_centered_text(draw, col_cx, box_y1 + 86 * scale, f"{item['temp']}°", fonts["info_bold"], TEXT_PRIMARY)

    card_y1, card_y2 = 344 * scale, 518 * scale
    col_gap = 12 * scale
    half_w = (card_w - col_gap) / 2

    draw_card(draw, [margin, card_y1, margin + half_w, card_y2], radius=22 * scale, fill=CARD_BG, outline=CARD_BORDER, width=int(1.5 * scale))
    draw.text((margin + 16 * scale, card_y1 + 14 * scale), "VENT & PRECIP", fill=TEXT_SECONDARY, font=fonts["card_title"])
    draw.text((margin + 16 * scale, card_y1 + 40 * scale), f"Vent : {data['wind']}", fill=TEXT_PRIMARY, font=fonts["info"])
    draw.text((margin + 16 * scale, card_y1 + 72 * scale), f"Risque : {data['pop']}", fill=TEXT_PRIMARY, font=fonts["info"])
    draw.text((margin + 16 * scale, card_y1 + 104 * scale), f"Cumul : {data['rain_sum']}", fill=TEXT_PRIMARY, font=fonts["info"])

    right_x1 = margin + half_w + col_gap
    draw_card(draw, [right_x1, card_y1, width - margin, card_y2], radius=22 * scale, fill=CARD_BG, outline=CARD_BORDER, width=int(1.5 * scale))
    draw.text((right_x1 + 16 * scale, card_y1 + 14 * scale), "ATMOSPHÈRE", fill=TEXT_SECONDARY, font=fonts["card_title"])
    draw.text((right_x1 + 16 * scale, card_y1 + 40 * scale), f"Humidité : {data['humidity']}", fill=TEXT_PRIMARY, font=fonts["info"])

    uv_val = data["uv"]
    uv_color = (
        (134, 239, 172, 255) if isinstance(uv_val, (int, float)) and uv_val <= 2
        else (253, 224, 71, 255) if isinstance(uv_val, (int, float)) and uv_val <= 5
        else (248, 113, 113, 255)
    )
    draw.text((right_x1 + 16 * scale, card_y1 + 72 * scale), f"Indice UV : {uv_val}", fill=uv_color, font=fonts["info_bold"])

    sun_y1, sun_y2 = 532 * scale, 642 * scale
    draw_card(draw, [margin, sun_y1, width - margin, sun_y2], radius=22 * scale, fill=CARD_BG, outline=CARD_BORDER, width=int(1.5 * scale))
    draw_centered_text(draw, cx, sun_y1 + 20 * scale, f"Lever du soleil  •  {data['sunrise']}", fonts["info_bold"], TEXT_PRIMARY)
    draw_centered_text(draw, cx, sun_y1 + 58 * scale, f"Coucher du soleil  •  {data['sunset']}", fonts["info_bold"], TEXT_SECONDARY)

    draw_centered_text(draw, cx, 715 * scale, "{{FOOTER_TEXT}}", fonts["footer"], TEXT_SECONDARY)

    img_final = Image.new("RGB", (width, height), top_color)
    img_final.paste(img, mask=img.split()[3])

    img_resized = img_final.resize((480, 768), resample=Image.LANCZOS)
    img_resized.save(filepath, "JPEG", quality=95, progressive=False, optimize=True, subsampling="4:2:0")
    
    return filepath


def generate_image(folder=None):
    """Point d'entrée appelé par app.py"""
    data = fetch_weather_data()
    return create_weather_image_portrait(data, folder=folder)