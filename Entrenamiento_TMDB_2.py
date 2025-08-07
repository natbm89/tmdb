
import pandas as pd
import numpy as np
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Conexión BD

conn = None
cursor = None
df = None
try:
    conn = psycopg2.connect(
        host = "database-1.cb40saqeczhj.eu-north-1.rds.amazonaws.com",
        user = "postgres",
        password = "hackaboss2025",
        database = "TMDB",
        port = 5432,
    )
    print("Conectado a la base de datos.")

# Cargamos y unimos las tablas

    cursor = conn.cursor()
    
    query = """
        SELECT
            p.movie_id,
            p.titulo,
            p.release_date,
            p.duracion,
            p.vote_average,
            p.vote_count,
            p.revenue,
            p.budget,
            g.nombre AS genero
        FROM
            peliculas p
        JOIN
            peliculas_generos pg ON p.movie_id = pg.movie_id
        JOIN
            generos g ON pg.genero_id = g.genero_id;
    """

    cursor.execute(query)

    data = cursor.fetchall()

#Preparamos los datos para el DataFrame

    column_names = [desc[0] for desc in cursor.description]

    df = pd.DataFrame(data, columns=column_names)
    print("Datos cargados exitosamente.")

# Modificicación para solventar los valores no númericos 
# Convertir columnas a tipo numérico
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce')
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce')

# df['revenue'] = df['revenue'].replace(0, np.nan) ó
    df['budget'] = df['budget'].replace(0, np.nan) #?


except psycopg2.OperationalError as e:
    print(f"Error de conexión a la base de datos: {e}")

except Exception as e:
    print(f"Ocurrió un error al cargar los datos: {e}")

finally:
    
    if cursor:
        cursor.close()
    if conn and conn.closed is False:
        conn.close()
        print("Conexión a la base de datos cerrada.")


# Exploramos datos -----Modificamos eliminando valores nulos y 
# aplicando una escala logarítmica para trabajar con cantidades altas----

if df is not None:
    print("Primeras 5 filas del DataFrame: ", df.head())

    print("\nInformación del DataFrame: ", df.info())
   
    print("\nConteo de valores nulos por columna: ", df.isnull().sum())

    df_cleaned = df.dropna(subset=['revenue', 'vote_average']) #modifiación


# Checkeamos los datos con gráficas

    plt.style.use('fivethirtyeight')
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('Distribución de Variables', fontsize=16)

    # Distribución de revenue
    # sns.histplot(df['revenue'].dropna(), bins=50, kde=True, ax=axes[0])
    # axes[0].set_title('Distribución de Revenue')
    # axes[0].set_xlabel('Revenue')
    # axes[0].set_ylabel('Frecuencia')

    #Modificación ^
     # Distribución de revenue con escala logarítmica
    sns.histplot(df_cleaned['revenue'], bins=50, kde=True, ax=axes[0])
    axes[0].set_title('Distribución de Ingresos')
    axes[0].set_xlabel('Revenue')
    axes[0].set_ylabel('Frecuencia')
    axes[0].set_xscale('log') # Aplicamos escala logarítmica aquí

    if (df_cleaned['revenue'] > 0).any():
        axes[0].set_xscale('log')
    else:
        print("Advertencia: Por ahpa no hay valores de 'revenue' mayores que cero para aplicar escala logarítmica.")


    # Distribución de vote_average
    # sns.histplot(df['vote_average'].dropna(), bins=20, kde=True, ax=axes[1])
    # axes[1].set_title('Distribución de Vote Average')
    # axes[1].set_xlabel('Vote Average')
    # axes[1].set_ylabel('Frecuencia')

    #Modificación ^
    sns.histplot(df_cleaned['vote_average'], bins=20, kde=True, ax=axes[1])
    axes[1].set_title('Distribución de Vote Average')
    axes[1].set_xlabel('Vote Average')
    axes[1].set_ylabel('Frecuencia')

    # Distribución de budget
    # sns.histplot(df['budget'].dropna(), bins=50, kde=True, ax=axes[2])
    # axes[2].set_title('Distribución de Budget')
    # axes[2].set_xlabel('Budget')
    # axes[2].set_ylabel('Frecuencia')

    #Modificación ^    sns.histplot(df_cleaned['budget'], bins=50, kde=True, ax=axes[2])
    axes[2].set_title('Distribución de Budget')
    axes[2].set_xlabel('Budget')
    axes[2].set_ylabel('Frecuencia')
    axes[2].set_xscale('log') # Aplicamos escala logarítmica aquí

