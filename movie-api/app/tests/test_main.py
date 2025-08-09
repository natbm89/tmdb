from fastapi.testclient import TestClient
from app.main import app
import os
from datetime import datetime

client = TestClient(app)

def log_test_result(test_name, response):
    log_path = os.path.join(os.path.dirname(__file__), 'test_results.log')
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {test_name}: status={response.status_code}, response={response.json()}\n")

# Test para el endpoint ask-text con el metodo POST
def test_ask_text_post():
    payload = {"question": "¿Cuántas películas hay de comedia?"}
    response = client.post("/ask-text", json=payload)
    log_test_result("test_ask_text_post", response)
    assert response.status_code == 200
    assert "datos" in response.json() or "respuesta" in response.json()

# Test para el endpoint ask-visual con el metodo POST
def test_ask_visual_post():
    payload = {"question": "¿Distribución de películas por año?"}
    response = client.post("/ask-visual", json=payload)
    log_test_result("test_ask_visual_post", response)
    assert response.status_code == 200
    assert "success" in response.json() or "error" in response.json()

# Test para el endpoint predict con el metodo POST
def test_predict_post():
    payload = {
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
    response = client.post("/predict", json=payload)
    log_test_result("test_predict_post", response)
    assert response.status_code == 200
    assert "probabilidad_exito" in response.json() or "success" in response.json()
