from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pickle
import os
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
import psycopg2  # Usar psycopg2 específicamente para este endpoint
from app.config import DB_CONFIG

router = APIRouter()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Rutas para el modelo, scaler y features
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
MODEL_PATH = os.path.join(MODELS_DIR, 'model_rf.pkl')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler_rf.pkl')
FEATURES_PATH = os.path.join(MODELS_DIR, 'model_features.json')

model = None
scaler = None
feature_columns = None

def load_model():
    # Carga el modelo, scaler y features
    global model, scaler, feature_columns
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        with open(FEATURES_PATH, 'r', encoding='utf-8') as f:
            import json
            feature_columns = json.load(f)
        logger.info(f"Modelo cargado desde {MODEL_PATH}")
        logger.info(f"Scaler cargado desde {SCALER_PATH}")
        logger.info(f"Features cargadas desde {FEATURES_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error al cargar el modelo: {e}")
        return False

# Cargar modelo al importar
load_model()

# Leer las features desde el archivo JSON para crear el modelo dinámicamente
import json
from typing import Optional
from pydantic import BaseModel, Field

with open(os.path.join(os.path.dirname(__file__), '..', 'models', 'model_features.json'), 'r', encoding='utf-8') as f:
    FEATURES_LIST = json.load(f)

# Crear el modelo MovieInput dinámicamente
attrs = {
    feat: (Optional[float], Field(0.0, description=feat)) for feat in FEATURES_LIST
}
attrs['titulo'] = (str, Field(..., description="Título de la película"))

MovieInput = type('MovieInput', (BaseModel,), {
    '__annotations__': {k: v[0] for k, v in attrs.items()},
    **{k: v[1] for k, v in attrs.items()},
    'model_config': {
        "json_schema_extra": {
            "example": {
                        "Action": 1,
                        "Adventure": 1,
                        "Animation": 0,
                        "Comedy": 0,
                        "Crime": 0,
                        "Documentary": 0,
                        "Drama": 1,
                        "Family": 1,
                        "Fantasy": 1,
                        "History": 0,
                        "Horror": 0,
                        "Music": 0,
                        "Mystery": 0,
                        "Romance": 0,
                        "Science Fiction": 1,
                        "TV Movie": 0,
                        "Thriller": 0,
                        "War": 0,
                        "Western": 0,
                        "adult_False": 1,
                        "adult_True": 0,
                        "budget": 460000000,
                        "duracion": 192,
                        "has_true_overview": 1,
                        "has_true_tagline": 1,
                        "in_collection": 1,
                        "num_production_companies": 3,
                        "num_production_countries": 1,
                        "num_spoken_languages": 2,
                        "original_language_en": 1,
                        "original_language_es": 0,
                        "original_language_fr": 0,
                        "original_language_ja": 0,
                        "popularity": 85.0,
                        "production_companies_20THCENTURYFOX": 0,
                        "production_companies_LIGHTSTORMENTERTAINMENT": 1,
                        "production_companies_20THCENTURYSTUDIOS": 1,
                        "production_companies_TSGENTERTAINMENT": 1,
                        "production_companies_UNIVERSALPICTURES": 0,
                        "production_companies_WARNERBROS.PICTURES": 0,
                        "production_countries_UNITEDSTATESOFAMERICA": 1,
                        "spoken_languages_ENGLISH": 1,
                        "spoken_languages_NA'VI": 1,
                        "status_Released": 1,
                        "titulo": "Avatar: The Way of Water",
                        "true_budget": 460000000,
                        "true_overview_len": 248,
                        "true_revenue": 2320000000,
                        "true_tagline_len": 26,
                        "vote_count": 11000
                        }

        }
    }
})

class PredictionResponse(BaseModel):
    # Modelo de respuesta para predicción
    titulo: str
    probabilidad_exito: float
    prediccion: str
    confianza: str
    success: bool


@router.post("/predict", response_model=PredictionResponse)
async def predict_movie_success(movie_data: MovieInput):

    """
    Endpoint que predice la probabilidad de éxito de una película basandose en las features requeridas por el modelo.
    Si falta alguna de las features requeridas se rellenan automaticamente con ceros.

    Devuelve JSON estructurado.
    """
        
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Modelo no disponible. Por favor, contacte al administrador."
        )
    try:
        # Extraer las features en el orden correcto
        X = [[getattr(movie_data, feat, 0.0) for feat in FEATURES_LIST]]
        # Escalar si corresponde
        if scaler is not None:
            X = scaler.transform(X)
        probabilidad_array = model.predict_proba(X)
        probabilidad = float(probabilidad_array[0][1])
        # Interpretar la probabilidad
        if probabilidad >= 0.7:
            prediccion = "Alto potencial de éxito"
            confianza = "Alta"
        elif probabilidad >= 0.5:
            prediccion = "Potencial moderado de éxito"
            confianza = "Media"
        elif probabilidad >= 0.3:
            prediccion = "Bajo potencial de éxito"
            confianza = "Media"
        else:
            prediccion = "Muy bajo potencial de éxito"
            confianza = "Alta"
        return PredictionResponse(
            titulo=movie_data.titulo,
            probabilidad_exito=round(probabilidad, 3),
            prediccion=prediccion,
            confianza=confianza,
            success=True
        )
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la predicción: {str(e)}"
        )

@router.get("/predict/health")
async def check_model_health():
    # Verifica el estado del modelo de predicción
    if model is None:
        return {
            "status": "error",
            "message": "Modelo no cargado",
            "model_available": False
        }
    
    return {
        "status": "ok", 
        "message": "Modelo de éxito cargado correctamente",
        "model_available": True,
        "model_path": MODEL_PATH
    }