# Para evitar errores con log(0), aplicamos log solo a valores > 0
    if (df_cleaned['budget'] > 0).any():
        axes[2].set_xscale('log')
    else:
        print("Advertencia: Por ahora no hay valores de 'budget' mayores que cero para aplicar escala logarítmica.")



    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


# Métrica de Éxito y Variable objetivo
# Vamos a considerar que el éxito tiene relación con un revenue superior a la mediana del resto,
# y que el vote_average debe ser superior a 6.5

# Definimos los umbrales

    # umbral_revenue = df['revenue'].median()
    # umbral_vote_average = 6.5

    #modificación ^ Usando la df limpia
    umbral_revenue = df_cleaned['revenue'].median()
    umbral_vote_average = 6.5

# Función para determinar el éxito


    def determinar_exito(axis):
        if (axis['revenue'] > umbral_revenue) and (axis['vote_average'] > umbral_vote_average):
            return 1
        else:
            return 0

# Creamos la variable 'exito' (1 para éxito, 0 para fracaso)

    # df['exito'] = df.apply(determinar_exito, axis=1)

    #Modificicación ^
    df_cleaned['exito'] = df_cleaned.apply(determinar_exito, axis=1) 

    print(f"Umbral de Revenue: {umbral_revenue}")
    print(f"Umbral de Vote Average: {umbral_vote_average}")
    print("\nDistribución de la variable 'exito':")
    # print(df['exito'].value_counts())
    #Modificación ^
    print (df_cleaned['exito'].value_counts())

#-------------LAS MODIFICACIONES LLEGAN HASTA AQUÍ---------
# Por ahora la escala logarítmica no es útil, pero limpiar los datos sirven para las
# métricas aunque con budget no lo tengo claro.
# Y aunque hay muchos vote average a cero, sirve para clasificar el éxito
# porque o bien no se han visto o no han impactado ni para bien o mal
# como para tomarse la molestia como para valorarlas (por tanto no éxito)
#------------------------------------------------------------

# Preparamos los datos para el modelo

# Rellenamos con la media(por ahora para poder ir avanzando)

    cols_fillna = ['duracion', 'revenue', 'budget', 'vote_average', 'vote_count']

    for col in cols_fillna:
        if col in df.columns: 
            df[col].fillna(df[col].mean(), inplace=True)


# Para género usamos One-Hot Encoding

    if 'genero' in df.columns:
        df['genero'].fillna('Desconocido', inplace=True) 
        df_encoded = pd.get_dummies(df.drop_duplicates(subset=['movie_id']), columns=['genero'], prefix='genero')
    else:
        df_encoded = df.drop_duplicates(subset=['movie_id']).copy()

# Para asegurarnos de que no hay duplicados

    df_final = df_encoded

# Definimos las variables X e Y

    cols_to_drop = ['movie_id', 'titulo', 'release_date', 'exito']
    X = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns], axis=1)
    y = df_final['exito']

    print(f"Forma de las variables predictoras (X): {X.shape}")
    print(f"Forma de la variable objetivo (y): {y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Tamaño del conjunto de entrenamiento: {X_train.shape[0]} muestras")
    print(f"Tamaño del conjunto de prueba: {X_test.shape[0]} muestras")



# Entrenamiento 

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)

    model = RandomForestClassifier(n_estimators=100, random_state=42)

    model.fit(X_train_scaled, y_train)

    print("Modelo entrenado con éxito.")


#Evaluación

    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Precisión del modelo: {accuracy:.2f}")

# Vemos precision, recall y f1-score
    print(classification_report(y_test, y_pred))

# Matriz de confusión
    cm = confusion_matrix(y_test, y_pred)
    print("\nMatriz de Confusión:")
    print(cm)

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.title('Matriz de Confusión')
    plt.xlabel('Predicción')
    plt.ylabel('Real')
    plt.show()


else:
    print("No se pudo cargar el DataFrame. El resto del script no se ejecutará.")