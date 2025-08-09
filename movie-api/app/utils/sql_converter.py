
import google.generativeai as genai
import re
import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
print(f"API Key detectada: {'Sí' if GEMINI_API_KEY else 'No'}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini configurado correctamente")
else:
    print("GEMINI_API_KEY no encontrada en variables de entorno")

# Modelo Gemini
GEMINI_MODEL = "gemini-1.5-flash"

def get_database_schema():
    # Retorna el esquema actualizado de la base de datos para el contexto de Gemini
    return """
    Base de datos de películas - Esquema actualizado:
    
    Tabla: peliculas
    - movie_id (INTEGER, PRIMARY KEY)
    - titulo (TEXT) - título de la película
    - release_date (DATE) - fecha de estreno
    - duracion (INTEGER) - duración en minutos
    - vote_average (NUMERIC(3,1)) - puntuación promedio (0-10)
    - vote_count (INTEGER) - número de votos
    - origin_country (TEXT) - país de origen
    - overview (TEXT) - sinopsis de la película
    - revenue (BIGINT) - recaudación en dólares
    - budget (BIGINT) - presupuesto en dólares
    - adult (BOOLEAN) - contenido para adultos
    - belong_to_collection (VARCHAR(1000)) - pertenece a colección
    - original_language (VARCHAR) - idioma original
    - original_title (VARCHAR(500)) - título original
    - popularity (DOUBLE PRECISION) - índice de popularidad
    - production_companies (TEXT) - compañías productoras
    - production_countries (TEXT) - países de producción
    - spoken_languages (TEXT) - idiomas hablados
    - status (VARCHAR) - estado de la película
    - tagline (VARCHAR(1000)) - eslogan de la película
    
    Tabla: generos  
    - genero_id (INTEGER, PRIMARY KEY)
    - nombre (VARCHAR(50)) - nombre del género (Comedy, Action, Drama, etc.)
    
    Tabla: peliculas_generos (tabla de unión)
    - movie_id (INTEGER, FOREIGN KEY -> peliculas.movie_id)
    - genero_id (INTEGER, FOREIGN KEY -> generos.genero_id)
    """

