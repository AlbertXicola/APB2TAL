-------------
*APB2TAL 60%*
-------------

PAU, MAX, ALBERT


Requeriments
============


-  pip install django
-  pip install djongo
-  pip install pymongo django-mongodb-engine
-  pip install requests
-  pip install django-admin-tools



Activar
=======
cd .\Desktop\
cd .\Proyecto\
.\myenv\Scripts\Activate.ps1
cd .\APB2AL\
python manage.py runserver


django-admin startproject APB2TAL .	-->>>   crear Proyecto
python manage.py migrate 		        -->>>	  Aplica las migraciones pendientes a la base de datos.
python manage.py makemigrations		  -->>>	  Genera archivos de migración basados en los cambios que has realizado en tus modelos.

python manage.py createsuperuser 	  -->>>   crear Admin

python manage.py startapp nombre	  -->>>   crear App

python manage.py runserver


