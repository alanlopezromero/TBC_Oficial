import sqlite3
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name="TU_CLOUD_NAME",
    api_key="TU_API_KEY",
    api_secret="TU_API_SECRET",
    secure=True
)

DB_IMAGENES = "imagenes.db"


def guardar_imagen(categoria, file, descripcion):
    # Subir a Cloudinary
    resultado = cloudinary.uploader.upload(
        file,
        folder=categoria
    )

    url = resultado["secure_url"]
    public_id = resultado["public_id"]

    # Guardar en SQLite
    conn = sqlite3.connect(DB_IMAGENES)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO imagenes (categoria, url, public_id, descripcion)
    VALUES (?, ?, ?, ?)
    """, (categoria, url, public_id, descripcion))

    conn.commit()
    conn.close()
