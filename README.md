# APB2TAL 99% Readme

## Integrantes
- Albert Xicola
- Pau Cañadillas
- Max Thomas

## Requisitos Previos

- Python 3.x: Descarga e instala desde [Python.org](https://www.python.org/downloads/)
- Virtualenv: Instálalo utilizando los siguientes comandos en tu terminal:

    ```bash
    python3 -m pip install --upgrade pip
    pip3 install virtualenv
    ```

## Instrucciones de Instalación y Ejecución (Windows)

1. Crea un entorno virtual y actívalo ejecutando los siguientes comandos en tu terminal:

    ```bash
    python3 -m venv entornovirtual
    .\entornovirtual\Scripts\activate
    ```

2. Clona el repositorio y navega hasta la carpeta:

    ```bash
    git clone https://github.com/AlbertXicola/APB2TAL.git
    cd .\APB2TAL\
    ```

3. Instala las dependencias utilizando el gestor de paquetes pip:

    ```bash
    pip install -r requirements.txt
    ```

4. Ejecuta las migraciones de la base de datos:

    ```bash
    python manage.py migrate
    ```

5. Inicia el servidor:

    ```bash
    python manage.py runserver
    ```

## Instrucciones de Instalación y Ejecución (Linux)

1. Crea un entorno virtual y actívalo ejecutando los siguientes comandos en tu terminal:

    ```bash
    python3 -m venv entornovirtual
    source entornovirtual/bin/activate
    ```

2. Clona el repositorio y navega hasta la carpeta:

    ```bash
    git clone https://github.com/AlbertXicola/APB2TAL.git
    cd APB2TAL/
    ```

3. Instala las dependencias utilizando el gestor de paquetes pip:

    ```bash
    pip install -r requirements.txt
    ```

4. Ejecuta las migraciones de la base de datos:

    ```bash
    python manage.py migrate
    ```

5. Inicia el servidor:

    ```bash
    python manage.py runserver
    ```

## Configuración de MongoDB (Docker) NECESARIO

1. Descarga e instala Docker Desktop desde [Docker.com](https://docs.docker.com/desktop/install/windows-install/)

2. Descarga la imagen de MongoDB utilizando el siguiente comando en tu terminal:

    ```bash
    docker pull mongo
    ```

3. Ejecuta el contenedor de MongoDB:

    ```bash
    docker run -d -p 27018:27017 --name django_mongo mongo:latest
    ```

## Supervisión de Logs de MongoDB

Si deseas supervisar manualmente los logs de MongoDB, sigue estos pasos:

1. Descarga MongoDB Compass desde [MongoDB.com](https://www.mongodb.com/try/download/shell)

2. Conéctate a MongoDB utilizando la siguiente URL:

    ```
    mongodb://localhost:27018/
    ```

## Información Adicional

### Credenciales Administrador

- Usuario: admin
- Contraseña: Asdewq123@

### Visualización de la Base de Datos SQLite

Si deseas ver las tablas y los datos de la base de datos, sigue estos pasos:

1. Instala SQLiteStudio desde [sqlitestudio.pl](https://sqlitestudio.pl/)

2. Abre el archivo `db.sqlite3` (ubicado en la raíz del repositorio) en la aplicación descargada.

## Advertencia

Asegúrate de haber configurado correctamente el archivo `settings.py`:
(Solo si es necesario ya esta en False)

- `DEBUG = False`: Modo Producción.
- `DEBUG = True`: Activa el modo de errores.
