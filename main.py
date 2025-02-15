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

#Indicamos donde encontrar el archivo csv
nltk.data.path.append('C:/Users/danys/AppData/Local/Programs/Python/Python312/Lib/site-packages/nltk')
#descargamos las herramientas necesarias de nltk para procesar textos y analizarlos
nltk.download('punkt') #paquete para dividir el texto en palabras
nltk.download('wordnet') #paquete para obtener sinonimos de las palabras en inglés
nltk.download('punkt_tab') #consejo para error interno del servidor error 500

def load_questions():
    #Leemos el archivo csv que contiene las preguntas y respuestas
    df=pd.read_csv("../WhattWise/DataSet/energia.csv",  encoding='iso-8859-1')[['version','name','applied_at']]
    
    #Renombramos las columnas del dataframe
    df.columns=["id","pregunta","respuesta"]
    return df.fillna('').to_dict(orient='records')
#Cargamos las preguntas al iniciar la aplicación para no leer el archivo csv en cada solicitud
pregunta_list=load_questions()

#función para obtener los sinonimos de una palabra
def get_synonyms(word):
    #Usamos wordnet para obtener los sinonimos de una palabra
    return{lemma.name().lower() for syn in wordnet.synsets(word) for lemma in syn.lemmas()}

#Creamos una instancia de la clase FastAPI que sea el motor de nuestra aplicación
#Esto inicializa la app con un titulo y una version
app=FastAPI(title="WattWise: ChatBot de Ahorro Energético", version="0.0.1")

#Cuando alguien ingresa a la app sin especificar una ruta, verá un mensaje de bienvenida
@app.get("/", tags=["Inicio"])
def inicio():
    #Cuando entremos en el navegador a http://127.0.0.1:8000 nos mostrara el siguiente mensaje
    return HTMLResponse(content="<h1>Bienvenido a WattWise</h1>")

#Obteniendo la lista de preguntas
#Creamos una ruta que nos permita obtener la lista de preguntas y respuestas

#Ruta para obtener todas las preguntas
@app.get("/preguntas", tags=["Preguntas"])
def preguntas():
    #Si hay preguntas las enviamos, sino, mostramos un mensaje de error
    return pregunta_list or HTTPException(status_code=500, detail="No hay preguntas disponibles")
#Ruta para obtener una sola pregunta
@app.get("/preguntas/{id}", tags=["Preguntas"])
def pregunta(id:int):
    #Buscamos la pregunta en la lista de preguntas la buscamos por su id
    return next((p for p in pregunta_list if p['id'] == id), {"Detalle":"Pregunta no encontrada"})


#Ruta del chatbot que responde a las preguntas con palabras clave de la categoria

@app.get('/chatbot', tags=["Chatbot"])
def chatbot(query: str):
    #Dividimos la pregunta en palabras clave para entender mejor la intención del usuario
    query_words = word_tokenize(query.lower())
    
    #Buscamos sinonimos de las palabras clave para ampliar la busqueda
    synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)
    
    #Filtramos la lista de las preguntas buscando coincidencias con las palabras clave
    results=[p for p in pregunta_list if any(s in p['respuesta'].lower() for s in synonyms)]
    
    #Si hay resultados, los enviamos, sino, mostramos un mensaje de error
    return JSONResponse(content={
        "Respuesta": "Aquí tienes algunas preguntas relacionadas: " if results else "No encontré preguntas en esa categoría.", "Respuesta": results
    })
    
# Ruta para buscar respuestas por palabra clave
@app.get("/preguntas/{keyword}", tags=["Preguntas"])
def buscar_pregunta(keyword: str):
    # Filtramos la lista de respuestas por palabra clave 
    return [p for p in pregunta_list if keyword.lower() in p['pregunta'].lower()]
    
