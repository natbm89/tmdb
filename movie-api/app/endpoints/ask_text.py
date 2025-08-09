from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.utils.sql_converter import generate_sql
from app.models.sql_predictor import execute_sql
import re

router = APIRouter()

SCHEMA = {
    "peliculas": ["movie_id", "titulo", "release_date", "duracion", "vote_average", "vote_count", "origin_country", "overview", "revenue", "budget"],
    "generos": ["genero_id", "nombre"],
    "peliculas_generos": ["movie_id", "genero_id"]
}

def results_to_html(results, question=""):
    # Convierte los resultados a HTML
    if results is None or results == 0:
        return """
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #ffebee; border: 1px solid #f44336; border-radius: 8px;">
            <h3 style="color: #d32f2f; margin: 0;">No se encontraron resultados</h3>
        </div>
        """
    
    # Caso especial para consultas de conteo (COUNT)
    if isinstance(results, list) and len(results) == 1 and isinstance(results[0], tuple) and len(results[0]) == 1:
        count_value = results[0][0]
        if isinstance(count_value, (int, float)) and ("cuántas" in question.lower() or "cuantas" in question.lower() or "count" in question.lower()):
            if "comedia" in question.lower() or "comedy" in question.lower():
                count_text = f"Total de películas de comedia: {count_value:,}"
            elif "acción" in question.lower() or "action" in question.lower():
                count_text = f"Total de películas de acción: {count_value:,}"
            elif "drama" in question.lower():
                count_text = f"Total de películas de drama: {count_value:,}"
            elif "género" in question.lower() or "genero" in question.lower():
                count_text = f"Total de películas del género solicitado: {count_value:,}"
            elif "película" in question.lower() or "pelicula" in question.lower():
                count_text = f"Total de películas: {count_value:,}"
            else:
                count_text = f"Total encontrado: {count_value:,}"
            
            return f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #4caf5015, #4caf5005); padding: 20px; border-radius: 12px; border-left: 4px solid #4caf50;">
                    <h2 style="color: #4caf50; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">
                        RESULTADO DE CONTEO
                    </h2>
                    <p style="color: #666; margin: 0; font-size: 14px;">
                        Consulta de cantidad ejecutada
                    </p>
                </div>
                
                <div style="background: white; margin-top: 20px; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                    <div style="font-size: 48px; font-weight: 700; color: #2e7d32; margin-bottom: 10px;">
                        {count_value:,}
                    </div>
                    <div style="font-size: 18px; color: #555; font-weight: 500;">
                        {count_text.split(': ')[0] if ': ' in count_text else count_text}
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                    <p>Movie API | Pregunta: "{question}"</p>
                </div>
            </div>
            """
    
    # Limita a los primeros 20 resultados
    max_items = 20
    if isinstance(results, list):
        items_html = []
        
        for i, r in enumerate(results[:max_items], 1):
            if isinstance(r, tuple):
                if len(r) == 1:
                    # Solo un campo (ej: título, género)
                    items_html.append(f"<li>{r[0]}</li>")
                elif len(r) == 2:
                    if isinstance(r[1], (int, float)):
                        # Detectar por contexto de la pregunta
                        if "presupuesto" in question.lower() or "budget" in question.lower():
                            if r[1] >= 1000000:  # Millones
                                millions = r[1] / 1000000
                                items_html.append(f"<li>{r[0]} <span style='color: #2e7d32; font-weight: 600;'>${millions:.0f}M</span></li>")
                            elif r[1] > 0:
                                items_html.append(f"<li>{r[0]} <span style='color: #2e7d32; font-weight: 600;'>${r[1]:,.0f}</span></li>")
                            else:
                                items_html.append(f"<li>{r[0]} <span style='color: #757575;'>Presupuesto no disponible</span></li>")
                        elif "rating" in question.lower() or "valorad" in question.lower() or "puntuac" in question.lower() or "mejor" in question.lower():
                            items_html.append(f"<li>{r[0]} <span style='color: #ff9800; font-weight: 600;'>{r[1]}/10</span></li>")
                        elif "popular" in question.lower() or "votos" in question.lower() or "vote" in question.lower():
                            # Formatear votos de manera más legible
                            if r[1] >= 1000000:
                                votes_formatted = f"{r[1]/1000000:.1f}M"
                            elif r[1] >= 1000:
                                votes_formatted = f"{r[1]/1000:.1f}K"
                            else:
                                votes_formatted = f"{r[1]:,}"
                            items_html.append(f"<li>{r[0]} <span style='color: #1976d2; font-weight: 600;'>{votes_formatted} votos</span></li>")
                        elif "revenue" in question.lower() or "recaudac" in question.lower():
                            if r[1] >= 1000000:
                                millions = r[1] / 1000000
                                items_html.append(f"<li>{r[0]} <span style='color: #388e3c; font-weight: 600;'>${millions:.0f}M recaudados</span></li>")
                            else:
                                items_html.append(f"<li>{r[0]} <span style='color: #388e3c; font-weight: 600;'>${r[1]:,.0f} recaudados</span></li>")
                        elif r[1] <= 10:
                            # Es probablemente un rating
                            rating = round(float(r[1]), 1)
                            items_html.append(f"<li>{r[0]} <span style='color: #ff9800; font-weight: 600;'>{rating}/10</span></li>")
                        elif r[1] > 1000000:
                            # Número muy grande, probablemente dinero o votos
                            if r[1] > 100000000:  # Más de 100M, probablemente votos
                                votes_formatted = f"{r[1]/1000000:.1f}M"
                                items_html.append(f"<li>{r[0]} <span style='color: #1976d2; font-weight: 600;'>{votes_formatted} votos</span></li>")
                            else:  # Probablemente dinero
                                millions = r[1] / 1000000
                                items_html.append(f"<li>{r[0]} <span style='color: #2e7d32; font-weight: 600;'>${millions:.0f}M</span></li>")
                        elif r[1] > 1000:
                            # Número mediano, formatear con comas o K
                            if r[1] > 10000:
                                formatted = f"{r[1]/1000:.1f}K"
                            else:
                                formatted = f"{int(r[1]):,}"
                            items_html.append(f"<li>{r[0]} <span style='color: #1976d2; font-weight: 600;'>{formatted}</span></li>")
                        else:
                            items_html.append(f"<li>{r[0]} <span style='color: #1976d2; font-weight: 600;'>{int(r[1]):,}</span></li>")
                    else:
                        items_html.append(f"<li>{r[0]} - {r[1]}</li>")
                elif len(r) == 3:
                    # Detectar el tipo de consulta por los valores
                    field1, field2, field3 = r[0], r[1], r[2]
                    
                    # Si es una consulta de géneros con total películas y rating promedio
                    if ("género" in question.lower() or "genre" in question.lower() or 
                        "mejor" in question.lower() and "rating" in question.lower()):
                        total_movies = int(field2) if isinstance(field2, (int, float)) else field2
                        # Redondeo más robusto para el rating promedio
                        try:
                            avg_rating = round(float(field3), 1)
                        except (ValueError, TypeError):
                            avg_rating = field3
                        items_html.append(f"<li>{field1} <span style='color: #1976d2; font-weight: 600;'>{total_movies:,} películas</span> <span style='color: #ff9800; font-weight: 600;'>{avg_rating}/10</span></li>")
                    else:
                        # Lógica original para rating + votos
                        rating = round(float(field2), 1) if isinstance(field2, (int, float)) and field2 <= 10 else field2
                        
                        if isinstance(field3, (int, float)) and field3 >= 1000000:
                            votes_formatted = f"{field3/1000000:.1f}M"
                        elif isinstance(field3, (int, float)) and field3 >= 1000:
                            votes_formatted = f"{field3/1000:.1f}K"
                        else:
                            votes_formatted = f"{int(field3):,}" if isinstance(field3, (int, float)) else field3
                        
                        items_html.append(f"<li>{field1} <span style='color: #ff9800; font-weight: 600;'>{rating}/10</span> <span style='color: #1976d2; font-weight: 600;'>{votes_formatted} votos</span></li>")
                else:
                    items_html.append(f"<li>{r[0]} - {r[1]}</li>")
            else:
                items_html.append(f"<li>{str(r)}</li>")
        
        # Determinar título y color basado en la pregunta
        if "género" in question.lower() or "genre" in question.lower():
            if "mejor" in question.lower() or "rating" in question.lower():
                title = f"Géneros con mejores ratings"
            else:
                title = f"Géneros disponibles"
            color = "#9c27b0"
        elif "presupuesto" in question.lower() or "budget" in question.lower():
            title = f"Películas por presupuesto"
            color = "#2e7d32"
        elif "revenue" in question.lower() or "recaudac" in question.lower():
            title = f"Películas por recaudación"
            color = "#388e3c"
        elif ("rating" in question.lower() or "valorad" in question.lower() or "mejor" in question.lower()) and "top" in question.lower():
            title = f"Top películas mejor valoradas"
            color = "#ff9800"
        elif "popular" in question.lower():
            title = f"Películas más populares"
            color = "#1976d2"
        elif "top" in question.lower():
            # Extraer número si existe
            import re
            number_match = re.search(r'top\s*(\d+)', question.lower())
            if number_match:
                num = number_match.group(1)
                title = f"Top {num} resultados"
            else:
                title = f"Top resultados"
            color = "#f57c00"
        else:
            # Usar parte de la pregunta como título
            clean_question = question.replace('?', '').replace('¿', '').strip()
            if len(clean_question) > 50:
                title = clean_question[:47] + "..."
            else:
                title = clean_question.title()
            color = "#616161"
        
        items_list = "\n".join(items_html)
        
        footer = ""
        if len(results) > max_items:
            footer = f"""
            <div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 6px; color: #1565c0;">
                <strong>Mostrando {len(items_html)} de {len(results)} resultados totales</strong>
            </div>
            """
        
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, {color}15, {color}05); padding: 20px; border-radius: 12px; border-left: 4px solid {color};">
                <h2 style="color: {color}; margin: 0 0 10px 0; font-size: 24px; font-weight: 600;">
                    {title}
                </h2>
                <p style="color: #666; margin: 0; font-size: 14px;">
                    {len(items_html)} resultado{'s' if len(items_html) != 1 else ''} encontrado{'s' if len(items_html) != 1 else ''}
                </p>
            </div>
            
            <div style="background: white; margin-top: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <ol style="padding-left: 20px; line-height: 1.8; font-size: 16px;">
                    {items_list}
                </ol>
                {footer}
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>Movie API | Pregunta: "{question}"</p>
            </div>
        </div>
        """
    
    return f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px;">
        <h3 style="color: #2e7d32; margin: 0;">Respuesta: {results}</h3>
    </div>
    """

def is_valid_sql(sql):
    return bool(re.match(r"(?i)^select\s.+\sfrom\s.+", sql.strip()))

class Question(BaseModel):
    question: str

# ENDPOINT PRINCIPAL: Respuesta como HTML
@router.get("/ask-text-html", response_class=HTMLResponse)
async def ask_text_simple(
    question: str = Query(
        ..., 
        description="Escribe tu pregunta sobre películas aquí",
        examples={"pregunta": {"summary": "Ejemplo", "value": "¿Cuáles son las 5 películas mejor valoradas?"}},
        min_length=5,
        max_length=200
    )
):
    """
    Responde preguntas sobre películas en HTML
    
    Ejemplos de preguntas válidas:
    - ¿Cuáles son las 5 películas mejor valoradas?
    - ¿Qué géneros están disponibles?
    - ¿Películas de terror más populares?
    - ¿Top 10 películas más populares?
    - ¿Películas con mayor presupuesto?
    - ¿Cuántas películas hay de comedia?
    
    Datos NO disponibles:
    - Directores, actores
    
    """
    
    if not question or len(question.strip()) < 3:
        return """
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #ffebee; border: 1px solid #f44336; border-radius: 8px;">
            <h3 style="color: #d32f2f; margin: 0 0 10px 0;">ERROR</h3>
            <p>Por favor, escribe una pregunta válida sobre películas.</p>
            <p style="color: #666;"><strong>Ejemplos:</strong> '¿Top 5 películas?' o '¿Géneros disponibles?'</p>
        </div>
        """

    print(f"Pregunta texto: {question}")

    # Generar SQL
    sql_query = generate_sql(question)
    print(f"SQL generada: {sql_query}")

    # Validación
    if not sql_query or len(sql_query.strip()) < 10:
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #fff3e0; border: 1px solid #ff9800; border-radius: 8px;">
            <h3 style="color: #f57c00; margin: 0 0 10px 0;">No se pudo procesar</h3>
            <p>No se pudo generar una consulta SQL válida.</p>
            <p><strong>Intenta reformular tu pregunta:</strong></p>
            <ul>
                <li>¿Top películas?</li>
                <li>¿Géneros más populares?</li>
                <li>¿Películas de comedia?</li>
            </ul>
            <p style="color: #666; font-size: 12px;">Debug: SQL generada: '{sql_query}'</p>
        </div>
        """

    try:
        results = execute_sql(sql_query)
        print(f"Resultados obtenidos: {len(results) if results else 0}")
        
        if not results:
            return f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #f3e5f5; border: 1px solid #9c27b0; border-radius: 8px;">
                <h3 style="color: #7b1fa2; margin: 0 0 10px 0;">Sin resultados</h3>
                <p>No se encontraron resultados para tu consulta.</p>
                <p><strong>Prueba con:</strong></p>
                <ul>
                    <li>¿Géneros disponibles?</li>
                    <li>¿Películas populares?</li>
                    <li>¿Top 10 películas?</li>
                </ul>
                <p style="color: #666; font-size: 12px;">SQL ejecutada: {sql_query}</p>
            </div>
            """
        
        return results_to_html(results, question)
        
    except Exception as e:
        print(f"Error en ask_text: {e}")
        return f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #ffebee; border: 1px solid #f44336; border-radius: 8px;">
            <h3 style="color: #d32f2f; margin: 0 0 10px 0;">ERROR</h3>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Verifica que tu pregunta sea sobre datos de películas o géneros disponibles en la base de datos.</p>
            <p style="color: #666; font-size: 12px;">SQL que causó el error: {sql_query}</p>
        </div>
        """

