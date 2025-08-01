# Vuelca en la base de datos todos los ficheros de peliculas que se extrajeron y guardaron inicialmente en el data-lake de S3. 
# Se ha utilizado un script de Python en local para invocar la lambda, simulando que entraban nuevos archivos, a modo de 'trigger'. Esto solo se hace una vez. 
# Se han usado ficheros que ya han tenido una primera 'limpieza'.

import json
import boto3
import psycopg
import os

def lambda_handler(event, context):
    # Leer variables de entorno
    rds_host = os.environ['RDS_HOST']
    rds_user = os.environ['RDS_USER']
    rds_password = os.environ['RDS_PASSWORD']
    rds_db = os.environ['RDS_DB']
    rds_port = 5432
    bucket_name = os.environ['S3_BUCKET']

    # Leer el nombre del archivo desde el evento
    key = event.get('key')
    if not key:
        return {
            'statusCode': 400,
            'body': 'No se proporcionó el nombre del archivo (key).'
        }

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
