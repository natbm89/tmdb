import requests
import json
import boto3
import io
import time
import os

# Establecer conexion con Secrets Manager para obtener la API KEY
def get_tmdb_key():
    secret_name = "api/key"
    region_name = "eu-north-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret.get('tmdb_api_key')
    except Exception as e:
        print(f"Error al obtener la clave TMDB: {e}")
        raise e

def lambda_handler(event, context):
    # VARIABLES GLOBALES
    TMDB_KEY = get_tmdb_key() # Desde SM
    LATEST_MOVIE_URL = f"https://api.themoviedb.org/3/movie/latest?api_key={TMDB_KEY}&language=en-US"
    MOVIES_URL = f"https://api.themoviedb.org/3/movie"
    # Variables del entorno
    BUCKET_NAME = os.environ.get("BUCKET_NAME")
    LAST_ID_FILE = os.environ.get("LAST_ID_FILE")

    s3 = boto3.client('s3')

    # 1) Leer LAST_SAVED_ID de S3
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=LAST_ID_FILE)
        LAST_SAVED_ID = int(obj['Body'].read().decode().strip())
    except Exception as e:
        print(f"No pude leer {LAST_ID_FILE}, inicio en 0: {e}")
        LAST_SAVED_ID = 0

    # 2) Obtener latest_movie_id de la API
    resp = requests.get(LATEST_MOVIE_URL)
    if resp.status_code != 200:
        print("Error al obtener latest_movie_id:", resp.status_code)
        return {"statusCode": 500, "body": "Error TMDB"}

    latest_movie_id = resp.json()["id"]
    print(f"TMDB latest_movie_id = {latest_movie_id}")

    # 3) Si no hay nuevos, salimos sin tocar el fichero con el ultimo id
    if latest_movie_id <= LAST_SAVED_ID:
        print("No hay nuevas películas")
        return {"statusCode": 200, "body": "Sin novedades"}

    # 4) Descarga de películas nuevas
    movies = []
    for movie_id in range(LAST_SAVED_ID + 1, latest_movie_id):
        try:
            r = requests.get(
                f"{MOVIES_URL}/{movie_id}?api_key={TMDB_KEY}&language=en-US",
                timeout=10
            )
            if r.status_code == 200:
                movies.append(r.json())
        except Exception as e:
            print(f"Error ID {movie_id}:", e)
        time.sleep(0.05)

    # 5) Subir JSON con los datos
    file_name = f"movies_{LAST_SAVED_ID+1}_to_{latest_movie_id}.json"
    buffer = io.BytesIO()
    buffer.write(json.dumps(movies, indent=4, ensure_ascii=False).encode('utf-8'))
    buffer.seek(0)
    s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=buffer)
    print(f"{file_name} subido (nuevas {len(movies)})")

    # 6) ACTUALIZAR el fichero con el ultimo id 
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=LAST_ID_FILE,
        Body=str(latest_movie_id).encode('utf-8')
    )
    print(f"{LAST_ID_FILE} actualizado a {latest_movie_id}")

    return {
        "statusCode": 200,
        "body": f"Guardadas películas hasta ID {latest_movie_id}"
    }