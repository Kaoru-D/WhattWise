#Este Proyecto se trata sobre un ChatBot que te resueva dudas sobre ahorro enegético
#Autores: Daniel Pulgarin Bedoya, Luisa Fernanda Rios Arias y German Buritica
#Fecha: 2025-02-26
#importamos la clase FastAPI del framework FastAPI
from fastapi import FastAPI, HTTPException#hhtp exceptions maneja errores
from fastapi.responses import HTMLResponse, JSONResponse #Importamos la clase HTMLResponse de la libreria fastapi.responses
import pandas as pd #Nops ayuda a manejar dataframes con tablas dinámicas 
import nltk #Nltk es una libreria para procesar textos y analizarlos
from nltk.tokenize import word_tokenize #Se usa para dividir el texto en palabras
from nltk.corpus import wordnet #Se usa para obtener sinonimos de las palabras
from fastapi.templating import Jinja2Templates #Se usa para renderizar templates
from starlette.requests import Request #Se usa para manejar solicitudes HTTP
from fastapi.staticfiles import StaticFiles #Se usa para servir archivos estáticos
from nltk.corpus import stopwords #Se usa para obtener sinonimos de las palabras
import string #Se usa para manejar cadenas de texto

#-------------------Librerias para entrenar el ChatBot-------------------   
#Librerias para procesar textos y analizarlos
from sentence_transformers import SentenceTransformer #Se usa para obtener embeddings de las preguntas
import numpy as np #Se usa para manejar matrices numéricas
from sklearn.metrics.pairwise import cosine_similarity #Se usa para calcular la similaridad entre embeddings
import faiss #Se usa para indexar embeddings

nltk.download('averaged_perceptron_tagger')# Esta función obliga a que la libreria nltk se descargue en el la carpeta predeterminada
#Indicamos donde encontrar el archivo csv
#descargamos las herramientas necesarias de nltk para procesar textos y analizarlos
nltk.download('punkt') #paquete para dividir el texto en palabras
nltk.download('punkt_tab') #consejo para error interno del servidor error 500
nltk.download('omw-1.4')  # Mejor paquete para wordnet en varios idiomas
nltk.download('stopwords') #paquete para limpiar el texto de palabras innecesarias



# Cargar modelo de embeddings
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Función para preprocesar el texto
def preprocess_text(text: str):
    text = text.lower()
    text = ''.join([char for char in text if char not in string.punctuation])
    tokens = word_tokenize(text, language='spanish')
    stop_words = set(stopwords.words('spanish'))
    return ' '.join([word for word in tokens if word not in stop_words])


def load_questions():
    try:
        df = pd.read_csv("dataSet/energia.csv", encoding='utf-8-sig')[['version', 'name', 'applied_at']] # minúsculas para sistemas UNIX
        df.columns = ["id", "pregunta", "respuesta"]
        df['pregunta_limpia'] = df['pregunta'].apply(preprocess_text)
        preguntas_limpias = df['pregunta_limpia'].tolist()
        # Convertir preguntas a embeddings
        preguntas = df['pregunta'].tolist()
        respuestas = df['respuesta'].tolist()
        embeddings = model.encode(preguntas)
        # Convertir embeddings a FAISS
        faiss.normalize_L2(embeddings) #Se usa para normalizar embeddings
        index = faiss.IndexFlatIP(embeddings.shape[1])# Se usa para indexar embeddings|
        index.add(embeddings)
        return {
        # ... (código existente)
        "data": df.to_dict(orient='records'),
        "preguntas": preguntas_limpias,
        "respuestas": df['respuesta'].tolist(),
        "embeddings": embeddings,
        "faiss_index": index
    }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando datos: {str(e)}")
#Cargamos las preguntas al iniciar la aplicación para no leer el archivo csv en cada solicitud
preguntaDatos=load_questions()
pregunta_list = preguntaDatos["data"]
preguntas = preguntaDatos["preguntas"]
respuestas = preguntaDatos["respuestas"]
embeddings = preguntaDatos["embeddings"]
indexF= preguntaDatos["faiss_index"]


#función para obtener los sinonimos de una palabra
def get_synonyms(word):
    #Usamos wordnet para obtener los sinonimos de una palabra
    return{lemma.name().lower() for syn in wordnet.synsets(word) for lemma in syn.lemmas()}

#Creamos una instancia de la clase FastAPI que sea el motor de nuestra aplicación
#Esto inicializa la app con un titulo y una version
app=FastAPI(title="WattWise: ChatBot de Ahorro Energético", version="0.0.5")

app.mount("/templates/dist", StaticFiles(directory="templates/dist"), name="static")
# Configuramos la carpeta de templates
templates = Jinja2Templates(directory="../WhattWise-master")


# Ruta de inicio que devuelve el archivo HTML
@app.get("/", tags=["Inicio"])
def inicio(request: Request):
    #Cuando entremos en el navegador a http://127.0.0.1:8000 nos mostrara el siguiente mensaje
    return templates.TemplateResponse("index.html", {"request": request})

#Obteniendo la lista de preguntas
#Creamos una ruta que nos permita obtener la lista de preguntas y respuestas

#Ruta para obtener todas las preguntas
@app.get("/preguntas", tags=["Preguntas"])
def preguntas():
    if pregunta_list:
        return pregunta_list
    raise HTTPException(status_code=500, detail="❌ No hay preguntas disponibles.")#muestra un error en caso de que no haya preguntas

#Ruta para obtener una sola pregunta
@app.get("/preguntas/id/{id}", tags=["Preguntas"])# Se coloca /id para que la ruta no sea ambigua
def pregunta(id:int):
    #Buscamos la pregunta en la lista de preguntas la buscamos por su id
    pregunta = next((p for p in pregunta_list if p['id'] == id), None)
    if pregunta:
        return pregunta
    raise HTTPException(status_code=404, detail="⚠️ Pregunta no encontrada")


#Ruta del chatbot que responde a las preguntas con palabras clave de la categoria
# Modifica la función del chatbot
SIMILARITY_THRESHOLD = 0.5  # Ajusta este valor según pruebas

@app.get('/chatbot', tags=["Chatbot"])
def chatbot(pregunta_usuario: str):
    
    #------Verificar que la pregunta no este vacia------
    if not pregunta_usuario.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    
    if embeddings is None:
        raise HTTPException(status_code=500, detail="❌ No hay preguntas disponibles.")
    
    #------analisis de sintaxis------
    embedding_usuario = model.encode([preprocess_text(pregunta_usuario)])[0].reshape(1, -1)
    faiss.normalize_L2(embedding_usuario) 
    similitudes, indices = indexF.search(embedding_usuario, k=3)
      
    # Tomar la mejor respuesta entre las 3 más similares
    best_match_idx = indices[0][0]
    max_similitud = similitudes[0][0]
    
    if max_similitud < SIMILARITY_THRESHOLD:
        return {"Respuesta": "No encontré una respuesta adecuada. Intenta esta pregunta ¿cómo puedo reducir el consumo de energía en mi hogar?"}
    
    return {"Respuesta": respuestas[best_match_idx]}


# Ruta para buscar respuestas por palabra clave
@app.get("/preguntas/keyword/{keyword}", tags=["Preguntas"])
def buscar_pregunta(keyword: str):
    # Filtramos la lista de respuestas por palabra clave 
    resultados = [p for p in pregunta_list if keyword.lower() in p['pregunta'].lower()]
    if resultados:
        return resultados
    raise HTTPException(status_code=404, detail="⚠️ No se encontraron preguntas con esa palabra clave")
    