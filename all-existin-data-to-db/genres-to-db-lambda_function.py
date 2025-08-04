# Vuelca en la BD el archivo de generos que se guardó inicialmente en el data-lake de S3. 
# Se ha invocado desde la propia lambda, pues es un único archivo.

import json
import boto3
import psycopg
import os

# Conectar con Secrets Manager para obtener las credenciales de la BD.
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

s3_client = boto3.client('s3')

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
    key = os.environ['KEY'] 

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        data = json.loads(content)
        generos = data.get("genres", [])

        with psycopg.connect(
            # Conectar a la BD
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