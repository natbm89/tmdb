
# Guía de Despliegue

## AWS EC2 Deployment

### 1. Preparar instancia EC2
```bash
# Conectar por SSH
ssh -i tu-key.pem ubuntu@tu-ip-ec2

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10+ y herramientas necesarias
sudo apt install python3.10 python3.10-venv python3-pip git -y

# Instalar Miniconda (recomendado)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b
export PATH="$HOME/miniconda3/bin:$PATH"
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Configurar aplicación
```bash
# Clonar código (actualizar con tu repositorio)
git clone https://github.com/natbm89/movie-app.git
cd movie-app

# Crear entorno conda con dependencias actualizadas
conda create -n movie-api python=3.10 -y
conda activate movie-api

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Variables de entorno
```bash
# Crear archivo .env
nano .env

# Contenido del .env:
DB_KEY=tusecreto
AWS_REGION=turegion
GEMINI_API_KEY=tu-gemini-api-key
```

### 4. Ejecutar aplicación
```bash
# Activar entorno
conda activate movie-api

# Navegar a directorio correcto
cd movie-app

# Modo desarrollo
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Modo producción con Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --daemon
```

### 5. Configurar seguridad
- **Security Group**: Puerto 8000 abierto para HTTP
- **HTTPS**: Certificado SSL opcional
- **Dominio**: Asignar dominio personalizado

### 6. Acceder a la API
```
# Documentación interactiva Swagger
http://tu-ip-ec2:8000/docs

# Documentación ReDoc
http://tu-ip-ec2:8000/redoc

# Endpoints principales
http://tu-ip-ec2:8000/ask-text?question=¿Top 5 películas?
http://tu-ip-ec2:8000/ask-visual?question=¿Distribución de géneros?
http://tu-ip-ec2:8000/predict (POST con JSON: { ... })
http://tu-ip-ec2:8000/predict/health (GET)
```

### 7. Mantener aplicación corriendo
```bash
# Opción 1: Screen (simple)
screen -S movie-api
conda activate movie-api
cd movie-app
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Ctrl+A, D para desconectar

# Opción 2: Systemd (recomendado para producción)
sudo nano /etc/systemd/system/movie-api.service
```

### Archivo systemd service:
```ini
[Unit]
Description=Movie API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/movie-app
Environment=PATH=/home/ubuntu/miniconda3/envs/movie-api/bin
EnvironmentFile=/home/ubuntu/movie-app/.env
ExecStart=/home/ubuntu/miniconda3/envs/movie-api/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Activar servicio
sudo systemctl daemon-reload
sudo systemctl enable movie-api
sudo systemctl start movie-api
sudo systemctl status movie-api
```

## Troubleshooting

### Verificar logs:
```bash
# Logs de aplicación
journalctl -u movie-api -f

# Verificar puerto
sudo netstat -tlnp | grep :8000
```

### Verificar variables de entorno:
```bash
# Test de variables
conda activate movie-api
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'AWS_REGION: {os.getenv(\"AWS_REGION\")}')
print(f'DB_KEY configurado: {\"Sí\" if os.getenv(\"DB_KEY\") else \"No\"}')
print(f'GEMINI_API_KEY configurado: {\"Sí\" if os.getenv(\"GEMINI_API_KEY\") else \"No\"}')
"
```

### Verificar modelo ML:
```bash
# Test del modelo de predicción
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{ ... }'

# Test de salud del modelo ML
curl http://localhost:8000/predict/health
# Respuesta esperada:
# {
#   "status": "ok",
#   "message": "Modelo de éxito cargado correctamente",
#   "model_available": true,
#   "model_path": "app/models/model_rf.pkl"
# }
```

### Verificar conectividad BD:
```bash
# Test de conexión usando AWS Secrets Manager
python3 -c "
# Tu código conecta automáticamente usando secrets manager
# No necesita variables DB_HOST, DB_PASSWORD, etc.
print('Conexión vía AWS Secrets Manager configurada')
"
```

## Checklist de Despliegue

 [ ] Instancia EC2 creada y configurada
 [ ] Miniconda instalado
 [ ] Repositorio clonado
 [ ] Entorno conda `movie-api` creado
 [ ] Dependencias instaladas desde requirements.txt
 [ ] Variables de entorno configuradas (DB_KEY, AWS_REGION, GEMINI_API_KEY)
 [ ] AWS Secrets Manager configurado
 [ ] Modelo ML `model_rf.pkl` presente en app/models/
 [ ] Puerto 8000 abierto en Security Group
 [ ] Aplicación ejecutándose con `app.main:app`
 [ ] Endpoints funcionando (/ask-text, /ask-visual, /predict, /predict/health, /health, /demo)
 [ ] Health check de la API y del modelo ML exitosos
 [ ] Documentación accesible en /docs

## URLs Finales

Una vez desplegado, tu API estará disponible en:
```
# API principal
http://TU-IP-EC2:8000

# Documentación
http://TU-IP-EC2:8000/docs
http://TU-IP-EC2:8000/redoc
```