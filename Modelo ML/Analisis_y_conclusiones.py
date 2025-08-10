El dataset inicial se presenta complicado desde el inicio, 
al estar caracterizado por la presencia masiva de valores nulos o atípicos 
(especialmente ceros) en métricas clave como los ingresos (revenue) y el presupuesto (budget).
Además, lo complejo de las columnas de texto como las compañías productoras, 
países e idiomas, así como los géneros, ha requerido un procesamiento específico.
Por lo que hemos implementado varias estrategias:

    • La creación de true_revenue y true_budget (filtrando valores inferiores a 9999) 
    que nos permite trabajar con datos más significativos.

    • Se derivan características binarias (has_true_overview, has_true_tagline, in_collection)
    para identificar la presencia de información clave, y se aplica One-Hot Encoding (OHE)
    a los géneros y a los "Top 10" elementos más frecuentes de las columnas de texto complejas,
    transformando datos cualitativos en características numéricas válidas para el modelo.

    • Para asegurar la robustez del DataFrame final hemos imputado nulos con la media en 
    columnas relevantes y la conversión de tipos de datos (como adult a booleano).

La definición de "éxito" la basamos en una combinación de umbrales para true_revenue,
vote_average, vote_count y popularity. Con esto buscamos capturar películas que no solo 
generen ingresos considerables, sino que también sean bien recibidas por la crítica y el público.
Sin embargo, el resultado de esta métrica revela un notable desbalance de clases 
(aproximadamente 8 películas no exitosas por cada película exitosa). 
Este desequilibrio refleja la realidad de la industria cinematográfica,
donde los grandes éxitos son, por definición, la excepción y no la norma,
la métrica de éxito que hemos definido está capturando películas que son verdaderamente 
excepcionales en términos de ingresos, calificación, votos y popularida, pero para un modelo
de clasificación, un desbalance tan pronunciado es una complicación más que una ayuda,
porque tiende a aprender a clasificar muy bien la clase 0 porque hay muy pocas películas 
que son exitosas, y equivocarse al predecir un "no éxito" le es “más fácil” con los datos 
que disponemos, así que además tiende a identificar “no éxitos”... 

Las visualizaciones muestran la relación entre las características y el éxito:

    • Vemos que las películas exitosas deben tener un true_revenue, vote_average, 
    vote_count y popularity significativamente más altos en comparación con las no exitosas.
    Estas son las impulsoras detrás del éxito “como se esperaba “.

    • La pertenencia a una colección (in_collection) parece ser un predictor 
    extremadamente potente, con una proporción de éxito mucho mayor para las películas 
    que forman parte de una.

    • De igual modo la presencia de un overview o tagline (has_true_overview, has_true_tagline) 
    también se correlaciona fuertemente con una mayor probabilidad de éxito 
    (probablemente por un nivel de producción o marketing más potente).

    • El idioma original (original_language) mostró que lenguas como el japonés y el chino 
    presentan una alta proporción de éxito relativo en nuestro dataset.

    • El status de la película es un predictor lógico: las películas Released (ya se han estrenado)
    tienen la mayor proporción de éxito.

El RandomForestClassifier fue seleccionado y entrenado con los datos preprocesados pero debido 
al desbalance de clases observado, el recall para la clase "1" (éxito) se nos presenta evidentemente 
como un área de mejora, lo que indica que el modelo puede tener dificíl identificar una proporción 
significativa de los verdaderos éxitos. Pero para abordar este desbalance, incluímos el parámetro 
class_weight='balanced' en el RandomForestClassifier para que el modelo diera mayor importancia 
a la clase minoritaria durante el entrenamiento.

La métrica de éxito, aunque desequilibrada, permitió definir y clasificar las películas exitosas.
Y el modelo de RandomForestClassifier, ajustado para el desbalance de clases, proporciona 
un punto de partida para la predicción.

NOTA:
Al finalizar todas las comprobaciones del modelo se observó que las películas más antiguas 
o los primeros registros de la API tendían a tener datos más completos, 
mientras que los datos más recientes presentaban más inconsistencias y valores faltantes.
Hemos podido confirmar que ha sido la variabilidad en tener completados todos los valores y 
calidad de los datos a lo largo del tiempo en la API de TMDB lo que nos ha faltado para que 
nuestro modelo fuera aún más eficiente. 
Integrar estos datos más completos en la base de datos y re-entrenar el modelo resulta en 
una mejora significativa en las métricas de predicción de éxito, al integrar los datos 
más completos de los primeros registros de la API, la base de datos se enriquece muchísimo,
lo que tiene un efecto transformador en el modelo.
