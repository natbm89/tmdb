import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.dirname(__file__)

def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 1. Test /ask-text
ask_text_payload = {"question": "¿Cuántas películas hay de comedia?"}
resp1 = requests.post(f"{BASE_URL}/ask-text", json=ask_text_payload)
print("/ask-text status:", resp1.status_code)
save_json("ask_text_response.json", resp1.json())

# 2. Test /ask-visual
ask_visual_payload = {"question": "¿Distribución de películas por año?"}
resp2 = requests.post(f"{BASE_URL}/ask-visual", json=ask_visual_payload)
print("/ask-visual status:", resp2.status_code)
save_json("ask_visual_response.json", resp2.json())

# 3. Test /predict
predict_payload = {
    "titulo": "Avatar: The Way of Water",
    "budget": 460000000,
    "duracion": 192,
    "popularity": 85.0,
    "vote_count": 11000,
    "true_revenue": 2320000000,
    "true_budget": 460000000,
    "true_overview_len": 248,
    "has_true_overview": 1,
    "true_tagline_len": 26,
    "has_true_tagline": 1,
    "in_collection": 1,
    "Action": 1,
    "Adventure": 1,
    "Drama": 1,
    "Family": 1,
    "Fantasy": 1,
    "Science Fiction": 1,
    "adult_False": 1,
    "adult_True": 0,
    "original_language_en": 1,
    "spoken_languages_ENGLISH": 1,
    "status_Released": 1,
    "num_production_companies": 3,
    "num_production_countries": 1,
    "num_spoken_languages": 2,
    "production_countries_UNITEDSTATESOFAMERICA": 1
}
resp3 = requests.post(f"{BASE_URL}/predict", json=predict_payload)
print("/predict status:", resp3.status_code)
save_json("predict_response.json", resp3.json())

print("Respuestas guardadas en la carpeta tests.")
