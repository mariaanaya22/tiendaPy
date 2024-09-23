from app import app, productos
from flask import request, jsonify, redirect, render_template, session, flash
import pymongo
import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError

@app.route("/listarProductos")
def inicio():
    if "user" in session:
        try:
            mensaje = ""
            listaProductos = productos.find()
            return render_template("listarProductos.html", productos=listaProductos, mensaje=mensaje)
        except PyMongoError as error:
            mensaje = str(error)
            return render_template("listarProductos.html", mensaje=mensaje)
    else:
        mensaje = "Debe primero ingresar con sus credenciales"
        return render_template("frmLogin.html", mensaje=mensaje)

@app.route("/agregar", methods=['POST', 'GET'])
def agregar():
    if "user" in session:
        producto = None  # Inicializa la variable
        mensaje = ""
        if request.method == 'POST':
            try:
                if 'txtCodigo' in request.form and request.form['txtCodigo'].isdigit():
                    codigo = int(request.form['txtCodigo'])
                else:
                    mensaje = "El código del producto debe ser un número válido."
                    return render_template("frmAgregarProducto.html", mensaje=mensaje, producto=producto)

                nombre = request.form['txtNombre']
                precio = int(request.form['txtPrecio'])
                categoria = request.form['cbCategoria']
                foto = request.files['fileFoto']
                nombreArchivo = secure_filename(foto.filename)
                extension = nombreArchivo.rsplit(".", 1)[1].lower()
                nombreFoto = f"{codigo}.{extension}"

                producto = {
                    "codigo": codigo, "nombre": nombre, "precio": precio, 
                    "categoria": categoria, "foto": nombreFoto
                }

                if not existeProducto(codigo):   
                    resultado = productos.insert_one(producto)
                    if resultado.acknowledged:
                        mensaje = "Producto Agregado Correctamente"
                        foto.save(os.path.join(app.config["UPLOAD_FOLDER"], nombreFoto))
                        return redirect('/listarProductos')
                    else:
                        mensaje = "Problemas al agregar el producto."
                else:
                    mensaje = "Ya existe un producto con ese código"
            except PyMongoError as error:
                mensaje = str(error)

        return render_template("frmAgregarProducto.html", mensaje=mensaje, producto=producto)
    else:
        mensaje = "Debe primero ingresar con sus credenciales"
        return render_template("frmLogin.html", mensaje=mensaje)


@app.route("/consultar/<string:id>", methods=["GET"])
def consultar(id):
    if "user" in session:
        try:
            id = ObjectId(id)
            producto = productos.find_one({"_id": id})
            return render_template("frmActualizarProducto.html", producto=producto)
        except PyMongoError as error:
            mensaje = str(error)
            return redirect("/listarProductos", mensaje=mensaje)
    else:
        mensaje = "Debe primero ingresar con sus credenciales"
        return render_template("frmLogin.html", mensaje=mensaje)

def existeProducto(codigo):
    try:
        return productos.find_one({"codigo": codigo}) is not None
    except PyMongoError as error:
        print(f"Error verificando existencia del producto: {error}")
        return False

@app.route("/actualizar", methods=["POST"])
def actualizarProducto():
    if "user" in session:
        try:
            codigo = int(request.form["txtCodigo"])
            nombre = request.form["txtNombre"]
            precio = int(request.form["txtPrecio"])
            categoria = request.form["cbCategoria"]
            id = ObjectId(request.form["id"])
            foto = request.files["fileFoto"]

            producto = {
                "_id": id,
                "codigo": codigo,
                "nombre": nombre,
                "precio": precio,
                "categoria": categoria
            }

            # Manejo de archivo
            if foto and foto.filename:
                nombreArchivo = secure_filename(foto.filename)
                extension = nombreArchivo.rsplit(".", 1)[1].lower()
                nombreFoto = f"{codigo}.{extension}"
                producto["foto"] = nombreFoto

            # Verificación de existencia de código
            existe = productos.find_one({"codigo": codigo, "_id": {"$ne": id}})
            if existe:
                mensaje = "Producto ya existe con ese código"
                return render_template("frmActualizarProducto.html", producto=producto, mensaje=mensaje)

            resultado = productos.update_one({"_id": id}, {"$set": producto})
            if resultado.acknowledged:
                if foto and foto.filename:
                    foto.save(os.path.join(app.config["UPLOAD_FOLDER"], nombreFoto))
                flash("Producto Actualizado")
                return redirect("/listarProductos")
        except PyMongoError as error:
            return redirect("/listarProductos", mensaje=str(error))
    else:
        mensaje = "Debe primero ingresar con sus credenciales"
        return render_template("frmLogin.html", mensaje=mensaje)

@app.route("/eliminar/<string:id>")
def eliminar(id):
    if "user" in session:
        try:
            id = ObjectId(id)
            producto = productos.find_one({"_id": id})
            nombreFoto = producto.get('foto', "")
            resultado = productos.delete_one({"_id": id})

            if resultado.acknowledged and nombreFoto:
                rutaFoto = os.path.join(app.config['UPLOAD_FOLDER'], nombreFoto)
                if os.path.exists(rutaFoto):
                    os.remove(rutaFoto)
                flash("Producto Eliminado")
        except PyMongoError as error:
            flash(str(error))
        return redirect("/listarProductos")
    else:
        mensaje = "Debe primero ingresar con sus credenciales"
        return render_template("frmLogin.html", mensaje=mensaje)

@app.route("/api/listarProductos", methods=["GET"])
def apiListarProductos():
    listaProductos = productos.find()
    lista = [{
        "_id": str(p['_id']),
        "codigo": p['codigo'],
        "nombre": p['nombre'],
        "precio": p['precio'],
        "categoria": p['categoria'],
        "foto": p['foto']
    } for p in listaProductos]
    return jsonify({'productos': lista})

@app.route("/api/consultar/<string:id>", methods=["GET"])
def apiConsultar(id):
    p = productos.find_one({"_id": ObjectId(id)})
    producto = {
        "_id": str(p['_id']),
        "codigo": p['codigo'],
        "nombre": p['nombre'],
        "precio": p['precio'],
        "categoria": p['categoria'],
        "foto": p['foto']
    }
    return jsonify({'producto': producto})

@app.route("/api/agregar", methods=["POST"])
def apiAgregarP():
    try:
        codigo = int(request.json['codigo'])
        nombre = request.json['nombre']
        precio = int(request.json['precio'])
        categoria = request.json['categoria']
        foto = request.json['foto']  # Aquí deberías manejar la foto de forma diferente

        producto = {
            "codigo": codigo,
            "nombre": nombre,
            "precio": precio,
            "categoria": categoria,
            "foto": foto  # Asumiendo que la foto es una URL o similar
        }

        if not existeProducto(codigo):
            resultado = productos.insert_one(producto)
            mensaje = "Producto Agregado Correctamente" if resultado.acknowledged else "Problemas al agregar el producto."
        else:
            mensaje = f"Ya existe un producto con el código {codigo}"

    except PyMongoError as error:
        mensaje = str(error)

    return jsonify({"mensaje": mensaje})
