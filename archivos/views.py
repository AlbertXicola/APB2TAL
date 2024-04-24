from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import adquisicion
from pymongo import MongoClient
from datetime import datetime
from .forms import TaskForm
from .models import Archivo
from .models import Task, Compartido
import requests
import hashlib
import shutil
import time
import os
from django.http import HttpResponse
import os
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from .models import Archivo, Compartido, adquisicion
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Archivo
from django.shortcuts import get_object_or_404, redirect
from .models import Compartido
from django.http import JsonResponse


def home(request):
    return render(request, 'home.html')

def signup(request):

    if request.method == 'GET':
        return render(request, 'signup.html',{
            'form' : UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'],
                password=request.POST['password1'],email=request.POST['email'],first_name=request.POST['first_name'],last_name=request.POST['last_name'])
                print('username:', request.POST['username'])
                user.save()
                login(request, user)
                return redirect('perfil')
            
            except IntegrityError:
                return render(request, 'signup.html',{
                'form' : UserCreationForm,
                'error' : 'Please enter valid data'
                })

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html',{
            'form' : AuthenticationForm    })
    else:
        user = authenticate(request, username=request.POST['username'], 
                                     password=request.POST['password'])
        if user is None:
            return render(request, 'signin.html',{
            'form' : AuthenticationForm,
            'error': 'Username or password is incorrect'})
            
        else:
            login(request, user)
            return redirect('perfil')

def validar_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)

@login_required
def perfil(request):

    return render(request, 'perfil.html')

def accepted_user_required(view_func):
    decorated_view_func = user_passes_test(
        lambda user: user.is_authenticated and user.is_accepted,
        login_url='/perfil'  # Redirige a la página de perfil si el usuario no tiene is_accepted
    )(view_func)
    return decorated_view_func


@login_required
def signout(request):
    logout(request)
    return redirect('home')


@accepted_user_required
@login_required
def create_task(request):
    
    if request.method == 'GET':
        return render(request,'create_task.html', {
            'form' : TaskForm
        })
    else:
        try:
            form = TaskForm(request.POST)
            new_task = form.save(commit=False)
            new_task.user = request.user
            new_task.save()
            return redirect('tasks')
        
        except ValueError:
            return render(request,'create_task.html', {
                'form' : TaskForm,
                'error' : 'Please provide valid data'
            })


@accepted_user_required
@login_required
def tasks(request):
    tasks = Task.objects.filter(user=request.user)
    
    return render(request, 'tasks.html', {'tasks' : tasks})



@accepted_user_required
@login_required
def tasks_completed(request):
    tasks = Task.objects.filter(user=request.user, completed=True)
    ('-datecompleted')
    return render(request, 'tasks.html', {'tasks' : tasks})


@accepted_user_required
@login_required
def task_detail(request, task_id):
    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id, user=request.user)
        form = TaskForm(instance=task)
        return render(request, 'task_detail.html', {'task': task, 'form': form})
    else:
        try:
            task = get_object_or_404(Task, pk=task_id, user=request.user)
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except ValueError:
            return render(request, 'task_detail.html', {'task': task, 'form': form, 'error': 'Error updating task.'})


@accepted_user_required
@login_required  
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.datecompleted = timezone.now()
        task.save()
        return redirect('tasks')


@accepted_user_required
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('tasks')
    
    
    
def is_staff(user):
    return user.is_authenticated and user.is_staff

@accepted_user_required
@user_passes_test(is_staff, login_url='/')
@login_required
def administrar(request):
    return render(request, 'administrar.html')



@accepted_user_required
@user_passes_test(is_staff)
@login_required
def administrar_usuarios(request):

    usuarios = User.objects.all()

    context = {
        'usuarios': usuarios
    }
    return render(request, 'administrar_usuarios.html', context)

@accepted_user_required
@user_passes_test(is_staff)
@login_required
def admi_usuario(request, id):
    usuario = get_object_or_404(User, id=id)
    
    if request.method == 'POST':
        if 'eliminar' in request.POST:
            usuario.delete()
            return redirect('administrar_usuarios')
        else:
            usuario.username = request.POST.get('username')
            usuario.first_name = request.POST.get('first_name')
            usuario.last_name = request.POST.get('last_name')
            usuario.email = request.POST.get('email')
            usuario.is_active = bool(request.POST.get('is_active'))
            usuario.is_superuser = bool(request.POST.get('is_superuser'))
            usuario.is_staff = bool(request.POST.get('is_staff'))
            usuario.is_accepted = bool(request.POST.get('is_accepted'))

            usuario.save()
            return redirect('administrar_usuarios')
    
    return render(request, 'admi_usuario.html', {'usuario': usuario})

