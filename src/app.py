from flask import Flask, request, url_for, render_template, session, flash, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token,JWTManager
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import requests
import random
import os

url = 'https://rickandmortyapi.com/api/character'

######## BLOQUE LISTA PETICIÓN ######
def get_dats():
    respuesta = requests.get(url)
    datos = respuesta.json()

    return datos['results']
######## FIN BLOQUE LISTA PETICIÓN ######

######## BLOQUE N_RANDOM ######
def n_random():
    numero = []

    while len(numero) != 5:
        n = random.randint(0,17)

        if n not in numero:
            numero.append(n)
    return numero
######## FIN BLOQUE N_RANDOM ######

load_dotenv()

app = Flask(__name__)

######## BLOQUE CREDENCIALES ######
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
conexion = MySQL(app)
######## FIN BLOQUE CREDENCIALES ######

######## BLOQUE JWT ######
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.secret_key = 'PAKITO'
######## FIN BLOQUE JWT ######



######## BLOQUE RUTAS BÁSICAS ######
@app.route('/')
def inicio():
    return render_template('inicio.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.errorhandler(404)
def manejar_404(error):
    return render_template('404.html'), 404
######## FIN BLOQUE RUTAS BÁSICAS ######

######## BLOQUE REGISTER ######
@app.route('/register', methods=['POST'])
def register():
    try:
        cursor = conexion.connection.cursor()

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password','')

        password_hash = generate_password_hash(password)

        if not email or not password:
            flash('Faltan datos, completa todos los campos')
            return redirect(url_for('do_register'))

        query1 = 'SELECT email FROM users WHERE email = %s'
        cursor.execute(query1,(email,))
        registrado = cursor.fetchone()

        if registrado:
            flash('Usuario ya registrado, inicia sesión')
            return redirect(url_for('do_login'))
        
        if email == 'admin@admin.com':
            query2 = 'INSERT INTO users(email,password,rol) VALUES(%s,%s,"admin")'

        else:
            query2 = 'INSERT INTO users(email,password) VALUES(%s,%s)'
        
        cursor.execute(query2,(email,password_hash))
        conexion.connection.commit()

        token = create_access_token(identity=email)

        query4 = 'SELECT * FROM users WHERE email = %s'
        cursor.execute(query4,(email,))
        full_user = cursor.fetchone()

        session['id'] = full_user['id']
        session['rol'] = full_user['rol']
        session['token'] = token
        
        datos = get_dats()
        numeros = n_random()

        query3 = 'INSERT INTO favorites(id_user,name,gender,image) VALUES(%s,%s,%s,%s)'

        for i in numeros:
            cursor.execute(query3,(
                full_user['id'],
                datos[i]['name'],
                datos[i]['gender'],
                datos[i]['image']
            ))
        conexion.connection.commit()

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(e)
        return 'A ocurrido un error en el register'
    finally:
        if cursor:
            cursor.close()

@app.route('/register')
def do_register():
    if session.get('token'):
        flash('Este lugar está protegido, cierre sesión para poder acceder')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')
######## FIN BLOQUE REGISTER ######

######## BLOQUE lOGIN ######
@app.route('/login', methods=['POST'])
def login():

    try:
        cursor = conexion.connection.cursor()

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password','')

        if not email or not password:
            flash('Faltan datos, completa todos los campos')
            return redirect(url_for('do_login'))
        
        query1 = 'SELECT password FROM users WHERE email = %s'
        cursor.execute(query1,(email,))
        contrasena = cursor.fetchone()
        print('ESTO ES CONTRASENA', contrasena)

        if not contrasena:
            flash('El usuario no existe')
            return redirect(url_for('do_login'))

        password_check = check_password_hash(contrasena['password'], password)

        if not password_check:
            flash('Los datos no coinciden, pruebe otra vez')
            return redirect(url_for('do_login'))
        
        token = create_access_token(identity=email)

        query4 = 'SELECT * FROM users WHERE email = %s'
        cursor.execute(query4,(email,))
        full_user = cursor.fetchone()

        session['id'] = full_user['id']
        session['rol'] = full_user['rol']
        session['token'] = token

        return redirect(url_for('dashboard'))

    except Exception as e:
        print(e)
        return 'A ocurrido un error en el login'
    finally:
        if cursor:
            cursor.close()

@app.route('/login')
def do_login():
    if session.get('token'):
        flash('Este lugar está protegido, cierre sesión para poder acceder')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')
######## FIN BLOQUE lOGIN ######

######## BLOQUE DASHBOARD ######
@app.route('/dashboard')
def dashboard():
    if not session.get('token'):
        flash('Debes tener una cuenta para acceder a este lugar')
        return redirect(url_for('do_register'))
    try:
        cursor = conexion.connection.cursor()

        id_user = session['id']

        query = 'SELECT * FROM favorites WHERE id_user = %s'
        cursor.execute(query,(id_user,))
        favoritos = cursor.fetchmany(5)
        
        print('ESTO ES FAVORITOS: ', favoritos)

        return render_template('dashboard.html', data = favoritos)
    
    except Exception as e:
        print(e)
        return 'Algo ha fallado en el dashboard'
    
    finally:
        if cursor:
            cursor.close()

######## FIN BLOQUE DASHBOARD ######

######## BLOQUE LOGOUT ######
@app.route('/logout')
def logout():
    if not session:
        flash('No tienes ninguna cuenta, crea o inicia en una')
        return redirect(url_for('do_register'))
    session.clear()
    return redirect(url_for('do_register'))
######## FIN BLOQUE LOGOUT ######

if __name__ == '__main__':
    app.run(debug=True)