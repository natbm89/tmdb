# Vuelca en la BD todos los ficheros de peliculas que se extrajeron y guardaron inicialmente en el data-lake de S3. 
# Se ha utilizado un script de Python en local para invocar la lambda, simulando que entraban nuevos archivos, a modo de 'trigger'. 
# Esto solo se hace una vez. Se han usado ficheros que ya han tenido una primera 'limpieza'.

import json
import boto3
import psycopg
import os

# Cargar las credenciales de acceso a la BD desde SM
def get_rds_key():
    secret_name = "tmdb/key"
    region_name = "eu-north-1"

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

    # Leer el nombre del archivo desde el evento
    key = event.get('key')
    if not key:
        return {
            'statusCode': 400,
            'body': 'No se proporcionó el nombre del archivo (key).'
        }

    # Conectar a la BD
    s3 = boto3.client('s3')
    conn = psycopg.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        dbname=rds_db,
        port=rds_port
    )

    total_peliculas = 0

    try:
        with conn.cursor() as cur:
            print(f"Procesando archivo: {key}")

            # Leer archivo JSON desde S3
            file_obj = s3.get_object(Bucket=bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            movies = json.loads(content)

            for movie in movies:
                # Insertar película
                cur.execute("""
                    INSERT INTO peliculas (
                        movie_id, titulo, release_date, duracion, vote_average,
                        vote_count, origin_country, overview, revenue, budget
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (movie_id) DO NOTHING;
                """, (
                    movie.get('id'),
                    movie.get('title'),
                    movie.get('release_date'),
                    movie.get('runtime'),
                    round(movie.get('vote_average', 0.0), 1),
                    movie.get('vote_count'),
                    ','.join(movie.get('origin_country', [])),
                    movie.get('overview'),
                    movie.get('revenue'),
                    movie.get('budget')
                ))

                # Insertar relación con géneros
                for genre in movie.get('genres', []):
                    genre_id = genre.get('id')
                    cur.execute("""
                        INSERT INTO peliculas_generos (movie_id, genero_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (movie.get('id'), genre_id))

            total_peliculas = len(movies)
            conn.commit()

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
        'body': f'{total_peliculas} películas procesadas desde {key}.'
    }
