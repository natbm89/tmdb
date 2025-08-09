import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

def get_db_key():
    secret_name = os.getenv("DB_KEY")
    region_name = os.getenv("AWS_REGION")

    if not secret_name:
        raise ValueError("La variable de entorno DB_KEY no está definida.")

    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")

        if not secret_string:
            raise ValueError("El secreto no contiene 'SecretString'.")

        secret = json.loads(secret_string)
        # pasar "username" a "user" 
        if "username" in secret:
            secret["user"] = secret.pop("username")
        # eliminar claves no necesarias
        for key in ["engine", "dbInstanceIdentifier"]:
            if key in secret:
                del secret[key]
        return secret

    except ClientError as e:
        error_code = e.response['Error']['Code']
        raise RuntimeError(f"Error al obtener el secreto: {error_code} - {e}")

    except json.JSONDecodeError:
        raise ValueError("El contenido del secreto no es un JSON válido.")

    except Exception as e:
        raise RuntimeError(f"Error inesperado al obtener el secreto: {e}")

# Diccionario con la configuración de conexión
DB_CONFIG = get_db_key()