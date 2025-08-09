# Documentación de la API

La página principal de la API muestra de forma visual los endpoints disponibles, las tecnologías utilizadas y ofrece acceso directo a ejemplos reales de uso.

## Endpoints Detallados

### 1. /ask-text-html (GET)
**Propósito**: Consultas en lenguaje natural con respuesta HTML formateada.

**Parámetros:**
- `question` (string, requerido): Pregunta sobre películas en español

**Ejemplo:**
```bash
GET /ask-text-html?question=¿Top 5 películas mejor valoradas?
```

**Respuesta:**
- HTML visual con colores y estilos.

---

### 2. /ask-text (POST)
**Propósito**: Consultas en lenguaje natural con respuesta JSON estructurada.

**Payload:**
```json
{
  "question": "¿Cuántas películas de comedia hay?"
}
```

**Respuesta ejemplo:**
```json
{
  "datos": [...],
  "sql": "SELECT ...",
  "metadata": {...}
}
```

---

### 3. /ask-visual (GET y POST)
**Propósito**: Generación automática de gráficos o datos visuales.

**Parámetros:**
- `question` (string, requerido): Pregunta para visualizar
- `format` (string, opcional): "image" o "json"

**Ejemplo GET:**
```bash
GET /ask-visual?question=¿Distribución de géneros?&format=image
```

**Ejemplo POST:**
```json
{
  "question": "¿Distribución de películas por año?"
}
```

**Respuesta ejemplo (image):**
```json
{
  "success": true,
  "image_base64": "..."
}
```


---


### 4. /predict (POST)
**Propósito**: Predicción de éxito de una película usando ML.

**Payload ejemplo:**
```json
{
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
```

**Respuesta ejemplo:**
```json
{
  "probabilidad_exito": 0.87,
  "success": true
}
```

---

### 5. /predict/health (GET)
**Propósito**: Verifica si el modelo de Machine Learning está cargado y disponible para predicciones.

**Respuesta ejemplo:**
```json
{
  "status": "ok",
  "message": "Modelo de éxito cargado correctamente",
  "model_available": true,
  "model_path": "app/models/model_rf.pkl"
}
```

---

### 6. /health (GET)
**Propósito**: Verificar el estado general de la API.

**Respuesta ejemplo:**
```json
{
  "status": "healthy",
  "message": "API funcionando correctamente"
}
```

---

### 7. /demo (GET)
**Propósito**: Página HTML de demostración con ejemplos de uso.


## Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos

### Base de Datos
- **PostgreSQL**: Base de datos relacional en AWS RDS
- **psycopg2**: Driver de PostgreSQL para Python

### Machine Learning & NLP
- **Google Gemini AI**: Conversión de lenguaje natural a SQL
- **scikit-learn**: Modelo de predicción de éxito
- **Deep Translator**: Soporte multiidioma

### Visualización
- **Matplotlib**: Generación de gráficos estáticos
- **Seaborn**: Visualizaciones estadísticas avanzadas
- **Pandas/Numpy**: Manipulación y análisis de datos

### Cloud & DevOps
- **AWS EC2**: Hosting de la aplicación
- **AWS RDS**: Base de datos PostgreSQL
- **AWS Secrets Manager**: Gestión segura de credenciales
- **Conda**: Gestión de entornos y dependencias

---

## Base de Datos

### Esquema
```sql
-- Tabla de películas
peliculas (
  movie_id integer NOT NULL,
  titulo text NOT NULL,
  release_date date,
  duracion integer,
  vote_average numeric(3,1),
  vote_count integer,
  origin_country text,
  overview text,
  revenue bigint,
  budget bigint,
  adult boolean,
  belong_to_collection character varying(1000),
  original_language character varying,
  original_title character varying(500),
  popularity double precision,
  production_companies text,
  production_countries text,
  spoken_languages text,
  status character varying,
  tagline character varying(1000),
  CONSTRAINT peliculas_pkey PRIMARY KEY (movie_id)
);

-- Tabla de géneros
generos (
  genero_id integer NOT NULL,
  nombre character varying(50) NOT NULL,
  CONSTRAINT generos_pkey PRIMARY KEY (genero_id)
);

-- Relación muchos a muchos
peliculas_generos (
  movie_id INT REFERENCES peliculas(movie_id),
  genero_id INT REFERENCES generos(genero_id)
);
```

### Datos disponibles
- **~50,000+ películas** con metadata completa
- **19 géneros** cinematográficos
- **Ratings y popularidad** de TMDB
- **Información financiera** (presupuesto, recaudación)

---

## URLs de Acceso

Una vez desplegado, la API estará disponible en:

```
# Documentación interactiva
http://TU-DOMINIO:8000/docs

# Documentación alternativa
http://TU-DOMINIO:8000/redoc

# Endpoints principales
http://TU-DOMINIO:8000/ask-text
http://TU-DOMINIO:8000/ask-visual  
http://TU-DOMINIO:8000/predict
```

---

## Códigos de Respuesta

- **200**: Operación exitosa
- **400**: Error en parámetros de entrada
- **422**: Error de validación de datos
- **500**: Error interno del servidor
- **503**: Servicio no disponible (modelo ML no cargado)

---

## Limitaciones

- **Idioma**: Optimizado para consultas en español (pero técnicamente podría responder preguntas en inglés gracias a Gemini AI)
- **Dominio**: Especializada en películas y entretenimiento
- **Modelo ML**: Entrenado con datos hasta 2025
- **Visualizaciones**: Limitadas a tipos de gráfico predefinidos