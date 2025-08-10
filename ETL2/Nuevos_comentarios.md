# Segundo Proceso de ETL

- Tras comprobar la calidad de los datos extraídos de la API de TMDB y el rendimiento del modelo en los entrenamientos, se decide **actualizar el contenido en RDS** para incluir:
  - Todos los campos existentes en los datos originales.
  - Los datos generados con las actualizaciones diarias.

## Mejoras en el Proceso

- Se investigó cómo acelerar el proceso respetando el timing y se decidió utilizar **varias Lambdas en paralelo**, lo que redujo considerablemente los tiempos de procesado.
- La lambda hizo todo el **proceso de transformación** previo a la carga de los datos en RDS.
- Durante el proceso se detectaron algunos errores que se fueron subsanando sin mayor problema.

## Automatización

- Como los datos ya estaban en S3, se utilizó nuevamente un script para llamar a las Lambdas, simulando la entrada de nuevos ficheros en el bucket.