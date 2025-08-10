# Último Proceso de ETL

Finalmente, se decide extraer **todos los datos de la API de TMDB**, desde el **ID 1** hasta el **ID 1,000,000**, que fue donde se comenó al inicio del proyecto.

## Mejoras implementadas

- Para acelerar el proceso de extracción (que en la primera ocasión fue muy lento), se investigaron alternativas y se introdujeron cambios en el script original, creando un nuevo notebook que:
  - Utiliza **concurrencia (hilos)** para acelerar la descarga de los datos.
  - Agrupa los resultados en **lotes de 5,000 películas**.
  - Guarda cada lote como un archivo `.json` y lo sube automáticamente al bucket de **S3**.

## Automatización y optimización

- En esta ocasión, se pudo utilizar una **Lambda en AWS** que se activa mediante trigger cada vez que entra un archivo nuevo en el bucket.
- Tanto esta Lambda como la que se usaba para la carga diaria en **RDS** se han optimizado para los nuevos requerimientos de la base de datos y para evitar los errores detectados en el segundo proceso de ETL.
- Estas Lambdas ya incluyen todos los campos, comprueban la existencia de títulos vacíos (solo espacios en blanco), transforman los datos y los cargan en **RDS**.