from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.endpoints import ask_text, ask_visual, predict

app = FastAPI(
    title="Movie Database API",
    description="""
API DE BASE DE DATOS DE PELÍCULAS (TMDB)

Esta API permite consultar una base de datos de películas usando lenguaje natural en español y generar visualizaciones automáticas.

FUNCIONALIDADES PRINCIPALES:
- /ask-text-html: Convierte preguntas en español a consultas SQL y devuelve respuestas formateadas.
- /ask-text: Devuelve respuestas crudas en JSON.
- /ask-visual: Genera gráficos automáticos basados en preguntas sobre películas.
- /predict: Predice la probabilidad de éxito de una película basándose en sus características.

TECNOLOGÍAS UTILIZADAS:
- FastAPI para la API REST
- Gemini (Google Generative AI) para NL2SQL
- PostgreSQL en AWS RDS
- Matplotlib/Seaborn para visualizaciones
"""
)

# Añadir los endpoints principales
app.include_router(ask_text.router, tags=["Text QA"])
app.include_router(ask_visual.router, tags=["Visual QA"])
app.include_router(predict.router, tags=["Predicción ML"])

@app.get("/", response_class=HTMLResponse, tags=["Info"])
async def root():
    """
    Página principal de la API con navegación
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie Database API</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; 
                margin: 0 auto; 
                background: white; 
                color: #333;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .nav-card { 
                background: #f8f9fa; 
                padding: 20px; 
                margin: 20px 0; 
                border-radius: 12px; 
                border-left: 5px solid #1976d2;
                transition: transform 0.2s;
            }
            .nav-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .nav-card h3 {
                margin-top: 0;
                color: #1976d2;
            }
            a { 
                color: #1976d2; 
                text-decoration: none; 
                font-weight: 500;
            }
            a:hover { 
                text-decoration: underline; 
            }
            .docs-section {
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid #eee;
            }
            .docs-link {
                display: inline-block;
                margin: 0 15px;
                padding: 15px 30px;
                background: #1976d2;
                color: white;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: background 0.3s;
            }
            .docs-link:hover {
                background: #1565c0;
                color: white;
            }
            .version {
                text-align: center;
                color: #666;
                font-size: 14px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Movie Database API</h1>
                <p>Consultas en lenguaje natural para base de datos de películas</p>
            </div>
            
            <div class="nav-card">
                <h3>Prueba la API</h3>
                <p>Ejemplos interactivos listos para usar</p>
                <a href="/demo">→ Ver ejemplos y demos</a>
            </div>
            
            <div class="nav-card">
                <h3>Endpoints disponibles</h3>
                <p><strong>/ask-text</strong> - Consultas con respuestas HTML/JSON<br>
                   <strong>/ask-visual</strong> - Gráficos automáticos<br>
                   <strong>/predict</strong> - Predicciones ML</p>
            </div>
            
            <div class="nav-card">
                <h3>Tecnologías</h3>
                <p>FastAPI • PostgreSQL • Matplotlib • Seaborn • scikit-learn • Google Gemini AI • AWS RDS • Conda</p>
            </div>
            
            <div class="docs-section">
                <a href="/docs" class="docs-link">Documentación Swagger</a>
                <a href="/redoc" class="docs-link">Documentación ReDoc</a>
            </div>
            
            <div class="version">
                <p>Movie Database API v2.0.0 | Powered by FastAPI</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health", tags=["Info"])
async def health_check():
    # Verificación de estado de la API
    return {"status": "healthy", "message": "API funcionando correctamente"}

@app.get("/demo", response_class=HTMLResponse, tags=["Info"])
async def demo_page():
    """
    Página de demostración interactiva
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie API Demo</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                color: #333;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .example-list {
                display: flex;
                flex-wrap: wrap;
                gap: 30px;
                justify-content: center;
                margin-bottom: 40px;
            }
            .example-card {
                background: #f8f9fa;
                border-left: 5px solid #1976d2;
                border-radius: 12px;
                padding: 25px 30px;
                min-width: 260px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                font-size: 16px;
            }
            .example-card h3 {
                margin-top: 0;
                color: #1976d2;
                font-size: 18px;
            }
            a {
                color: #1976d2;
                text-decoration: none;
                font-weight: 500;
            }
            a:hover {
                text-decoration: underline;
            }
            .json-sample {
                background: #222;
                color: #fff;
                padding: 10px;
                border-radius: 6px;
                overflow-x: auto;
                font-size: 15px;
                margin-top: 10px;
            }
            .docs-section {
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 2px solid #eee;
            }
            .docs-link {
                display: inline-block;
                margin: 0 15px;
                padding: 15px 30px;
                background: #1976d2;
                color: white;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: background 0.3s;
            }
            .docs-link:hover {
                background: #1565c0;
                color: white;
            }
            .version {
                text-align: center;
                color: #666;
                font-size: 14px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Movie Database API - Demo Interactiva</h1>
                <p>Prueba ejemplos reales de consultas, visualizaciones y predicción ML.</p>
            </div>
            <div class="example-list">
                <div class="example-card">
                    <h3>Consulta de Texto (HTML)</h3>
                    <a href="/ask-text-html?question=¿Películas de drama más populares?" target="_blank">¿Películas de drama más populares?</a><br>
                    <a href="/ask-text-html?question=¿Qué géneros existen?" target="_blank">¿Qué géneros existen?</a><br>
                    <a href="/ask-text-html?question=¿Películas con mayor presupuesto?" target="_blank">¿Películas con mayor presupuesto?</a>
                </div>
                <div class="example-card">
                    <h3>Visualizaciones Automáticas</h3>
                    <a href="/ask-visual?question=¿Distribución de géneros?&format=image" target="_blank">¿Distribución de géneros? (Gráfico)</a><br>
                    <a href="/ask-visual?question=¿Top 10 películas populares?&format=image" target="_blank">¿Top 10 películas populares? (Gráfico)</a>
                </div>
                <div class="example-card">
                    <h3>Predicción de Éxito (ML)</h3>
                    <span>POST a <b>/predict</b> con el siguiente JSON de ejemplo:</span>
                    <div class="json-sample">{
  "budget": 10000000,
  "popularity": 50.2,
  "vote_average": 7.5,
  "vote_count": 1200,
  "release_date": "2025-08-08",
  "duracion": 120,
  "revenue": 30000000,
  "generos": "Action, Adventure",
  "overview": "Una película de acción emocionante."
}</div>
                    <span>Prueba en <a href="/docs" target="_blank">Swagger UI</a> o con tu herramienta favorita.</span>
                </div>
            </div>
            <div class="docs-section">
                <a href="/" class="docs-link">Volver a Inicio</a>
                <a href="/docs" class="docs-link">Documentación Swagger</a>
                <a href="/redoc" class="docs-link">Documentación ReDoc</a>
            </div>
            <div class="version">
                <p>Movie Database API v2.0.0 | Powered by FastAPI</p>
            </div>
        </div>
    </body>
    </html>
    """

