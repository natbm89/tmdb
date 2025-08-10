
# Guía de Despliegue

## AWS EC2 Deployment

### 1. Preparar instancia EC2
```bash
# Conectar por SSH
ssh -i tu-key.pem ec2-user@tu-ip-ec2

# Actualizar sistema
sudo dnf upgrade --releasever=2023.8.20250808

# Instalar Python 3.10+ y herramientas necesarias
sudo yum install python3.11 -y
sudo yum install git -y
```

### 2. Configurar aplicación
```bash
# Configurar git
git config --global user.name "tu-usuario"
git config --global user.email "tu-email"
#Crear clave SSH
ssh-keygen -t ed25519 -C "nombre-clave"
cat ~/.ssh/id_ed25519.pub #Añadir al repositorio en git
# Clonar repositorio
git clone git@github.com:natbm89/tmdb.git
cd tmdb/movie-api/

# Crear entorno con dependencias actualizadas
python3.11 -m venv venv
source venv/bin/activate

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
### 4. Configurar CLI para AWS
```bash
aws configure
```

### 5. Ejecutar aplicación
```bash
# Activar entorno
source venv/bin/activate

# Navegar a directorio correcto
cd tmdb/movie-api/

# Lanzar uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Configurar seguridad
- **Security Group**: Puerto 8000 abierto para HTTP

### 7. Acceder a la API
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

### 8. Mantener aplicación corriendo
```bash
# Opción 1: Screen (simple)
screen -S movie-api
source venv/bin/activate
cd ~/tmdb/movie-api
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
User=ec2-user
WorkingDirectory=/home/ec2-user/tmdb/movie-api
Environment=PATH=/home/ec2-user/tmdb/movie-api/venv/bin
EnvironmentFile=/home/ec2-user/tmdb/movie-api/.env
ExecStart=/home/ec2-user/tmdb/movie-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
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
# Si netstat no está instalado, ejecuta:
# sudo yum install net-tools -y
```

### Verificar variables de entorno:
```bash
# Test de variables
source venv/bin/activate
python3.11 -c "
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='/home/ec2-user/tmdb/movie-api/.env')  # Ajusta la ruta si tu .env está en otro sitio
print(f'AWS_REGION: {os.getenv("AWS_REGION")})')
print(f'DB_KEY configurado: {'Sí' if os.getenv('DB_KEY') else 'No'}')
print(f'GEMINI_API_KEY configurado: {'Sí' if os.getenv('GEMINI_API_KEY') else 'No'}')
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
 [ ] Repositorio clonado
 [ ] Entorno creado
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