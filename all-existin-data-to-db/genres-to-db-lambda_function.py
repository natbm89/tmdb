# Vuelca en la base de datos el archivo de generos que se guardó inicialmente en el data-lake de S3. 
# Se ha invocado desde la propia lambda, pues es un único archivo.

import json
import boto3
import psycopg
import os

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Leer variables de entorno
    bucket = os.environ['S3_BUCKET']
    key = os.environ['KEY'] 
    rds_host = os.environ['RDS_HOST']
    rds_user = os.environ['RDS_USER']
    rds_password = os.environ['RDS_PASSWORD']
    rds_db = os.environ['RDS_DB']
    rds_port = 5432

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        data = json.loads(content)
        generos = data.get("genres", [])

        with psycopg.connect(
            host=rds_host,
            dbname=rds_db,
            user=rds_user,
            password=rds_password,
            port=rds_port
        ) as conn:
            with conn.cursor() as cur:
                for genero in generos:
                    cur.execute("""
                        INSERT INTO generos (genero_id, nombre)
                        VALUES (%s, %s)
                        ON CONFLICT (genero_id) DO NOTHING;
                    """, (genero.get('id'), genero.get('name')))
                conn.commit()

        return {
            'statusCode': 200,
            'body': f'{len(generos)} géneros insertados correctamente'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }