from flask import Flask
import pymongo
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


app.secret_key="sdsadasd233242"
app.config['UPLOAD_FOLDER']='./static/imagenes'
miConexion = pymongo.MongoClient("mongodb://localhost:27017/")
baseDatos = miConexion['Tienda']
productos = baseDatos['productos']

usuarios = baseDatos['usuarios']

if __name__=="__main__":
    from controlador.apiController import *
    from controlador.usuarioController import * 

    app.run(port=9000,debug=True)
    
    
