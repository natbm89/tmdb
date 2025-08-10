# Vuelca de forma automatica en la BD los datos nuevos que se descargan a diario.
# Utiliza los ficheros en bruto que se obtienen desde la API y se hace la limpieza inicial con la propia lambda.
# Version actualizada con todos los campos.

import json
import boto3
import psycopg
import os
import re

# Cargar las credenciales de acceso a la BD desde SM
def get_rds_key():
    secret_name = os.environ.get('DB_KEY')
    region_name = os.environ.get('REGION')
    
    if not secret_name or not region_name:
        raise ValueError("Las variables de entorno DB_KEY y REGION son requeridas")

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


def is_valid_title(title):
    
    # Valida si un título es válido para insertar en la base de datos.
    
    if not title:
        return False
    
    # Verificar si es solo espacios en blanco
    if title in [' ', '  ', '   '] or title.strip() == '':
        return False
    
    return True


def lambda_handler(event, context):
    # Leer los datos extraidos de Secrets Manager
    rds_key = get_rds_key()
    rds_host = rds_key['host']
    rds_user = rds_key['username']
    rds_password = rds_key['password']
    rds_db = rds_key['dbname']
    rds_port = rds_key['port']
    # Leer variables de entorno
    bucket_name = os.environ['S3_BUCKET']

    # Extraer el nombre del archivo desde el evento de S3
    try:
        key = event['Records'][0]['s3']['object']['key']
    except (KeyError, IndexError):
        return {
            'statusCode': 400,
            'body': 'No se pudo extraer el nombre del archivo del evento.'
        }

    # Conectar con la BD
    s3 = boto3.client('s3')
    conn = psycopg.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        dbname=rds_db,
        port=rds_port
    )

    total_peliculas = 0
    peliculas_omitidas = 0

    try:
        with conn.cursor() as cur:
            print(f"Procesando archivo: {key}")

            # Leer archivo JSON desde S3
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            movies = json.loads(content)

            for movie in movies:
                # Validar campos obligatorios
                movie_id = movie.get('id')
                title = movie.get('title')
                if not movie_id or not title:
                    print(f"Película omitida por falta de ID o título: {movie}")
                    peliculas_omitidas += 1
                    continue

                # Validar calidad del título
                if not is_valid_title(title):
                    print(f"Película omitida por título vacío (ID: {movie_id}, título: '{title}')")
                    peliculas_omitidas += 1
                    continue

                # Validaciones y conversiones
                release_date = movie.get('release_date') or None
                runtime = movie.get('runtime')
                runtime = runtime if isinstance(runtime, int) else None
                vote_average = round(movie.get('vote_average', 0.0), 1)
                vote_count = movie.get('vote_count', 0)
                origin_country = ','.join(movie.get('origin_country', [])) or None
                overview = movie.get('overview') or None
                revenue = movie.get('revenue', 0)
                budget = movie.get('budget', 0)
                adult = movie.get('adult', False)
                belong_to_collection = None
                if movie.get('belongs_to_collection'):
                    belong_to_collection = movie['belongs_to_collection'].get('name')
                original_language = movie.get('original_language') or None
                original_title = movie.get('original_title') or None
                popularity = movie.get('popularity', 0.0)
                
                # Procesar arrays como strings separados por comas
                production_companies = None
                if movie.get('production_companies'):
                    companies = [comp.get('name') for comp in movie['production_companies'] if comp.get('name')]
                    production_companies = ','.join(companies) if companies else None
                
                production_countries = None
                if movie.get('production_countries'):
                    countries = [country.get('name') for country in movie['production_countries'] if country.get('name')]
                    production_countries = ','.join(countries) if countries else None
                
                spoken_languages = None
                if movie.get('spoken_languages'):
                    languages = [lang.get('name') for lang in movie['spoken_languages'] if lang.get('name')]
                    spoken_languages = ','.join(languages) if languages else None
                
                status = movie.get('status') or None
                tagline = movie.get('tagline') or None

                # Insertar película con todos los campos
                cur.execute("""
                    INSERT INTO peliculas (
                        movie_id, titulo, release_date, duracion, vote_average,
                        vote_count, origin_country, overview, revenue, budget,
                        adult, belong_to_collection, original_language, original_title,
                        popularity, production_companies, production_countries,
                        spoken_languages, status, tagline
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (movie_id) DO NOTHING;
                """, (
                    movie_id,
                    title,
                    release_date,
                    runtime,
                    vote_average,
                    vote_count,
                    origin_country,
                    overview,
                    revenue,
                    budget,
                    adult,
                    belong_to_collection,
                    original_language,
                    original_title,
                    popularity,
                    production_companies,
                    production_countries,
                    spoken_languages,
                    status,
                    tagline
                ))

                # Insertar relación con géneros
                for genre in movie.get('genres', []):
                    genre_id = genre.get('id')
                    if genre_id:
                        cur.execute("""
                            INSERT INTO peliculas_generos (movie_id, genero_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;
                        """, (movie_id, genre_id))

            total_peliculas = len([m for m in movies if m.get('id') and is_valid_title(m.get('title', ''))])
            conn.commit()
            print(f"Procesamiento completado: {total_peliculas} películas insertadas, {peliculas_omitidas} omitidas")

    except Exception as e:
        print(f"Error procesando {key}: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Error procesando {key}: {str(e)}'
        }

    finally:
        conn.close()

    return {
        'statusCode': 200,
        'body': f'{total_peliculas} películas procesadas desde {key}. {peliculas_omitidas} películas omitidas por problemas de calidad.'
    }