import boto3
import json
import psycopg
import os

def lambda_handler(event, context):
    # Lambda function para procesar un archivo JSON de películas desde S3
    # y actualizar la base de datos RDS con validación completa.
    
    try:
        # Obtener información del archivo desde el evento
        bucket_name = event['bucket_name']
        file_key = event['file_key']
        
        print(f"Procesando archivo: {file_key}")
        
        # Inicializar clientes
        s3 = boto3.client('s3')
        
        # Obtener credenciales de RDS
        rds_key = get_rds_key()
        
        # Procesar archivo
        processed, inserted, updated = process_movie_file(s3, bucket_name, file_key, rds_key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Archivo {file_key} procesado exitosamente',
                'processed': processed,
                'inserted': inserted,
                'updated': updated
            })
        }
        
    except Exception as e:
        print(f"Error procesando archivo: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'file_key': event.get('file_key', 'unknown')
            })
        }

def get_rds_key():
    # Obtener credenciales de RDS desde AWS Secrets Manager
    secret_name = os.environ['DB_KEY']
    region_name = os.environ['REGION']

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return {
            'username': secret.get('username'),
            'password': secret.get('password'),
            'host': secret.get('host'),
            'port': secret.get('port'),
            'dbname': secret.get('dbname')
        }
    except Exception as e:
        print(f"Error al obtener el secreto: {e}")
        raise e

def process_movie_file(s3_client, bucket, key, rds_credentials):
    # Procesa un archivo JSON desde S3 y actualiza la base de datos
    
    try:
        # Leer archivo JSON desde S3
        file_obj = s3_client.get_object(Bucket=bucket, Key=key)
        content = file_obj['Body'].read().decode('utf-8')
        movies = json.loads(content)
        
        print(f"Archivo leído: {len(movies)} películas encontradas")
        
        # Conectar a la base de datos
        conn = psycopg.connect(
            host=rds_credentials['host'],
            user=rds_credentials['username'],
            password=rds_credentials['password'],
            dbname=rds_credentials['dbname'],
            port=rds_credentials['port']
        )
        
        processed_count = 0
        updated_count = 0
        inserted_count = 0
        
        try:
            with conn.cursor() as cur:
                for movie in movies:
                    # Limpiar y validar datos de la película
                    cleaned_movie = clean_and_validate_movie(movie)
                    if not cleaned_movie:
                        continue  # Salta películas con datos inválidos
                    
                    movie_id = cleaned_movie['id']
                    
                    # Verificar si la película ya existe
                    cur.execute("SELECT movie_id FROM peliculas WHERE movie_id = %s", (movie_id,))
                    exists = cur.fetchone()
                    
                    if exists:
                        # Actualizar película existente con campos completos
                        update_movie(cur, cleaned_movie)
                        updated_count += 1
                    else:
                        # Insertar nueva película
                        insert_movie(cur, cleaned_movie)
                        inserted_count += 1
                    
                    # Gestionar géneros (usar datos originales para géneros)
                    update_movie_genres(cur, movie_id, movie.get('genres', []))
                    
                    processed_count += 1
            
            conn.commit()
            print(f"Procesamiento completado: {processed_count} películas ({inserted_count} insertadas, {updated_count} actualizadas)")
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return processed_count, inserted_count, updated_count
        
    except Exception as e:
        print(f"Error procesando {key}: {str(e)}")
        raise e

