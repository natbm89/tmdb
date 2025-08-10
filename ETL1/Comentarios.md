# Comentarios sobre el Proceso ETL

- Para agilizar la extracción, se decidió comenzar a extraer datos a partir del **ID 1,000,000** hasta el último disponible en la API de TMDB.
- Para cargar los datos en la Base de Datos, **solo se utilizaron los campos considerados como relevantes** para el posterior entrenamiento del modelo.

## Fases del Proceso

1. **Extracción inicial:**  
   Se extrajeron los datos y se subieron automáticamente a un bucket de **S3**.
2. **Limpieza:**  
   Los datos fueron limpiados tras la extracción.
3. **Automatización con AWS Lambda:**  
   - Se crearon Lambdas para:
     - Extracción de nuevos datos de la API.
     - Guardado en S3.
     - Transformación y carga diaria en **RDS**.

## Carga Masiva Inicial

- Los datos extraídos inicialmente de forma masiva se cargaron en RDS mediante una Lambda invocada manualmente con un script que simula la entrada de archivos nuevos al bucket.
- Esto fue necesario porque la base de datos en RDS **no estaba disponible** cuando se comenzó la extracción de datos.