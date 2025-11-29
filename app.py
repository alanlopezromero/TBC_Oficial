from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
import sqlite3
import cloudinary
import cloudinary.uploader

from urllib.parse import unquote

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# Configuración de Cloudinary

cloudinary.config(
  cloud_name = "dnfgqlzoq",
  api_key = "821424853667995",
  api_secret = "4Zcph-t8j3atCR4XgzfEeNg4cMA"
)

# Categorías disponibles
CATEGORIAS = {
    'eventos_escolares': 'Eventos Escolares',
    'actividades_deportivas': 'Actividades Deportivas y Culturales',
    'calendario_escolar': 'Calendario Escolar',
    'calificaciones': 'Calificaciones',
    'proyectos_escolares': 'Proyectos Escolares'
}
AVISOS = []  # Avisos temporales en memoria

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html', categorias=CATEGORIAS)

@app.route('/galeria/<categoria>')
def galeria_categoria(categoria):
    categoria = categoria.strip()
    imagenes = []
    archivo = f'datos_{categoria}.txt'
    
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            for linea in f:
                try:
                    partes = linea.strip().split('|')
                    if len(partes) >= 2:
                        descripcion = partes[2] if len(partes) > 2 else ''
                        imagenes.append((partes[0], descripcion))
                    elif len(partes) == 1:
                        imagenes.append((partes[0], ''))
                except Exception as e:
                    print(f"Error procesando línea: {linea} - {e}")
    
    return render_template('galeria_categoria.html', imagenes=imagenes, categoria=categoria, categorias=CATEGORIAS)



@app.route('/login/director', methods=['GET', 'POST'])
def login_director():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        if usuario == 'TBC' and contraseña == '1234':
            session['director_logueado'] = True
            return redirect(url_for('panel_director'))
        else:
            error = 'Usuario o contraseña incorrectos'
            return render_template('login_director.html', error=error)

    return render_template('login_director.html')

@app.route('/panel/director')
def panel_director():
    if not session.get('director_logueado'):
        return redirect(url_for('login_director'))

    imagenes_por_categoria = {}

    for categoria_key in CATEGORIAS:
        imagenes = []
        # Trae todas las imágenes dentro de la carpeta de la categoría
        resultado = cloudinary.api.resources(
            type='upload',
            prefix=f'galeria/{categoria_key}',
            max_results=500  # ajusta según cuántas imágenes esperes
        )

        for item in resultado['resources']:
            imagenes.append({
                'url': item['secure_url'],
                'public_id': item['public_id'],
                'descripcion': item.get('context', {}).get('custom', {}).get('descripcion', '')
            })

        imagenes_por_categoria[categoria_key] = imagenes

    # Cargar mensajes desde la base de datos
    conn = sqlite3.connect('mensajes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, correo, contenido FROM mensajes')
    mensajes = cursor.fetchall()
    conn.close()

    return render_template(
        'panel_director.html',
        categorias=CATEGORIAS,
        imagenes_por_categoria=imagenes_por_categoria,
        mensajes=mensajes,
        avisos=AVISOS
    )



@app.route('/eliminar-imagen/<categoria_key>/<path:public_id>', methods=['POST'])
def eliminar_imagen(categoria_key, public_id):
    public_id = unquote(public_id)  # Decodifica los caracteres especiales
    try:
        cloudinary.uploader.destroy(public_id)
        flash("Imagen eliminada correctamente.", 'success')
    except Exception as e:
        flash(f"Error al eliminar la imagen: {e}", 'error')

    return redirect(url_for('panel_director'))




@app.route('/eliminar-mensaje/<int:mensaje_id>', methods=['POST'])
def eliminar_mensaje(mensaje_id):
    if not session.get('director_logueado'):
        return redirect(url_for('login_director'))

    try:
        conn = sqlite3.connect('mensajes.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mensajes WHERE id = ?', (mensaje_id,))
        conn.commit()
        conn.close()
        flash("Mensaje eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar mensaje: {e}", "error")

    return redirect(url_for('panel_director'))

@app.route('/subir-imagen-general', methods=['POST'])
def subir_imagen_general():
    if not session.get('director_logueado'):
        return redirect(url_for('login_director'))

    categoria_key = request.form.get('categoria')
    archivo = request.files.get('imagen')
    descripcion = request.form.get('descripcion', '').strip().replace('|', '')

    if categoria_key not in CATEGORIAS:
        flash('Categoría no válida.', 'error')
        return redirect(url_for('panel_director'))

    if not archivo or archivo.filename == '':
        flash('No seleccionaste ninguna imagen.', 'error')
        return redirect(url_for('panel_director'))

    try:
        resultado = cloudinary.uploader.upload(
            archivo,
            folder=f'galeria/{categoria_key}',
            context=f'caption={descripcion}'
        )
        flash(f'Imagen subida correctamente a {CATEGORIAS[categoria_key]}.', 'success')
    except Exception as e:
        flash(f'Error al subir imagen: {e}', 'error')

    return redirect(url_for('panel_director'))




@app.route('/agregar-aviso', methods=['POST'])
def agregar_aviso():
    if not session.get('director_logueado'):
        return redirect(url_for('login_director'))

    nuevo_aviso = request.form['aviso']
    if nuevo_aviso:
        AVISOS.append(nuevo_aviso)
    return redirect(url_for('panel_director'))

@app.route('/eliminar-aviso/<int:indice>', methods=['POST'])
def eliminar_aviso(indice):
    if not session.get('director_logueado'):
        return redirect(url_for('login_director'))

    if 0 <= indice < len(AVISOS):
        AVISOS.pop(indice)
    return redirect(url_for('panel_director'))

@app.route('/avisos')
def ver_avisos():
    return render_template('ver_avisos.html', avisos=AVISOS)

@app.route('/logout')
def logout():
    session.pop('director_logueado', None)
    return redirect(url_for('index'))

# Páginas alumnos y otras secciones

@app.route('/alumnos/categoria')
def alumnos():
    return render_template('alumnos_categoria.html')

@app.route('/becas')
def becas():
    return render_template('becas.html')

@app.route('/reglamento')
def reglamento():
    return render_template('reglamento.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html') 

@app.route('/paraescolares')
def paraescolares():
    return render_template('paraescolares.html')

@app.route('/ceremonias')
def ceremonias():
    return render_template('ceremonias.html')

@app.route('/aniversario')
def aniversario():
    return render_template('aniversario.html')

@app.route('/tbc')
def tbc():
    return render_template('tbc.html')

@app.route('/misión')
def misión():
    return render_template('misión.html')

@app.route('/equipo')
def equipo():
    return render_template('equipo.html')

@app.route('/mensaje', methods=['GET', 'POST'])
def mensaje():
    mensaje_enviado = False
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contenido = request.form['mensaje']

        try:
            conn = sqlite3.connect('mensajes.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO mensajes (nombre, correo, contenido) VALUES (?, ?, ?)',
                           (nombre, correo, contenido))
            conn.commit()
            conn.close()
            mensaje_enviado = True
            flash('Mensaje enviado correctamente.', 'success')
        except Exception as e:
            flash(f'Error al enviar mensaje: {e}', 'error')

    return render_template('mensaje.html', mensaje_enviado=mensaje_enviado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