@router.post("/ask-text")
async def ask_text(data: Question):
    """
    Endpoint para consultas de texto (JSON)
    
    Acepta JSON con estructura: {"question": "tu pregunta"}
    Devuelve JSON estructurado.
    """
    question = data.question
    
    if not question or len(question.strip()) < 3:
        return {
            "error": "Por favor, escribe una pregunta válida sobre películas.",
            "sugerencia": "Ejemplos: '¿Top 5 películas?' o '¿Géneros disponibles?'"
        }

    print(f"Pregunta texto (JSON): {question}")

    sql_query = generate_sql(question)
    print(f"SQL generada: {sql_query}")

    if not sql_query or len(sql_query.strip()) < 10:
        return {
            "error": "No se pudo generar una consulta SQL válida para tu pregunta.",
            "sugerencia": "Intenta reformular tu pregunta. Ejemplos: '¿Top películas?' o '¿Géneros más populares?'",
            "debug": {
                "pregunta": question,
                "sql_generada": sql_query
            }
        }

    try:
        results = execute_sql(sql_query)
        print(f"Resultados obtenidos: {len(results) if results else 0}")

        if not results:
            return {
                "respuesta": "No se encontraron resultados para tu consulta.",
                "sugerencia": "Prueba con preguntas como: '¿Géneros disponibles?' o '¿Películas populares?'",
                "sql_ejecutada": sql_query
            }

        # Devuelve los datos crudos sin formateo ni límite
        return {
            "success": True,
            "datos": results,
            "pregunta_original": question,
            "sql_ejecutada": sql_query
        }

    except Exception as e:
        print(f"Error en ask_text: {e}")
        return {
            "error": f"Error al procesar tu consulta: {str(e)}",
            "sugerencia": "Verifica que tu pregunta sea sobre datos de películas o géneros disponibles en la base de datos."
        }