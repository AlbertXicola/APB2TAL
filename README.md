-------------
*APB2TAL 98%*
-------------

PAU, MAX, ALBERT


Requeriments
============


-  pip install django
-  pip install djongo
-  pip install pymongo django-mongodb-engine
-  pip install requests
-  pip install django-admin-tools
-  pip install django-avatar
-  pip install cryptography
-  pip install python-dotenv



Activar
=======
cd .\Desktop\
cd .\Proyecto\
.\myenv\Scripts\Activate.ps1
cd .\APB2AL\
python manage.py runserver


-  django-admin startproject APB2TAL .	-->>>   Crear Proyecto

-  python manage.py migrate 		    -->>>	Aplica las migraciones pendientes a la base de datos.

-  python manage.py makemigrations		-->>>	Genera archivos de migración basados en los cambios que has realizado en tus modelos.

-  python manage.py createsuperuser 	-->>>   Crear Admin

-  python manage.py startapp nombre	    -->>>   Crear App

-  python manage.py runserver	        -->>>   Iniciar Servidor Web


Tener un mongo corriendo (puerto 27018 para servidor mongo)
===========================================================

- Facil con docker Pull Mongo y conectar a dicho puerto