@accepted_user_required
@user_passes_test(is_staff)
@login_required
def administrar_grupos(request):
    grupos = Group.objects.all()  # Obtén todos los grupos

    context = {
        'grupos': grupos  # Agrega los grupos al contexto
    }
    return render(request, 'administrar_grupos.html', context)


@accepted_user_required
@user_passes_test(is_staff)
@login_required
def crear_grupo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        description = request.POST.get('description')
        
        # Verificar si el grupo ya existe
        if Group.objects.filter(name=nombre).exists():
            messages.error(request, 'El grupo ya existe.')
            return redirect('crear_grupo')  # Redireccionar al mismo formulario
            
        # Crear el grupo
        nuevo_grupo = Group(name=nombre, description=description)  # Asegúrate de que 'descripcion' sea un campo válido en tu modelo Group
        
        nuevo_grupo.save()


        messages.success(request, 'Grupo creado con éxito.')
        
        return redirect('/administrar/grupos')  # Redireccionar a donde sea apropiado
        
    return render(request, 'crear_grupo.html')  # Asegúrate de reemplazar 'nombre_de_tu_template.html' con el nombre de tu template para el formulario



@accepted_user_required
@user_passes_test(is_staff)
@login_required
def admi_grupo(request, id):
    grupo = get_object_or_404(Group, id=id)
    usuarios = User.objects.all()

    if request.method == 'POST':
        if 'eliminar' in request.POST:
            grupo.delete()
            return redirect('administrar_grupos')

        elif 'guardar' in request.POST:
            nombre = request.POST.get('nombre')
            description = request.POST.get('description')
            grupo.description = description
            grupo.name = nombre
            grupo.save()


            # Procesar los usuarios añadidos al grupo
            usuarios_seleccionados = request.POST.getlist('usuarios_no_grupo')
            for usuario_id in usuarios_seleccionados:
                try:
                    usuario = User.objects.get(id=usuario_id)
                    grupo.user_set.add(usuario)
                except User.DoesNotExist:
                    pass

            # Procesar los usuarios eliminados del grupo
            usuarios_a_eliminar = request.POST.getlist('usuarios_a_eliminar')
            for usuario_id in usuarios_a_eliminar:
                try:
                    usuario = User.objects.get(id=usuario_id)
                    grupo.user_set.remove(usuario)
                except User.DoesNotExist:
                    pass

            return redirect('administrar_grupos')

    return render(request, 'admi_grupo.html', {'grupo': grupo, 'usuarios': usuarios})

@accepted_user_required
@login_required
def contacta(request):
        
        return render(request, 'contacto.html')


@accepted_user_required
@login_required
def contact_admin(request):
        
        return render(request, 'contact_admin.html')

@accepted_user_required
@login_required
def contact_user(request):
        
        return render(request, 'contact_user.html')


