from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.utils.sql_converter import generate_sql
from app.models.sql_predictor import execute_sql
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import matplotlib
matplotlib.use('Agg')

router = APIRouter()

class VisualQuestion(BaseModel):
    question: str

def detect_chart_type(question, sql_query):
    # Detecta qué tipo de gráfico crear basado en la pregunta y SQL
    question_lower = question.lower()
    sql_lower = sql_query.lower()
    
    if "top" in question_lower or "mayor" in question_lower or "mejor" in question_lower:
        return "bar"
    elif "distribución" in question_lower or "distribution" in question_lower:
        return "pie"
    elif "evolución" in question_lower or "tiempo" in question_lower or "año" in question_lower:
        return "line"
    else:
        return "bar"

def create_chart(df, chart_type, question):
    # Crea el gráfico basado en los datos y tipo
    plt.figure(figsize=(12, 8))
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    if len(df.columns) == 1:
        value_counts = df.iloc[:, 0].value_counts().head(10)
        
        if chart_type == "pie":
            colors = plt.cm.Set3(range(len(value_counts)))
            plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%', colors=colors)
            plt.title(f"{question}", fontsize=16, fontweight='bold', pad=20)
        else:
            bars = plt.bar(range(len(value_counts)), value_counts.values, color='steelblue', alpha=0.8)
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
            plt.title(f"{question}", fontsize=16, fontweight='bold', pad=20)
            plt.ylabel("Cantidad", fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
    elif len(df.columns) == 2:
        if chart_type == "pie":
            colors = plt.cm.Set3(range(len(df)))
            plt.pie(df.iloc[:, 1], labels=df.iloc[:, 0], autopct='%1.1f%%', colors=colors)
            plt.title(f"{question}", fontsize=16, fontweight='bold', pad=20)
        elif chart_type == "line":
            plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker='o', linewidth=3, markersize=8, color='steelblue')
            plt.title(f"📈 {question}", fontsize=16, fontweight='bold', pad=20)
            plt.xlabel(df.columns[0], fontsize=12)
            plt.ylabel(df.columns[1], fontsize=12)
            plt.grid(True, alpha=0.3)
        else:
            bars = plt.bar(range(len(df)), df.iloc[:, 1], color='steelblue', alpha=0.8)
            plt.xticks(range(len(df)), df.iloc[:, 0], rotation=45, ha='right')
            plt.title(f"{question}", fontsize=16, fontweight='bold', pad=20)
            plt.ylabel(df.columns[1], fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
            
    elif len(df.columns) == 3:
        bars = plt.bar(range(len(df)), df.iloc[:, 2], color='steelblue', alpha=0.8)
        plt.xticks(range(len(df)), df.iloc[:, 0], rotation=45, ha='right')
        plt.title(f"{question}", fontsize=16, fontweight='bold', pad=20)
        plt.ylabel(df.columns[2], fontsize=12)
        plt.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()

async def process_visual_question(question: str, return_image: bool = False):
    # Función común para procesar preguntas visuales
    
    if not question or len(question.strip()) < 3:
        if return_image:
            raise HTTPException(status_code=400, detail="Pregunta muy corta")
        return {"error": "Por favor, escribe una pregunta válida sobre películas."}

    print(f"Pregunta visual: {question}")

    # Generar SQL
    sql_query = generate_sql(question)
    
    if not sql_query or not sql_query.strip().lower().startswith("select"):
        error_msg = "No se pudo generar una consulta SQL válida para visualización."
        if return_image:
            raise HTTPException(status_code=400, detail=error_msg)
        return {
            "error": error_msg,
            "suggestion": "Intenta reformular tu pregunta. Ejemplos: '¿Top 10 géneros?'",
            "debug": {"question": question, "sql_query": sql_query}
        }

    try:
        results = execute_sql(sql_query)
        print(f"Resultados obtenidos: {len(results) if results else 0} filas")
        
        if not results:
            error_msg = "No se encontraron datos para tu consulta."
            if return_image:
                raise HTTPException(status_code=404, detail=error_msg)
            return {
                "error": error_msg,
                "suggestion": "Prueba con preguntas como: '¿Top géneros?' o '¿Mejores películas?'"
            }

        # Convertir resultados a DataFrame
        if isinstance(results[0], tuple):
            num_cols = len(results[0])
        else:
            results = [(r,) for r in results]
            num_cols = 1

        # Crear columnas descriptivas
        if num_cols == 1:
            columns = ["Valor"]
        elif num_cols == 2:
            columns = ["Categoría", "Valor"]
        elif num_cols == 3:
            columns = ["Nombre", "Rating", "Cantidad"]
        else:
            columns = [f"Col_{i+1}" for i in range(num_cols)]

        df = pd.DataFrame(results, columns=columns)
        print(f"DataFrame creado: {df.shape}")

        # Limitar a top 10 para mejor visualización
        df = df.head(10)

        # Detectar tipo de gráfico automáticamente
        chart_type = detect_chart_type(question, sql_query)
        print(f"Tipo de gráfico: {chart_type}")

        # Crear gráfico mejorado
        create_chart(df, chart_type, question)

        # Convertir a imagen
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)

        if return_image:
            # DEVOLVER IMAGEN DIRECTA
            return StreamingResponse(
                io.BytesIO(buf.read()), 
                media_type="image/png",
                headers={
                    "Content-Disposition": "inline; filename=chart.png",
                    "Cache-Control": "no-cache"
                }
            )
        else:
            # DEVOLVER JSON CON BASE64
            img_base64 = base64.b64encode(buf.read()).decode("utf-8")
            return {
                "success": True,
                "grafico": f"data:image/png;base64,{img_base64}",
                "mensaje": f"Gráfico generado para: {question}",
                "detalles": {
                    "pregunta": question,
                    "tipo_grafico": chart_type,
                    "datos_encontrados": len(results),
                    "sql_ejecutada": sql_query,
                    "columnas": columns
                }
            }

    except Exception as e:
        print(f"Error en proceso visual: {e}")
        if return_image:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
        return {
            "error": f"Error al generar la visualización: {str(e)}",
            "suggestion": "Verifica que tu pregunta sea sobre películas, géneros..."
        }