""" preguntas =[
    {
        "id":1,
        "pregunta 1":"¿Qué es el ahorro energético?",
        "respuesta 1":"El ahorro energético es la práctica de reducir el consumo de energía mediante la optimización de los procesos de producción y el uso eficiente de la energía.",
    },
    {
        "id":2,
        "pregunta 2":"¿Cómo puedo ahorrar energía en casa?",
        "respuesta 2":"Para ahorrar energía en casa puedes apagar los electrodomésticos que no estés utilizando, utilizar bombillas de bajo consumo y aislar tu hogar para evitar pérdidas de calor.",
    },
    {
        "id":3,
        "pregunta 3":"¿Qué es la eficiencia energética?",
        "respuesta 3":"La eficiencia energética es la relación entre la energía consumida y la energía producida. A mayor eficiencia energética, menor consumo de energía.",
    },
    {
        "id":4,
        "pregunta 4":"¿Cómo puedo ahorrar energía en la oficina?",
        "respuesta 4":"Para ahorrar energía en la oficina puedes apagar los equipos que no estés utilizando, utilizar bombillas de bajo consumo y programar el encendido y apagado de los equipos.",  
    },
    {
        "id":5,
        "pregunta 5":"¿Qué es el consumo fantasma?",
        "respuesta 5":"El consumo fantasma es el consumo de energía de los equipos electrónicos en modo de espera. Para reducir el consumo fantasma, es importante apagar los equipos por completo.",
    },
    {
        "id":6,
        "pregunta 6":"¿Cómo puedo ahorrar energía en la cocina?",
        "respuesta 6":"Para ahorrar energía en la cocina puedes utilizar ollas a presión, tapar las ollas mientras cocinas y utilizar electrodomésticos eficientes.",
    },
    {
        "id":7,
        "pregunta 7":"¿Qué es la energía solar?",
        "respuesta 7":"La energía solar es la energía obtenida a partir de la radiación solar. Para aprovechar la energía solar, se utilizan paneles solares para la captación de la radiación solar.",
    },
    {
        "id":8,
        "pregunta 8":"¿Cómo puedo ahorrar energía en el baño?",
        "respuesta 8":"Para ahorrar energía en el baño puedes utilizar grifos y duchas de bajo consumo, instalar un sistema de reutilización de aguas grises y utilizar bombillas de bajo consumo.",  
    },
    {
        "id":9,
        "pregunta 9":"¿Qué es la energía eólica?",
        "respuesta 9":"La energía eólica es la energía obtenida a partir del viento. Para aprovechar la energía eólica, se utilizan aerogeneradores para la captación de la energía cinética del viento.",
    },
    {
        "id":10,
        "pregunta 10":"¿Cómo puedo ahorrar energía en el jardín?",
        "respuesta 10":"Para ahorrar energía en el jardín puedes utilizar sistemas de riego eficientes, plantar árboles para proporcionar sombra y utilizar bombillas de bajo consumo."
    }
]

app = FastAPI() #Creamos una instancia de la clase FastAPI
app.title = "WattWise: ChatBot de Ahorro Energético" #Definimos el titulo de la aplicación
app.version = "0.0.1" #Definimos la versión de la aplicación

@app.get('/', tags=["Inicio"])#Definimos la ruta raiz
def message():#Definimos una función de la ruta raiz
    return HTMLResponse(content="<h1>Bienvenido a WattWise</h1>", status_code=200)

@app.get('/chatbot/{id}', tags=["ChatBot"])#Definimos la ruta chatbot con un parámetro id
def chatbot(id: int):
    for item in preguntas:#Recorremos la lista preguntas
        if item["id"] == id:#Si el id de la pregunta es igual al id pasado como parámetro
            return item
        return[]
@app.get('/preguntas', tags=["Preguntas"])#Definimos la ruta preguntas
def buscarPregunta(pregunta: str, respuesta: str):
    return [item for item in preguntas if item["pregunta"] == pregunta and item["respuesta"] == respuesta]  
    


 """