@accepted_user_required
@login_required
def archivos_analiz(request):
    API_KEY = "2f047d42c57a702fd720dd049e5d7f8d24baf8811faf42d34226e703be6270a9"
    base_url = "https://www.virustotal.com/api/v3"
    headers = {"x-apikey": API_KEY}  # Definir las cabeceras una sola vez

    if request.method == 'POST':
        archivos_subidos = request.FILES.getlist('archivos')  # Obtener los archivos subidos
        for archivo_subido in archivos_subidos:  # Renombrar la variable para evitar conflictos de nombres
            nombre_archivo = archivo_subido.name
            usuario = request.user.username

            # Leer el contenido del archivo
            contenido = archivo_subido.read()

            # Calcular el hash combinando el nombre del archivo y su contenido
            hasher = hashlib.sha256()
            hasher.update(archivo_subido.name.encode('utf-8'))
            hasher.update(contenido)
            hash_archivo = hasher.hexdigest()
        
        
            # Buscar el hash en la base de datos django

            if Archivo.objects.filter(id_APB2TAL=hash_archivo).exists():
                archivo_existente = Archivo.objects.get(id_APB2TAL=hash_archivo)
                print("Ya existe registro de", nombre_archivo, "para este usuario.")
                
                # Verificar si el usuario actual está en la tabla de adquisición para este archivo
                if not adquisicion.objects.filter(archivo=archivo_existente, user=request.user).exists():
                    # El usuario no está en la tabla de adquisición para este archivo, así que creamos un nuevo registro
                    adquisicion.objects.create(archivo=archivo_existente, user=request.user, group=None)
   
                
            else:
                # Generar el nombre de la carpeta utilizando el hash del archivo y el nombre de usuario
                # Ver línea 369
                nombre_carpeta = hash_archivo
                ruta_carpeta = os.path.join(settings.MEDIA_ROOT, nombre_carpeta)
                
                # Crear la carpeta si no existe
                if not os.path.exists(ruta_carpeta):
                    os.makedirs(ruta_carpeta)
                print ("       ")
                print ("       ")
                

                # Función para animar el texto en la consola
                def animar():
                    start_time = time.time()  # Obtener el tiempo de inicio
                    while True:
                        elapsed_time = time.time() - start_time
                        if elapsed_time >= 16:  # Esperar 16 segundos
                            break
                        for cursor in '|/-\\':
                            print(f'\rEsperando a la cola {cursor}', end='', flush=True)
                            time.sleep(0.1)  # Aquí es donde se llama la función sleep

                # Llamar a la función de animación
                try:
                    animar()
                    print("\nContinuando con el resto del código...")
                except KeyboardInterrupt:
                    # Manejar la interrupción del teclado (Ctrl+C) para detener la animación
                    print('\nAnimación detenida.')



                print ("==================================================")
                print ("ANALIZANDO")
                print (nombre_archivo)
                print ("==================================================")
                

                print ("Creando carpeta encriptada ....")
                # Guardar el archivo en la carpeta
                with open(os.path.join(ruta_carpeta, archivo_subido.name), 'wb+') as destino:
                    destino.write(contenido)
                print ("Guardando archivo ....")

                print ("Enviando archivo a la API ....")
                url = f"{base_url}/files"
                files = {"file": (nombre_archivo, contenido)}
                response_json = requests.post(url, files=files, headers=headers)

                print ("Recogiendo ID de la API ....")

                print ("Enviando ID a la API ....")

                result = response_json.json()

                url_self = result['data']['links']['self']

                headers = {
                    "accept": "application/json",
                    "x-apikey": API_KEY
                }
                
                response = requests.get(url_self, headers=headers)
                # Después de recibir la respuesta JSON de VirusTotal
                informe = response.json()
                print("Recogiendo INFORME de la API ....")

                # Obtener el valor de 'malicious' de la respuesta JSON
                malicious = informe.get('data', {}).get('attributes', {}).get('stats', {}).get('malicious', 0)
                sha256 = informe.get('meta', {}).get('file_info', {}).get('sha256')
                #identificador = informe.get('data', {}).get('id')



                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print("Guardando datos en nuestra base de datos ....")


                # Intentar insertar el documento en la base de datos
                try:
                    nuevo_archivo = Archivo.objects.create(
                        archivo_hash=sha256,
                        id_APB2TAL=hash_archivo,
                        nombre_archivo=nombre_archivo,
                        positivos=malicious,
                        current_time=current_time
                    )

                    usuario_actual = request.user

                    adquisicion.objects.create(
                        archivo=nuevo_archivo,
                        user=usuario_actual,
                        group=None
                    )

                    nuevo_path = "hecho"
                    print("Moviendo carpeta en HECHO ...")
                    print("TODO CORRECTO!")
                    print("=========== SCAN FINALIZADO (" + current_time + ") ===========")
                    print("       ")

                    shutil.move(ruta_carpeta, nuevo_path)
                    
                except Exception as e:
                    # Manejar cualquier excepción que pueda ocurrir durante la inserción en la base de datos
                    print(f"Error al insertar en la base de datos: {e}")
                    print("       ")
                    print("       ")

                    shutil.rmtree(ruta_carpeta)
                    

                    print ("ERROR")
                    print ("No se ha guardado en Django")
                    print ("Se ha eliminado al carpeta")
            
        return redirect('archivos')
      
        
    # Devolver la respuesta HTML
    return render(request, 'archivos_analiz.html')



@accepted_user_required
@login_required
def archivos(request):
    usuario_actual = request.user
    if adquisicion.objects.filter(user=usuario_actual).exists():
        # Obtener todos los archivos asociados al usuario actual en la clase adquisicion
        archivos_adquisicion = adquisicion.objects.filter(user=usuario_actual).values_list('archivo', flat=True)
        # Filtrar los registros de la clase Archivo basados en los archivos obtenidos anteriormente
        registros = Archivo.objects.filter(id__in=archivos_adquisicion)
    else:
        registros = Archivo.objects.none()  # Retorna una queryset vacía si no hay archivos asociados al usuario
    
    return render(request, 'archivos.html', {'registros': registros})