# ENDPOINT HÍBRIDO
@router.get("/ask-visual")
async def ask_visual_get(
    question: str = Query(
        ..., 
        description="Escribe tu pregunta sobre películas aquí",
        examples={"pregunta": {"summary": "Ejemplo", "value": "¿Cuáles son los top 5 géneros con mejores ratings?"}},
        min_length=5,
        max_length=200
    ),
    format: str = Query(
        "image", 
        description="Formato de respuesta: 'image' para imagen directa, 'json' para datos",
        pattern="^(image|json)$"
    )
):
    """
    **Genera un gráfico basado en tu pregunta sobre películas de la base de datos**
    
    
    **(GET) Para ver imagen directamente:**
    - format=image (por defecto)
    - La imagen se carga automáticamente en el navegador
    
    **Ejemplos de preguntas válidas:**
    - ¿Cuáles son los top 5 géneros con mejores ratings?
    - ¿Distribución de géneros?
    - ¿Qué películas tienen mejor puntuación?
    - ¿Top 10 películas más populares?
    - ¿Películas con mayor presupuesto?
    - ¿Distribución de películas por año?
    - ¿Películas de comedia más populares?
    - ¿Géneros más populares?
    
    **Datos NO disponibles en esta BD:**
    - Directores, actores
    
    """
    
    return await process_visual_question(question, return_image=(format == "image"))

@router.post("/ask-visual")
async def ask_visual_post(data: VisualQuestion):
    """
    **Versión POST del endpoint**
    
    Acepta JSON con estructura: {"question": "tu pregunta"}
    Siempre devuelve JSON con Base64.
    """
    
    return await process_visual_question(data.question, return_image=False)