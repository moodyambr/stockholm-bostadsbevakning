import requests
import json
import smtplib
import os
from email.mime.text import MIMEText
from pathlib import Path


URL = "https://bostad.stockholm.se/AllaAnnonser/"

MIN_RUM = 1
MIN_YTA = 30
MAX_HYRA = 14000

OMRADEN = [
    "Södermalm", "Kungsholmen", "Norrmalm", "Vasastan",
    "Östermalm", "Gamla stan", "Ladugårdsgärdet",
    "Johanneshov", "Liljeholmen", "Gröndal",
    "Årstadal", "Hammarby Sjöstad"
]

SEEN_FILE = "seen.json"

EMAIL_FROM = "msn610@gmail.com"
EMAIL_TO = "moodyamberdal@gmail.com"


def fetch_data():
    res = requests.get(URL, timeout=15)
    res.raise_for_status()
    return res.json()


def load_seen():
    if Path(SEEN_FILE).exists():
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def filter_bostader(data):
    results = []

    for b in data:

        try:
            if (
                b["AntalRum"] >= MIN_RUM and
                b["Yta"] >= MIN_YTA and
                b["Hyra"] <= MAX_HYRA and
                b["Stadsdel"] in OMRADEN
            ):
                results.append(b)
        except Exception:
            continue

    return results


def get_new(listings, seen):
    new_items = []

    for b in listings:
        annons_id = b["AnnonsId"]

        if annons_id not in seen:
            new_items.append(b)
            seen.add(annons_id)

    return new_items, seen




def send_mail(items):
    if not items:
        return

    email_pass = os.environ["EMAIL_PASS"]

    text = "🏠 Nya bostäder i Stockholm:\n\n"

    for b in items:
        text += f"""
Adress: {b['Gatuadress']}
Område: {b['Stadsdel']}
Rum: {b['AntalRum']}
Yta: {b['Yta']} m²
Hyra: {b['Hyra']} kr
Länk: {b['Url']}
------------------------
"""

    msg = MIMEText(text)
    msg["Subject"] = f"{len(items)} nya bostäder hittade"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_FROM, email_pass)
    server.send_message(msg)
    server.quit()




def main():
    data = fetch_data()
    seen = load_seen()
    filtered = filter_bostader(data)
    new_items, seen = get_new(filtered, seen)
    send_mail(new_items)
    save_seen(seen)


if __name__ == "__main__":
    main()