from .models import  *
@accepted_user_required
@login_required
def eliminar_archivo(request, archivo_id):
    # Obtener el archivo de la tabla de adquisiciones por su ID
    try:
        compartidos = Compartido.objects.filter(archivo_id=archivo_id, usuario_propietario=request.user)
        registro_adquisicion = adquisicion.objects.get(archivo_id=archivo_id, user=request.user)
        
    except adquisicion.DoesNotExist:
        # Manejar el caso en el que no se encuentra el registro de adquisición
        # Redireccionar a donde corresponda, por ejemplo, a una página de error
        return redirect('archivos')  # Redirigir a la página de archivos

    # Si se encontró el registro de adquisición, eliminarlo
    for compartido in compartidos:
        compartido.delete()
    registro_adquisicion.delete()
    
    

    # Después de eliminar, redirigir a la página de archivos
    return redirect('archivos')




@accepted_user_required
@login_required
def descargar_archivo(request, archivo_id):
    try:
        # Buscar el archivo en la base de datos
        archivo = Archivo.objects.get(id=archivo_id)
        # Verificar si el usuario tiene permiso para descargar este archivo
        if adquisicion.objects.filter(archivo=archivo, user=request.user).exists():
            # Obtener la ruta del archivo en el sistema de archivos
            ruta_archivo = os.path.join(settings.MEDIA_ROOT2, archivo.id_APB2TAL, archivo.nombre_archivo)
            with open(ruta_archivo, 'rb') as f:
                response = HttpResponse(f.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'attachment; filename="{archivo.nombre_archivo}"'
                return response
        else:
            # Si el usuario no tiene permiso para descargar el archivo, redirigir a algún lugar apropiado
            return HttpResponse("No tienes permiso para descargar este archivo.")
    except Archivo.DoesNotExist:
        # Manejar el caso en el que el archivo no existe en la base de datos
        return HttpResponse("El archivo no existe.")

@accepted_user_required
@login_required
def mis_grupos(request):
    usuario = request.user  # Obtener el usuario actual
    return render(request, 'mis_grupos.html', {'usuario': usuario})





@accepted_user_required
@login_required
def archivos_manage(request, archivo_id):
    usuario_actual = request.user
    archivo = get_object_or_404(Archivo, pk=archivo_id)
    usuarios = User.objects.all().exclude(id=usuario_actual.id)
    grupos = usuario_actual.groups.all()



    # Obtener los usuarios y grupos con los que se ha compartido el archivo
    usuarios_compartidos = [compartido.usuario_destinatario_id for compartido in Compartido.objects.filter(archivo=archivo, usuario_destinatario__isnull=False, usuario_propietario=usuario_actual)]
    grupos_compartidos = [compartido.grupo_destinatario_id for compartido in Compartido.objects.filter(archivo=archivo, grupo_destinatario__isnull=False, usuario_propietario=usuario_actual)]

    
    return render(request, 'archivos_manage.html', {
        'usuario_actual': usuario_actual,
        'usuarios': usuarios,
        'grupos': grupos,
        'archivo': archivo,
        'usuarios_compartidos': usuarios_compartidos,
        'grupos_compartidos': grupos_compartidos,
    })



@accepted_user_required
@login_required
def compartir_archivo(request, archivo_id):
    if request.method == 'POST':
        usuarios_seleccionados = request.POST.getlist('usuarios')
        grupos_seleccionados = request.POST.getlist('grupos')
        archivo = Archivo.objects.get(pk=archivo_id)
        
        # Buscar la adquisición del archivo para determinar el propietario
        adquisicion1 = adquisicion.objects.filter(archivo=archivo).first()
        usuario_propietario = request.user
        grupo_propietario = adquisicion1.group if adquisicion1 else None
        
        # Obtener los registros compartidos existentes para el archivo
        compartidos_exist = Compartido.objects.filter(archivo=archivo)
        
        # Usuarios y grupos compartidos existentes
        usuarios_compartidos = [compartido.usuario_destinatario_id for compartido in compartidos_exist if compartido.usuario_destinatario]
        grupos_compartidos = [compartido.grupo_destinatario_id for compartido in compartidos_exist if compartido.grupo_destinatario]
        
        # Comprobar si algún usuario o grupo fue desmarcado y eliminar el registro correspondiente
        for usuario_id in usuarios_compartidos:
            if str(usuario_id) not in usuarios_seleccionados:
                Compartido.objects.filter(archivo=archivo, usuario_destinatario_id=usuario_id).delete()
        
        for grupo_id in grupos_compartidos:
            if str(grupo_id) not in grupos_seleccionados:
                Compartido.objects.filter(archivo=archivo, grupo_destinatario_id=grupo_id).delete()
        
        # Compartir con usuarios seleccionados
        for usuario_id in usuarios_seleccionados:
            usuario_destinatario = User.objects.get(pk=usuario_id)
            Compartido.objects.get_or_create(
                usuario_propietario=usuario_propietario,
                usuario_destinatario=usuario_destinatario,
                archivo=archivo
            )
        
        # Compartir con grupos seleccionados
        for grupo_id in grupos_seleccionados:
            grupo_destinatario = Group.objects.get(pk=grupo_id)
            Compartido.objects.get_or_create(
                grupo_propietario=grupo_propietario,
                grupo_destinatario=grupo_destinatario,
                archivo=archivo
            )
        
        # Mensaje de éxito
        messages.success(request, 'Archivo compartido exitosamente.')

        # Redireccionar a alguna página, por ejemplo, a la página de archivos
        return redirect('archivos')
    else:
        # Si la solicitud no es POST, renderizar nuevamente el formulario o redireccionar según tu lógica
        pass


@accepted_user_required
@login_required
def eliminar_compartido(request):
    if request.method == 'POST' and request.is_ajax():
        tipo = request.POST.get('tipo')
        usuario_grupo_id = request.POST.get('usuario_grupo_id')
        archivo_id = request.POST.get('archivo_id')
        
        # Lógica para eliminar el registro compartido
        # Por ejemplo:
        if tipo == 'usuarios':
            Compartido.objects.filter(usuario_destinatario_id=usuario_grupo_id, archivo_id=archivo_id).delete()
        elif tipo == 'grupos':
            Compartido.objects.filter(grupo_destinatario_id=usuario_grupo_id, archivo_id=archivo_id).delete()
        
        return JsonResponse({'mensaje': 'Registro compartido eliminado correctamente.'})
    else:
        return JsonResponse({'error': 'La solicitud debe ser de tipo POST y AJAX.'}, status=400)




@accepted_user_required
@login_required
def compartido(request):
    # Obtener el usuario actual
    usuario_actual = request.user
    
    # Obtener archivos compartidos al usuario actual
    archivos_compartidos_al_usuario = [(compartido.archivo, compartido.usuario_propietario) for compartido in Compartido.objects.filter(usuario_destinatario=usuario_actual)]
    
    archivos_compartidos_por_usuario = [(compartido.archivo, compartido.usuario_destinatario) for compartido in Compartido.objects.filter(usuario_propietario=usuario_actual)]
    
    return render(request, 'compartido.html', {
        'archivos_compartidos_al_usuario': archivos_compartidos_al_usuario,
        'archivos_compartidos_por_usuario': archivos_compartidos_por_usuario
    })



@accepted_user_required
@login_required
def descargar_archivo_compartido(request, archivo_id):
    # Obtener el objeto Archivo basado en su ID
    archivo = get_object_or_404(Archivo, pk=archivo_id)
    
    # Aquí debes implementar la lógica para obtener la ruta del archivo en tu sistema de archivos
    # Supongamos que la ruta del archivo se almacena en el atributo 'ruta' del modelo Archivo
    ruta_archivo = os.path.join(settings.MEDIA_ROOT2, archivo.id_APB2TAL, archivo.nombre_archivo)
    
    # Abrir el archivo para lectura en modo binario
    with open(ruta_archivo, 'rb') as file:
        # Leer el contenido del archivo
        contenido_archivo = file.read()
    
    # Configurar la respuesta HTTP con el contenido del archivo
    response = HttpResponse(contenido_archivo, content_type='application/octet-stream')
    
    # Configurar las cabeceras HTTP para la descarga del archivo
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(archivo.nombre_archivo)
    
    return response

@accepted_user_required
@login_required
def eliminar_archivo_compartido(request, archivo_id):
    # Obtener el archivo de la tabla de adquisiciones por su ID
    try:
        compartidos = Compartido.objects.filter(archivo_id=archivo_id, usuario_propietario=request.user) 
    except adquisicion.DoesNotExist:
        # Manejar el caso en el que no se encuentra el registro de adquisición
        # Redireccionar a donde corresponda, por ejemplo, a una página de error
        return redirect('archivos')  # Redirigir a la página de archivos
    # Si se encontró el registro de adquisición, eliminarlo
    for compartido in compartidos:
        compartido.delete()
    # Después de eliminar, redirigir a la página de archivos
    return redirect('compartido')


def compartido_archivo_info(request, archivo_id):

    archivo = get_object_or_404(Archivo, pk=archivo_id)

    return render(request, 'compartido_archivo_info.html', {

        'archivo': archivo,

    })