def generate_sql_with_gemini(question: str, schema: str) -> Optional[str]:
    # Genera SQL usando Gemini AI
    if not GEMINI_API_KEY:
        return None
        
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""
        Eres un experto en SQL para PostgreSQL. Tu tarea es convertir preguntas en lenguaje natural a consultas SQL válidas.

        ESQUEMA DE BASE DE DATOS:
        {schema}

        REGLAS IMPORTANTES:
        1. Usa SOLO las tablas y columnas mencionadas en el esquema
        2. Para filtros por género, SIEMPRE usa JOIN con las tablas generos y peliculas_generos
        3. Usa LIMIT para controlar el número de resultados (máximo 20)
        4. Para fechas, usa EXTRACT(YEAR FROM release_date) para obtener el año
        5. IMPORTANTE: Para contar películas por género usa COUNT(*) desde peliculas_generos con JOIN a generos
        6. Ordena por campos relevantes según el contexto:
           - Para valoraciones: vote_average DESC
           - Para popularidad: popularity DESC o vote_count DESC
           - Para presupuesto: budget DESC
           - Para recaudación: revenue DESC
           - Para duración: duracion DESC
        7. SIEMPRE incluye las columnas relevantes en SELECT:
           - Para presupuesto: titulo, budget
           - Para valoraciones: titulo, vote_average
           - Para popularidad: titulo, popularity o vote_count
           - Para recaudación: titulo, revenue
           - Para duración: titulo, duracion
           - Para año: titulo, EXTRACT(YEAR FROM release_date) as año
        8. Usa filtros apropiados:
           - budget > 0 para consultas de presupuesto
           - revenue > 0 para consultas de recaudación
           - vote_average IS NOT NULL para valoraciones
           - adult = false para contenido familiar
        9. Retorna SOLO la consulta SQL sin explicaciones adicionales
        10. La consulta debe terminar con punto y coma (;)

        PREGUNTA: {question}

        SQL:
        """
        
        response = model.generate_content(prompt)
        sql_query = response.text.strip()
        
        # Limpiar la respuesta si viene con markdown
        if sql_query.startswith('```sql'):
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        elif sql_query.startswith('```'):
            sql_query = sql_query.replace('```', '').strip()
            
        print(f"SQL generada por Gemini: {sql_query}")
        return sql_query
        
    except Exception as e:
        print(f"Error usando Gemini: {e}")
        return None

def extract_number(text):
    # Extrae número de la pregunta (ej: 'top 5' → 5)
    numbers = re.findall(r'\d+', text)
    return int(numbers[0]) if numbers else None

def create_better_fallback(question):
    # Crea consultas SQL más inteligentes como fallback usando la estructura de la BD
    question_lower = question.lower()
    
    if "mejor valorad" in question_lower or "rating" in question_lower or "highest rated" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, vote_average FROM peliculas WHERE vote_average IS NOT NULL ORDER BY vote_average DESC LIMIT {limit};"
    
    elif "popular" in question_lower or "más popular" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, popularity FROM peliculas WHERE popularity IS NOT NULL ORDER BY popularity DESC LIMIT {limit};"
    
    elif "votos" in question_lower or "más votad" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, vote_count FROM peliculas WHERE vote_count IS NOT NULL ORDER BY vote_count DESC LIMIT {limit};"
    
    elif "presupuesto" in question_lower or "budget" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, budget FROM peliculas WHERE budget > 0 ORDER BY budget DESC LIMIT {limit};"
    
    elif "recaudac" in question_lower or "revenue" in question_lower or "taquilla" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, revenue FROM peliculas WHERE revenue > 0 ORDER BY revenue DESC LIMIT {limit};"
    
    elif "duración" in question_lower or "duration" in question_lower or "larga" in question_lower or "corta" in question_lower:
        limit = extract_number(question) or 10
        if "corta" in question_lower:
            return f"SELECT titulo, duracion FROM peliculas WHERE duracion IS NOT NULL ORDER BY duracion ASC LIMIT {limit};"
        else:
            return f"SELECT titulo, duracion FROM peliculas WHERE duracion IS NOT NULL ORDER BY duracion DESC LIMIT {limit};"
    
    elif "año" in question_lower or "estreno" in question_lower or "year" in question_lower:
        limit = extract_number(question) or 10
        return f"SELECT titulo, EXTRACT(YEAR FROM release_date) as año FROM peliculas WHERE release_date IS NOT NULL ORDER BY release_date DESC LIMIT {limit};"
    
    elif "género" in question_lower or "genre" in question_lower:
        return "SELECT DISTINCT nombre FROM generos ORDER BY nombre;"
    
    else:
        limit = extract_number(question) or 10
        return f"SELECT titulo, vote_average FROM peliculas WHERE vote_average IS NOT NULL ORDER BY vote_average DESC LIMIT {limit};"

def is_valid_sql(sql_query):
    # Valida si la SQL es correcta
    if not sql_query or len(sql_query.strip()) < 5:
        return False
    
    sql_upper = sql_query.upper().strip()
    
    # Debe empezar con SELECT
    if not sql_upper.startswith('SELECT'):
        return False
    
    # No debe tener fragmentos incompletos
    invalid_patterns = [
        'UP BY',  
        'ORDER BY;',
        'SELECT;',
        'WHERE;',
        'FROM;'
    ]
    
    for pattern in invalid_patterns:
        if pattern in sql_upper:
            return False
    
    return True

def clean_sql_output(sql_raw):
    # Limpia la salida del modelo
    sql_query = sql_raw.strip()
    
    # Si no empieza con SELECT, buscar SELECT en la cadena
    if not sql_query.upper().startswith('SELECT'):
        if 'SELECT' in sql_query.upper():
            select_pos = sql_query.upper().find('SELECT')
            sql_query = sql_query[select_pos:]
        else:
            return ""
    
    # Asegurar que termine con punto y coma
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    return sql_query

def post_process_sql(sql_query):
    # Adapta la SQL generada a tu esquema real y la limpia
    sql_query = clean_sql_output(sql_query)
    
    if not sql_query:
        return ""
    
    # Mapeo de nombres comunes
    mappings = {
        r'\bmovies\b': 'peliculas',
        r'\bfilms\b': 'peliculas',
        r'\btitle\b': 'titulo',
        r'\btitles\b': 'titulo',
        r'\breleased\b': 'release_date',
        r'\byear\b': 'EXTRACT(YEAR FROM release_date)',
        r'\bgenres\b': 'generos',
        r'\bgenre\b': 'generos',
        r'\bname\b': 'nombre',
        r'\brating\b': 'vote_average',
        r'\bscore\b': 'vote_average',
        r'\bbudget\b': 'budget',
        r'\brevenue\b': 'revenue',
        r'\bpopularity\b': 'popularity',
        r'\bvotes\b': 'vote_count',
        r'\bvotos\b': 'vote_count',
        r'\bduration\b': 'duracion',
        r'\bruntime\b': 'duracion',
        r'\boverview\b': 'overview',
        r'\bsinopsis\b': 'overview'
    }
    
    for pattern, replacement in mappings.items():
        sql_query = re.sub(pattern, replacement, sql_query, flags=re.IGNORECASE)
    
    return sql_query

def generate_sql(question, tables_dict=None):
    print("Pregunta recibida:", question)

    # Enviar la pregunta directamente en español a Gemini
    if GEMINI_API_KEY:
        print("Intentando generar SQL con Gemini...")
        schema = get_database_schema()
        gemini_sql = generate_sql_with_gemini(question, schema)

        if gemini_sql and is_valid_sql(gemini_sql):
            print("SQL válida generada por Gemini")
            return gemini_sql
        else:
            print("Gemini no pudo generar SQL válida, usando fallbacks...")
    else:
        print("Gemini no disponible (falta API key), usando fallbacks...")

    # OPCIÓN 2: Intentar fallback inteligente para preguntas comunes
    fallback_result = generate_fallback_sql(question, question)
    if "JOIN" in fallback_result or "WHERE" in fallback_result or "GROUP BY" in fallback_result or "ORDER BY" in fallback_result:
        print("Usando fallback inteligente especializado")
        return fallback_result

    # OPCIÓN 3: Fallback simple si todo lo demás falla
    print("Usando fallback simple...")
    smart_fallback = create_better_fallback(question)
    print(f"Fallback final: {smart_fallback}")
    return smart_fallback

def generate_fallback_sql(question_en, original_question=""):
    # Genera SQL usando patrones para preguntas comunes
    question_lower = question_en.lower()
    original_lower = original_question.lower()
    
    # Usar la pregunta original si está disponible para detectar mejor los patrones
    combined_question = (question_lower + " " + original_lower).lower()
    
    if "titles" in question_lower and ("2023" in question_lower or "released" in question_lower):
        return "SELECT titulo FROM peliculas WHERE EXTRACT(YEAR FROM release_date) = 2023;"
    
    # Distribución de géneros
    elif ("distribución" in combined_question or "distribution" in question_lower) and ("género" in combined_question or "genres" in question_lower):
        return """
        SELECT g.nombre, COUNT(DISTINCT pg.movie_id) as cantidad_peliculas
        FROM generos g 
        LEFT JOIN peliculas_generos pg ON g.genero_id = pg.genero_id 
        GROUP BY g.nombre 
        ORDER BY cantidad_peliculas DESC
        LIMIT 10;
        """
    
    # Contar películas por género específico
    elif ("cuántas" in combined_question or "cuantas" in combined_question or "how many" in question_lower) and ("película" in combined_question or "movie" in question_lower):
        # Detectar el género en la pregunta
        genre_mapping = {
            "comedy": "Comedy",
            "comedia": "Comedy",
            "action": "Action",
            "acción": "Action",
            "drama": "Drama",
            "horror": "Horror",
            "terror": "Horror",
            "thriller": "Thriller",
            "romance": "Romance",
            "romántica": "Romance",
            "adventure": "Adventure",
            "aventura": "Adventure",
            "animation": "Animation",
            "animación": "Animation",
            "documentary": "Documentary",
            "documental": "Documentary",
            "fantasy": "Fantasy",
            "fantasía": "Fantasy",
            "science fiction": "Science Fiction",
            "ciencia ficción": "Science Fiction",
            "sci-fi": "Science Fiction",
            "mystery": "Mystery",
            "misterio": "Mystery",
            "crime": "Crime",
            "crimen": "Crime",
            "war": "War",
            "guerra": "War",
            "western": "Western",
            "family": "Family",
            "familiar": "Family",
            "music": "Music",
            "música": "Music",
            "history": "History",
            "historia": "History",
            "tv movie": "TV Movie"
        }
        detected_genre = None
        for keyword, genre in genre_mapping.items():
            if keyword in combined_question:
                detected_genre = genre
                break
        if detected_genre:
            return f"""
            SELECT COUNT(*) as total_peliculas
            FROM peliculas_generos pg
            JOIN generos g ON pg.genero_id = g.genero_id 
            WHERE g.nombre = '{detected_genre}';
            """
    
    # Top géneros por popularidad
    elif ("genres" in question_lower or "géneros" in combined_question) and ("top" in question_lower or "popular" in question_lower):
        return """
        SELECT g.nombre, COUNT(pg.movie_id) as total_peliculas, 
               AVG(p.vote_count) as popularidad_promedio
        FROM generos g 
        LEFT JOIN peliculas_generos pg ON g.genero_id = pg.genero_id 
        LEFT JOIN peliculas p ON pg.movie_id = p.movie_id
        GROUP BY g.nombre 
        ORDER BY popularidad_promedio DESC 
        LIMIT 5;
        """
    
    # Solo lista de géneros
    elif ("genres" in question_lower or "géneros" in combined_question) and not ("distribución" in combined_question or "distribution" in question_lower):
        return "SELECT nombre FROM generos ORDER BY nombre;"
    elif "available" in question_lower:
        return "SELECT nombre FROM generos ORDER BY nombre;"
    
    # Películas mejor valoradas
    elif ("mejor valorad" in combined_question or "highest rated" in question_lower or "best rated" in question_lower or "better" in question_lower) and ("score" in question_lower or "rating" in question_lower):
        limit = extract_number(original_question or question_en) or 10
        return f"SELECT titulo, vote_average FROM peliculas WHERE vote_average IS NOT NULL ORDER BY vote_average DESC LIMIT {limit};"
    
    elif "budget" in question_lower or "presupuesto" in combined_question:
        limit = extract_number(original_question or question_en) or 10
        return f"SELECT titulo, budget FROM peliculas WHERE budget > 0 ORDER BY budget DESC LIMIT {limit};"
    
    elif "top" in question_lower and "popularity" in question_lower:
        limit = extract_number(original_question or question_en) or 5
        return f"SELECT titulo, popularity FROM peliculas WHERE popularity IS NOT NULL ORDER BY popularity DESC LIMIT {limit};"
    
    # Detectar géneros específicos
    genre_mapping = {
        "comedy": "Comedy",
        "comedia": "Comedy",
        "action": "Action",
        "acción": "Action",
        "drama": "Drama",
        "horror": "Horror",
        "terror": "Horror",
        "thriller": "Thriller",
        "romance": "Romance",
        "romántica": "Romance",
        "adventure": "Adventure",
        "aventura": "Adventure",
        "animation": "Animation",
        "animación": "Animation",
        "documentary": "Documentary",
        "documental": "Documentary",
        "fantasy": "Fantasy",
        "fantasía": "Fantasy",
        "science fiction": "Science Fiction",
        "ciencia ficción": "Science Fiction",
        "sci-fi": "Science Fiction",
        "mystery": "Mystery",
        "misterio": "Mystery",
        "crime": "Crime",
        "crimen": "Crime",
        "war": "War",
        "guerra": "War",
        "western": "Western",
        "family": "Family",
        "familiar": "Family",
        "music": "Music",
        "música": "Music",
        "history": "History",
        "historia": "History",
        "tv movie": "TV Movie"
    }
    
    # Buscar si algún género está mencionado en la pregunta
    detected_genre = None
    for keyword, genre in genre_mapping.items():
        if keyword in combined_question:
            detected_genre = genre
            break
    
    # Películas por género específico
    if detected_genre:
        return f"""
        SELECT p.titulo, p.vote_average, p.vote_count 
        FROM peliculas p 
        LEFT JOIN peliculas_generos pg ON p.movie_id = pg.movie_id 
        LEFT JOIN generos g ON pg.genero_id = g.genero_id 
        WHERE g.nombre = '{detected_genre}'
        ORDER BY p.vote_count DESC 
        LIMIT 10;
        """
    
    # Fallback inteligente basado en la pregunta original
    if original_question:
        return create_better_fallback(original_question)
    
    # Fallback por defecto
    return "SELECT titulo FROM peliculas ORDER BY vote_average DESC LIMIT 10;"