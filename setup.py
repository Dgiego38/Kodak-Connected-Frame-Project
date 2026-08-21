import os
import socket
import requests

def obtenir_ip_locale():
    """Détecte automatiquement l'IP locale de la machine sur le réseau."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_locale = s.getsockname()[0]
    except Exception:
        ip_locale = "127.0.0.1"
    finally:
        s.close()
    return ip_locale

def configurer_projet():
    print("--- Configuration automatique de votre cadre Kodak connecté ---")
    
    ville = input("Nom de la ville (ex: Paris) : ").strip()
    prenom = input("Votre nom / prénom pour le footer (ex: Ton Prénom) : ").strip()
    
    # Détection automatique de l'IP + port par défaut
    ip_detectee = obtenir_ip_locale()
    port = "8000"
    ip_defaut = f"{ip_detectee}:{port}"
    
    choix_ip = input(f"Adresse IP du serveur détectée [{ip_defaut}] (Appuie sur Entrée pour valider ou tape-en une autre) : ").strip()
    ip = choix_ip if choix_ip else ip_defaut

    print(f"[INFO] Recherche automatique des coordonnées pour '{ville}'...")
    lat, lon = None, None
    try:
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(ville)}&count=1&language=fr&format=json"
        response = requests.get(url_geo, timeout=5)
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            nom_officiel = result.get("name", ville)
            print(f"[SUCCÈS] Trouvé : {nom_officiel} (Latitude: {lat}, Longitude: {lon})")
        else:
            print("[ERREUR] Ville introuvable via l'API. Vérifie l'orthographe.")
            return
    except Exception as e:
        print(f"[ERREUR] Impossible de contacter le service de géocodage : {e}")
        return

    # 1. Configuration directe de app.py
    if os.path.exists("app.py"):
        with open("app.py", "r", encoding="utf-8") as f:
            contenu_app = f.read()
        
        print("[INFO] Mise à jour directe de app.py...")
        contenu_app = contenu_app.replace("{{SERVER_IP}}", ip)
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(contenu_app)

    # 2. Configuration directe du module météo (module_meteo.py)
    if os.path.exists("module_meteo.py"):
        with open("module_meteo.py", "r", encoding="utf-8") as f:
            contenu_meteo = f.read()
        
        print("[INFO] Mise à jour directe de module_meteo.py...")
        contenu_meteo = contenu_meteo.replace("{{VILLE}}", ville)
        contenu_meteo = contenu_meteo.replace("{{LAT}}", str(lat))
        contenu_meteo = contenu_meteo.replace("{{LON}}", str(lon))
        contenu_meteo = contenu_meteo.replace("{{FOOTER_TEXT}}", prenom)
        
        with open("module_meteo.py", "w", encoding="utf-8") as f:
            f.write(contenu_meteo)

    # 3. Configuration directe du fichier XML du flux (ex: feed.xml)
    fichier_xml = "feed.xml" 
    if os.path.exists(fichier_xml):
        with open(fichier_xml, "r", encoding="utf-8") as f:
            contenu_xml = f.read()
        
        print(f"[INFO] Mise à jour directe de {fichier_xml}...")
        contenu_xml = contenu_xml.replace("{{SERVER_IP}}", ip)
        contenu_xml = contenu_xml.replace("{{VILLE}}", ville)
        
        with open(fichier_xml, "w", encoding="utf-8") as f:
            f.write(contenu_xml)

    print("\n[SUCCÈS] Fichiers configurés avec succès ! Tes scripts sont prêts à être lancés.")

if __name__ == "__main__":
    configurer_projet()