def insert_movie(cursor, movie):
    # Inserta una nueva película con todos los campos disponibles
    cursor.execute("""
        INSERT INTO peliculas (
            movie_id, titulo, release_date, duracion, vote_average, vote_count,
            origin_country, overview, revenue, budget, adult, belong_to_collection,
            original_language, original_title, popularity,
            production_companies, production_countries, spoken_languages,
            status, tagline
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        movie['id'],
        movie['title'],
        movie['release_date'],
        movie['runtime'],
        movie['vote_average'],
        movie['vote_count'],
        ','.join([c for c in movie['origin_country'] if c]) if movie['origin_country'] else None,
        movie['overview'],
        movie['revenue'],
        movie['budget'],
        movie['adult'],
        json.dumps(movie['belongs_to_collection']) if movie['belongs_to_collection'] else None,
        movie['original_language'],
        movie['original_title'],
        movie['popularity'],
        ','.join([pc.get('name', '') for pc in movie['production_companies']]) if movie['production_companies'] else None,
        ','.join([pc.get('name', '') for pc in movie['production_countries']]) if movie['production_countries'] else None,
        ','.join([sl.get('name', '') for sl in movie['spoken_languages']]) if movie['spoken_languages'] else None,
        movie['status'],
        movie['tagline']
    ))

def update_movie(cursor, movie):
    # Actualiza una película existente con los campos faltantes
    cursor.execute("""
        UPDATE peliculas SET
            titulo = %s,
            release_date = %s,
            duracion = %s,
            vote_average = %s,
            vote_count = %s,
            origin_country = %s,
            overview = %s,
            revenue = %s,
            budget = %s,
            adult = %s,
            belong_to_collection = %s,
            original_language = %s,
            original_title = %s,
            popularity = %s,
            production_companies = %s,
            production_countries = %s,
            spoken_languages = %s,
            status = %s,
            tagline = %s
        WHERE movie_id = %s
    """, (
        movie['title'],
        movie['release_date'],
        movie['runtime'],
        movie['vote_average'],
        movie['vote_count'],
        ','.join([c for c in movie['origin_country'] if c]) if movie['origin_country'] else None,
        movie['overview'],
        movie['revenue'],
        movie['budget'],
        movie['adult'],
        json.dumps(movie['belongs_to_collection']) if movie['belongs_to_collection'] else None,
        movie['original_language'],
        movie['original_title'],
        movie['popularity'],
        ','.join([pc.get('name', '') for pc in movie['production_companies']]) if movie['production_companies'] else None,
        ','.join([pc.get('name', '') for pc in movie['production_countries']]) if movie['production_countries'] else None,
        ','.join([sl.get('name', '') for sl in movie['spoken_languages']]) if movie['spoken_languages'] else None,
        movie['status'],
        movie['tagline'],
        movie['id']
    ))

def update_movie_genres(cursor, movie_id, genres):
    # Actualiza la relación película-géneros
    # Primero, eliminar géneros existentes para esta película
    cursor.execute("DELETE FROM peliculas_generos WHERE movie_id = %s", (movie_id,))
    
    # Insertar nuevos géneros
    for genre in genres:
        genre_id = genre.get('id')
        genre_name = genre.get('name')
        
        if genre_id and genre_name:
            # Asegurar que el género existe en la tabla géneros
            cursor.execute("""
                INSERT INTO generos (genero_id, nombre) 
                VALUES (%s, %s) 
                ON CONFLICT (genero_id) DO NOTHING
            """, (genre_id, genre_name))
            
            # Insertar relación película-género
            cursor.execute("""
                INSERT INTO peliculas_generos (movie_id, genero_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (movie_id, genre_id))

# Funciones de validación y limpieza de datos
def clean_and_validate_movie(movie):
    # Limpia y valida los datos de una película antes de procesarla
    # Verificar que tenga ID válido
    movie_id = movie.get('id')
    if not movie_id or not isinstance(movie_id, int):
        return None
    
    # Verificar que tenga título válido
    title = clean_string(movie.get('title'))
    if not title:
        print(f"Saltando película sin título válido: ID {movie_id}")
        return None
    
    # Limpiar y validar campos
    cleaned_movie = {
        'id': movie_id,
        'title': title,  # Ya validado arriba
        'release_date': clean_date(movie.get('release_date')),
        'runtime': clean_integer(movie.get('runtime')),
        'vote_average': clean_float(movie.get('vote_average'), max_val=10.0),
        'vote_count': clean_integer(movie.get('vote_count')),
        'origin_country': clean_list(movie.get('origin_country', [])),
        'overview': clean_text(movie.get('overview')),
        'revenue': clean_bigint(movie.get('revenue')),
        'budget': clean_bigint(movie.get('budget')),
        'adult': clean_boolean(movie.get('adult')),
        'belongs_to_collection': movie.get('belongs_to_collection'),
        'original_language': clean_string(movie.get('original_language'), max_len=10),
        'original_title': clean_string(movie.get('original_title')),
        'popularity': clean_float(movie.get('popularity')),
        'production_companies': clean_list(movie.get('production_companies', [])),
        'production_countries': clean_list(movie.get('production_countries', [])),
        'spoken_languages': clean_list(movie.get('spoken_languages', [])),
        'status': clean_string(movie.get('status'), max_len=50),
        'tagline': clean_text(movie.get('tagline'))
    }
    
    return cleaned_movie

def clean_string(value, max_len=255):
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    if len(cleaned) == 0:
        return None
    return cleaned[:max_len] if max_len else cleaned

def clean_text(value, max_len=2000):
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned[:max_len] if cleaned else None

def clean_integer(value, min_val=0):
    if value is None:
        return None
    try:
        int_val = int(value)
        return int_val if int_val >= min_val else None
    except (ValueError, TypeError):
        return None

def clean_bigint(value):
    if value is None or value == 0:
        return None
    try:
        return int(value) if int(value) > 0 else None
    except (ValueError, TypeError):
        return None

def clean_float(value, min_val=0.0, max_val=None):
    if value is None:
        return None
    try:
        float_val = float(value)
        if float_val < min_val:
            return None
        if max_val and float_val > max_val:
            return max_val
        return round(float_val, 2)
    except (ValueError, TypeError):
        return None

def clean_boolean(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes']
    return bool(value)

def clean_date(value):
    if not value or not isinstance(value, str):
        return None
    # Verificar formato YYYY-MM-DD
    if len(value) != 10 or value.count('-') != 2:
        return None
    try:
        year, month, day = value.split('-')
        if int(year) < 1888 or int(year) > 2030:
            return None
        return value
    except (ValueError, TypeError):
        return None

def clean_list(value):
    if not value or not isinstance(value, list):
        return []
    return [item for item in value if item and isinstance(item, dict)]
