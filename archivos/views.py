from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.files.uploadedfile import UploadedFile
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.http import HttpResponse, Http404
from pymongo.mongo_client import MongoClient
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm
from pymongo.server_api import ServerApi
from requests.auth import HTTPBasicAuth
from cryptography.fernet import Fernet
from django.http import HttpResponse
from django.http import FileResponse
from django.db import IntegrityError
from .models import Task, Compartido
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import adquisicion
from pymongo import MongoClient
from datetime import datetime
from .forms import TaskForm
from .models import Archivo
from .forms import RepoForm
from .models import  *
from .utils import *
import subprocess
import mimetypes
import requests
import hashlib
import random
import string
import shutil
import uuid
import time
import os


def accepted_user_required(view_func):
    decorated_view_func = user_passes_test(
        lambda user: user.is_authenticated and user.is_accepted,
        login_url='/perfil'  # Redirige a la página de perfil si el usuario no tiene is_accepted
    )(view_func)
    return decorated_view_func
    
def is_staff(user):
    return user.is_authenticated and user.is_staff




JENKINS_URL = 'http://10.30.212.36:8080'
JOB_NAME = 'Pipeline_SonarQube'
TRIGGER_URL = f'{JENKINS_URL}/job/{JOB_NAME}/build?token=mi_token_seguro'
API_USER = 'admin-jenkins'
API_TOKEN = '1147a292f0559733a360e43466040414f9'

JOB_API_URL = f'{JENKINS_URL}/job/{JOB_NAME}'

auth = (API_USER, API_TOKEN)

def get_last_build_number():
    url = f'{JOB_API_URL}/api/json'
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    data = r.json()
    return data['lastBuild']['number']

def get_build_status(build_number):
    url = f'{JOB_API_URL}/{build_number}/api/json'
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    data = r.json()
    return data['building'], data.get('result')


@accepted_user_required
@user_passes_test(is_staff)
@login_required
def proyectoanaliz(request):
    context = {}

    if request.method == "POST":

        # Lanzar build nuevo
        r = requests.post(TRIGGER_URL, auth=auth)
        if r.status_code not in [201, 200]:
            return HttpResponse(f"Error al lanzar pipeline: {r.status_code}", status=500)

        queue_url = r.headers.get('Location')
        if not queue_url:
            return HttpResponse("No se recibió URL de la build lanzada", status=500)

        build_number = None
        for _ in range(30):
            queue_api_url = queue_url + "api/json"
            rq = requests.get(queue_api_url, auth=auth)
            rq.raise_for_status()
            data = rq.json()
            if 'executable' in data and data['executable'] is not None:
                build_number = data['executable']['number']
                break
            time.sleep(10)

        if build_number is None:
            return HttpResponse("Timeout esperando asignación de build", status=500)

        while True:
            building, result = get_build_status(build_number)
            if not building:
                break
            time.sleep(10)

        if result != "SUCCESS":
            return HttpResponse(f"La build terminó con estado {result}", status=500)

        artifact_url = f'{JOB_API_URL}/lastSuccessfulBuild/artifact/reporte_zap.html'
        r = requests.get(artifact_url, auth=auth)
        if r.status_code == 200:
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            filename = f'zap_report_{uuid.uuid4().hex}.html'
            filepath = os.path.join(reports_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(r.content)

            # Guardar en contexto la URL para descargar el archivo
            context['download_url'] = f'/data/reports/{filename}'
            context['visitar_sonar'] = "http://10.30.212.36:9000/dashboard?id=APB2TAL"
            context['message'] = "¡Pipeline completado exitosamente! Aquí está tu reporte."


        else:
            context['error'] = "No se encontró el reporte ZAP"

    return render(request, 'proyectoanaliz.html', context)

URL = "http://10.30.212.36:8080"
JENKINS_USER = "admin-jenkins"
JENKINS_TOKEN = "11d5010945658812cf7fa005160d2e2b13"
JOB_NAME = "universal-runner"


@login_required
def seleccion(request):
    return render(request, 'seleccion.html')



def obtener_branch_default(repo_url):
    try:
        # Ejecuta git ls-remote para obtener refs/heads/*
        result = subprocess.run(
            ["git", "ls-remote", "--symref", repo_url, "HEAD"],
            capture_output=True, text=True, check=True
        )
        # El output contiene una línea como:
        # ref: refs/heads/main HEAD
        for line in result.stdout.splitlines():
            if line.startswith("ref: "):
                # Ejemplo: "ref: refs/heads/main HEAD"
                parts = line.split()
                if len(parts) >= 2:
                    ref = parts[1]  # refs/heads/main
                    branch_name = ref.replace("refs/heads/", "")
                    return branch_name
        # Si no encontró, retorna 'main' por defecto
        return "main"
    except Exception as e:
        print(f"[WARN] No se pudo obtener branch default: {e}")
        return "main"


SONAR_URL = "http://10.30.212.36:9000/"
SONAR_TOKEN = "squ_8f2a30868e775986e41fa1002349456c58d6e962"

def obtener_informe_sonar(proyecto_key):
    """
    Consulta el resumen del análisis de SonarQube para el proyecto dado.
    Devuelve un string con info relevante (por ejemplo, estado general).
    """
    try:
        url = f"{SONAR_URL}/api/qualitygates/project_status"
        params = {'projectKey': proyecto_key}
        resp = requests.get(url, params=params, auth=HTTPBasicAuth(SONAR_TOKEN, ''))
        resp.raise_for_status()
        data = resp.json()
        status = data.get('projectStatus', {}).get('status', 'UNKNOWN')
        conditions = data.get('projectStatus', {}).get('conditions', [])
        msg_conditions = "; ".join(
            [f"{c['metricKey']}: {c['status']}" for c in conditions]
        )
        return f"Estado SonarQube: {status}. Condiciones: {msg_conditions}"
    except Exception as e:
        return f"No se pudo obtener informe SonarQube: {str(e)}"



def obtener_metricas_sonar(proyecto_key):
    """
    Obtiene métricas clave del proyecto en SonarQube.
    """
    try:
        url = f"{SONAR_URL}/api/measures/component"
        params = {
            'component': proyecto_key,
            'metricKeys': 'bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc'
        }
        resp = requests.get(url, params=params, auth=HTTPBasicAuth(SONAR_TOKEN, ''))
        resp.raise_for_status()
        data = resp.json()

        measures = data.get('component', {}).get('measures', [])
        resumen = []
        for m in measures:
            resumen.append(f"{m['metric']}: {m['value']}")
        return " | ".join(resumen)

    except Exception as e:
        return f"No se pudo obtener métricas SonarQube: {str(e)}"

def obtener_informe_completo_sonar(project_key):
    import requests

    base_url = SONARQUBE_URL
    auth = (SONAR_USER, SONAR_PASS)

    result = {}

    # Quality Gate
    try:
        r = requests.get(f"{base_url}/api/qualitygates/project_status?projectKey={project_key}", auth=auth)
        r.raise_for_status()
        result['quality_gate'] = r.json()
    except Exception as e:
        result['quality_gate'] = f"Error: {e}"

    # Métricas
    metrics = "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,lines,ncloc"
    try:
        r = requests.get(f"{base_url}/api/measures/component?component={project_key}&metricKeys={metrics}", auth=auth)
        r.raise_for_status()
        result['metrics'] = r.json()
    except Exception as e:
        result['metrics'] = f"Error: {e}"

    # Issues críticos (ejemplo bugs sin resolver, máximo 5)
    try:
        r = requests.get(f"{base_url}/api/issues/search?componentKeys={project_key}&types=BUG&resolved=false&ps=5", auth=auth)
        r.raise_for_status()
        result['bugs'] = r.json()
    except Exception as e:
        result['bugs'] = f"Error: {e}"

    return result



def obtener_nombre_repo(repo_url):
    import os
    if not repo_url:
        return "Nombre no disponible"
    repo_name = os.path.basename(repo_url)
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


SONAR_USER = 'admin'
SONAR_PASS = 'Sonargrupo5.'
SONAR_URL = 'http://10.30.212.36:9000'

def obtener_proyecto_sonar(proyecto_key):
    url = f"{SONAR_URL}/api/measures/component?component={proyecto_key}&metricKeys=bugs,vulnerabilities"
    resp = requests.get(url, auth=HTTPBasicAuth(SONAR_USER, SONAR_PASS))
    return resp.json()



import random
import string

def generar_contrasena(longitud=12):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def cambiar_contrasena_sonarqube(login_usuario, nueva_contrasena, admin_user, admin_pass, sonar_url):
    url = f"{sonar_url}/api/users/change_password"
    data = {
        "login": login_usuario,
        "password": nueva_contrasena
    }

    resp = requests.post(url, auth=HTTPBasicAuth(admin_user, admin_pass), data=data)
    if resp.status_code == 204:
        return True
    else:
        print(f"[ERROR] No se pudo cambiar la contraseña. Código: {resp.status_code}, Detalle: {resp.text}")
        return False




@login_required
def procesar_repo(request):
    context = {}
    repo_url = request.GET.get('repo_url')
    branch = request.GET.get('branch')
    repo_nombre = obtener_nombre_repo(repo_url)

    
    if repo_url is None:
        context['status'] = 'error'
        context['message'] = '❌ No se recibió URL del repositorio.'
        return render(request, "proyectos.html", context)
    repo_nombre = obtener_nombre_repo(repo_url)
    
    if not branch:
        branch = obtener_branch_default(repo_url)

    print(f"[DEBUG] branch usado: {branch}")

    if repo_url:
        try:
            context['status'] = "ok"
            context['message'] = "🚀 Disparando pipeline en Jenkins..."

            jenkins_api_url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters"
            params = {
                'GIT_URL': repo_url,
                'GIT_BRANCH': branch
            }            
            headers = {}

            try:
                crumb_resp = requests.get(
                    f"{JENKINS_URL}/crumbIssuer/api/json",
                    auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN)
                )
                crumb_resp.raise_for_status()
                crumb_data = crumb_resp.json()
                headers[crumb_data['crumbRequestField']] = crumb_data['crumb']
                print(f"[DEBUG] Obtenido crumb: {crumb_data['crumb']}")
            except Exception as e:
                print(f"[WARN] No se obtuvo crumb: {e}")

            build_resp = requests.post(
                jenkins_api_url,
                auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN),
                params=params,
                headers=headers
            )

            print(f"[DEBUG] Jenkins trigger status: {build_resp.status_code}")

            if build_resp.status_code in [200, 201, 202]:
                context['message'] += " ✅ Pipeline disparado correctamente."

                queue_url = build_resp.headers.get('Location')
                print(f"[DEBUG] Jenkins Queue URL: {queue_url}")

                if queue_url:
                    time.sleep(5)
                    build_number = None
                    for _ in range(20):
                        q_resp = requests.get(queue_url + "api/json", auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN))
                        q_data = q_resp.json()
                        if 'executable' in q_data:
                            build_number = q_data['executable']['number']
                            print(f"[DEBUG] Build Number: {build_number}")
                            break
                        time.sleep(1)

                    if build_number:
                        build_info_url = f"{JENKINS_URL}/job/{JOB_NAME}/{build_number}/api/json"
                        for _ in range(60):
                            b_resp = requests.get(build_info_url, auth=HTTPBasicAuth(JENKINS_USER, JENKINS_TOKEN))
                            b_data = b_resp.json()
                            if not b_data.get("building", True):
                                result = b_data.get("result", "UNKNOWN")
                                context['message'] += f" 📄 Resultado del pipeline: {result}."
                                
                                # Aquí llamamos a SonarQube solo si la build fue exitosa
                                if result == "SUCCESS":
                                    proyecto_key = "jenkinsMaster"
                                    print(f"[DEBUG] Consultando SonarQube para proyecto: {proyecto_key}")
                                    informe_sonar = obtener_informe_sonar(proyecto_key)
                                    metricas = obtener_metricas_sonar(proyecto_key)
                                    print(f"[DEBUG] Respuesta SonarQube: {informe_sonar}")
                                    print(f"[DEBUG] Métricas SonarQube: {metricas}")

                                    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    print(f"[SonarQube] Repo: {proyecto_key} - Hora: {ahora} - {informe_sonar} - {metricas}")

                                    context['sonar_info'] = informe_sonar
                                    context['sonar_metrics'] = metricas
                                    context['proyecto_key'] = repo_nombre
                                    context['visitar_sonar'] = "http://10.30.212.36:9000/dashboard?id=jenkinsMaster"


                                    context['hora'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    # Cambiar contraseña del usuario compartido en SonarQube
                                    nuevo_pass = generar_contrasena()
                                    usuario_sonar = "User_Report2m5c"
                                    admin_sonar = "admin"
                                    admin_sonar_pass = "Sonargrupo5."
                                    sonarqube_url = "http://10.30.212.36:9000"

                                    if cambiar_contrasena_sonarqube(usuario_sonar, nuevo_pass, admin_sonar, admin_sonar_pass, sonarqube_url):
                                        context['nueva_contrasena'] = nuevo_pass
                                        context['mensaje_contraseña'] = f"🔐 Usuario:    {usuario_sonar} Contraseña:    {nuevo_pass}"
                                    else:
                                        context['mensaje_contraseña'] = "⚠️ Error al cambiar la contraseña del usuario compartido."



                                break
                            time.sleep(2)
                    else:
                        context['message'] += " ⚠️ No se pudo obtener el número de build."
                else:
                    context['message'] += " ⚠️ No se encontró ubicación de la build en Jenkins."
            else:
                context['status'] = "error"
                context['message'] += f" ❌ Error llamando a Jenkins: {build_resp.status_code}"

        except Exception as e:
            context['status'] = "error"
            context['message'] = f"❌ Error procesando el repositorio: {str(e)}"

    return render(request, "proyectos.html", context)



def trigger_jenkins_pipeline(git_url):
    jenkins_url = 'http://jenkins-server/job/tu-pipeline/buildWithParameters'
    user = 'tu_usuario'
    api_token = 'tu_api_token'

    params = {
        'GIT_URL': git_url
    }

    response = requests.post(jenkins_url, params=params, auth=HTTPBasicAuth(user, api_token))

    if response.status_code == 201:
        print('Pipeline triggered successfully.')
    else:
        print(f'Error triggering pipeline: {response.status_code} {response.text}')

def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {'form': CustomUserCreationForm()})  # Utiliza el formulario personalizado
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = CustomUser.objects.create_user(username=request.POST['username'],
                                                       password=request.POST['password1'],
                                                       email=request.POST['email'],
                                                       first_name=request.POST['first_name'],
                                                       last_name=request.POST['last_name'])
                print('username:', request.POST['username'])
                user.save()
                login(request, user)
                return redirect('perfil')
            
            except IntegrityError:
                return render(request, 'signup.html', {'form': CustomUserCreationForm(), 'error': 'Please enter valid data'})



def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {'form': AuthenticationForm()})
    else:
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('perfil')
        return render(request, 'signin.html', {'form': form, 'error': 'Username or password is incorrect'})


def terminos(request):

    return render(request, 'terminos.html')

def project(request):

    return render(request, 'proyecto.html')


def about(request):

    return render(request, 'About-us.html')


def validar_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': CustomUser.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)


def accepted_user_required(view_func):
    decorated_view_func = user_passes_test(
        lambda user: user.is_authenticated and user.is_accepted,
        login_url='/perfil'  # Redirige a la página de perfil si el usuario no tiene is_accepted
    )(view_func)
    return decorated_view_func



@login_required
def perfil(request):
    return render(request, 'perfil.html')


@accepted_user_required
@login_required
def editar_perfil(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Obtener el usuario actual
        user = request.user

        # Actualizar los datos del usuario
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        if password:
            user.set_password(password)
   
        user.save()

        # Redirigir a la página de perfil
        return redirect('perfil')

    # Si es una solicitud GET, renderizar el formulario de edición
    return render(request, 'perfil_edit.html')
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

@accepted_user_required
@user_passes_test(is_staff, login_url='/')
@login_required
def administrar(request):
    return render(request, 'administrar.html')



@accepted_user_required
@user_passes_test(is_staff)
@login_required
def administrar_usuarios(request):

    usuarios = CustomUser.objects.all()

    context = {
        'usuarios': usuarios
    }
    return render(request, 'administrar_usuarios.html', context)

@accepted_user_required
@user_passes_test(is_staff)
@login_required
def admi_usuario(request, id):
    usuario = get_object_or_404(CustomUser, id=id)
    
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
def proyectos(request):

    return render(request, 'proyectos.html')



# Conexión a MongoDB 
from pymongo import MongoClient
client = MongoClient('localhost', 27018)
db = client['django_db']

collection = db['logs']


@accepted_user_required
@login_required
def registros(request):
    # Obtener el ID del usuario actual
    user_id = request.user.id
    print(user_id)
    # Filtrar los registros por el ID del usuario actual
    mensaje = list(collection.find({"user_id": user_id}))
    print(mensaje)
    print("mensaje")

    return render(request, 'mis_registros.html', {'logs_mongo': mensaje})


@user_passes_test(is_staff)
@accepted_user_required
@login_required
def registros_admin(request):
    
 
    mensaje = list(collection.find({}))  # Retrieve all logs
    return render(request, 'logs_admin.html', {'logs_mongo': mensaje})



from django.contrib.auth.models import Group
from .models import GroupDescription
from django.shortcuts import render, redirect
from django.contrib import messages

@accepted_user_required
@user_passes_test(is_staff)
@login_required
@csrf_protect
def crear_grupo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion_texto = request.POST.get('description')
        
        # Verificar si el grupo ya existe
        if Group.objects.filter(name=nombre).exists():
            messages.error(request, 'El grupo ya existe.')
            return redirect('crear_grupo')  # Redireccionar al mismo formulario
            
        # Crear una instancia de Group
        nuevo_grupo = Group.objects.create(name=nombre)
        
        # Crear una instancia de GroupDescription y asignarla al grupo
        descripcion = GroupDescription.objects.create(group=nuevo_grupo, description=descripcion_texto)
        
        messages.success(request, 'Grupo creado con éxito.')
        
        return redirect('/administrar/grupos')  # Redireccionar a donde sea apropiado
        
    return render(request, 'crear_grupo.html')  # Asegúrate de reemplazar 'crear_grupo.html' con el nombre de tu template para el formulario


@csrf_protect
@accepted_user_required
@user_passes_test(is_staff)
@login_required
def admi_grupo(request, id):
    grupo = get_object_or_404(Group, id=id)
    usuarios = CustomUser.objects.all()

    if request.method == 'POST':
        if 'eliminar' in request.POST:
            grupo.delete()
            return redirect('administrar_grupos')

        elif 'guardar' in request.POST:
            nombre = request.POST.get('nombre')
            descripcion_texto = request.POST.get('descripcion')  # Cambia 'description' a 'descripcion'
            
            descripcion, created = GroupDescription.objects.get_or_create(group=grupo)
            descripcion.description = descripcion_texto

            grupo.name = nombre
            grupo.save()
            descripcion.save()



            # Procesar los usuarios añadidos al grupo
            usuarios_seleccionados = request.POST.getlist('usuarios_no_grupo')
            for usuario_id in usuarios_seleccionados:
                try:
                    usuario = CustomUser.objects.get(id=usuario_id)
                    grupo.user_set.add(usuario)
                except CustomUser.DoesNotExist:
                    pass

            # Procesar los usuarios eliminados del grupo
            usuarios_a_eliminar = request.POST.getlist('usuarios_a_eliminar')
            for usuario_id in usuarios_a_eliminar:
                try:
                    usuario = CustomUser.objects.get(id=usuario_id)
                    grupo.user_set.remove(usuario)
                except CustomUser.DoesNotExist:
                    pass

            return redirect('administrar_grupos')

    return render(request, 'admi_grupo.html', {'grupo': grupo, 'usuarios': usuarios})




from django.db.models import Count

@login_required
def contacta(request):
    # Obtener el recuento de mensajes no leídos
    mensajes_no_leidos = Mensajes.objects.filter(receptor=request.user, leido=False).count()
    
    return render(request, 'contacta.html', {'mensajes_no_leidos': mensajes_no_leidos})

@csrf_protect
@login_required
def contact_admin(request):
    if request.method == 'POST':
        enviador = request.user
        title = request.POST.get('title')
        tipomensaje = request.POST.get('tipomensaje')
        description = request.POST.get('description')
        
        if request.user.is_staff:
            receptor_username = request.POST.get('receptor_username')
            receptor = CustomUser.objects.filter(username=receptor_username).first()
            if receptor is None:
                usuarios = CustomUser.objects.all()
                return render(request, 'contacta_adminstracion.html', {'usuarios': usuarios, 'error': 'Usuario no válido'})
        else:
            receptor = CustomUser.objects.filter(is_staff=True).first()
        
        mensaje = Mensajes.objects.create(enviador=enviador, receptor=receptor, title=title, tipomensaje=tipomensaje, description=description)
        mensaje.save()
        return redirect('contacta')
    else:
        usuarios = CustomUser.objects.all()
        return render(request, 'contacta_adminstracion.html', {'usuarios': usuarios})

@csrf_protect
@login_required
def buzon(request):
    # Obtener todos los mensajes recibidos por el usuario actual y ordenarlos por hora de envío descendente
    mensajes_recibidos = Mensajes.objects.filter(receptor=request.user).order_by('-hora_envio')

    # Marcar todos los mensajes como leídos
    for mensaje in mensajes_recibidos:
        mensaje.leido = True
        mensaje.save()

    return render(request, 'buzon.html', {'mensajes_recibidos': mensajes_recibidos})
from django.shortcuts import redirect, get_object_or_404

def eliminar_mensaje(request, mensaje_id):
    mensaje = get_object_or_404(Mensajes, id=mensaje_id)
    if request.method == 'POST':
        mensaje.delete()
        # Redirigir a la página de buzón después de eliminar el mensaje
        return redirect('buzon')
    # Manejar casos donde la solicitud no sea POST
    return redirect('buzon')


@accepted_user_required
@login_required
def contact_buzon(request):
        
        return render(request, 'buzon.html')



import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .en

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def generar_clave():
    if not os.path.exists('.env'):
        # Si el archivo .env no existe, crea uno y guarda la clave
        with open('.env', 'w') as f:
            clave = Fernet.generate_key()
            clave_str = clave.decode()
            f.write(f'SECRET_KEY={clave_str}\n')
            os.environ["SECRET_KEY"] = clave_str
    else:
        # Si el archivo .env ya existe, verifica si la variable de entorno SECRET_KEY está definida
        if not os.getenv("SECRET_KEY"):
            clave = Fernet.generate_key()
            clave_str = clave.decode()
            # Guarda la clave en el archivo .env y en la variable de entorno
            with open('.env', 'a') as f:
                f.write(f'SECRET_KEY={clave_str}\n')
                os.environ["SECRET_KEY"] = clave_str

def cargar_clave():
    # Cargar la clave desde la variable de entorno SECRET_KEY
    clave_env = os.getenv("SECRET_KEY")
    if clave_env:
        return clave_env.encode()
    else:
        # Si la clave no está definida en las variables de entorno, generarla y guardarla
        generar_clave()
        return os.getenv("SECRET_KEY").encode()


@login_required
def archivos_analiz(request):
    API_KEY = "2f047d42c57a702fd720dd049e5d7f8d24baf8811faf42d34226e703be6270a9"
    base_url = "https://www.virustotal.com/api/v3"
    #https://www.virustotal.com/api/v3/private/files
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
                collection.insert_one(archivo_mongo)

                
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
                # Generar la clave si no existe
                generar_clave()
                
                # Cargar la clave y encriptar el contenido
                clave = cargar_clave()
                fernet = Fernet(clave)
                encrypted_contenido = fernet.encrypt(contenido)
                
                # Guardar el archivo en la carpeta
                with open(os.path.join(ruta_carpeta, archivo_subido.name), 'wb+') as destino:
                    destino.write(encrypted_contenido)

                    
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

                import math

                from datetime import datetime  # Correct import
                hora_actual = datetime.now()
                current_time = hora_actual.strftime("%H:%M:%S")
                print("Guardando datos en nuestra base de datos ....")
                
                if isinstance(archivo_subido, UploadedFile):  # Verificar si es un objeto UploadedFile
                    tamaño_archivo_bytes = archivo_subido.size
                else:
                    tamaño_archivo_bytes = len(contenido)

                # Calcular el tamaño del archivo en KB o MB
                if tamaño_archivo_bytes >= 1024 * 1024:  # Si es mayor o igual a 1 MB
                    tamaño_archivo = f"{tamaño_archivo_bytes / (1024 * 1024):.2f} MB"  # Convertir a MB con dos decimales
                else:  # Si es menor que 1 MB
                    tamaño_archivo = f"{tamaño_archivo_bytes / 1024:.2f} KB"  # Convertir a KB con dos decimales

                # Intentar insertar el documento en la base de datos
                try:
                    nuevo_archivo = Archivo.objects.create(
                        archivo_hash=sha256,
                        id_APB2TAL=hash_archivo,
                        nombre_archivo=nombre_archivo,
                        positivos=malicious,
                        current_time=current_time,
                        tamaño=tamaño_archivo
                    )

                    usuario_actual = request.user

                    adquisicion.objects.create(
                        archivo=nuevo_archivo,
                        user=usuario_actual,
                        group=None
                    )

                    nuevo_path = "hecho"
                    print("Moviendo carpeta en HECHO ...")
                    print("Ruta de la carpeta destino:", ruta_carpeta)
                    print("TODO CORRECTO!")
                    
                    
                    
                    print("=========== SCAN FINALIZADO (" + current_time + ") ===========")
                    print("       ")
                    
                    texto_analisis = f"El usuario '{request.user.username}' ha analizado el archivo '{nombre_archivo}'"

                    # Crear el documento a insertar en la colección
                    archivo_mongo = {
                            
                        "hora": hora_actual,
                        "user_id": request.user.id,
                        "mensaje": texto_analisis
                    }

                    try:

                        collection.insert_one(archivo_mongo)

                        print("Documento insertado en MongoDB Atlas exitosamente!")
                    except Exception as e:
                        print("Error al insertar documento en MongoDB Atlas:", e)
                        
                    if malicious >= 1:
                        # Eliminar la carpeta si hay al menos 1 positivo
                        print("Eliminando carpeta por tener al menos 1 positivo...")
                        shutil.rmtree(ruta_carpeta)
                        print("Carpeta eliminada correctamente.")

                    else:
                        # Mover la carpeta si no hay positivos
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




@accepted_user_required
@login_required
@csrf_protect
def eliminar_archivo(request, archivo_id):
    from datetime import datetime  # Correct import
    hora_actual = datetime.now()
    # Obtener el archivo de la tabla de adquisiciones por su ID
    archivo = get_object_or_404(Archivo, id=archivo_id)

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


    texto_analisis = f"El usuario '{request.user.username}' ha eliminado el archivo '{archivo.nombre_archivo}'"

    # Crear el documento a insertar en la colección
    archivo_mongo = {
        "hora": hora_actual,
        "user_id": request.user.id,
        "mensaje": texto_analisis
    }


    try:

        collection.insert_one(archivo_mongo)

        print("Documento insertado en MongoDB Atlas exitosamente!")
    except Exception as e:
        print("Error al insertar documento en MongoDB Atlas:", e)
        
    # Después de eliminar, redirigir a la página de archivos
    return redirect('archivos')

@csrf_protect
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
            # Imprimir la ruta del archivo
            print("Ruta del archivo:", ruta_archivo)
            
            # Cargar la clave y desencriptar el contenido
            clave = cargar_clave()
            fernet = Fernet(clave)
            with open(ruta_archivo, 'rb') as f:
                encrypted_contenido = f.read()
                decrypted_contenido = fernet.decrypt(encrypted_contenido)
            
            # Crear una respuesta HTTP con el contenido desencriptado
            response = HttpResponse(decrypted_contenido, content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{archivo.nombre_archivo}"'
            return response
        else:
            # Si el usuario no tiene permiso para descargar el archivo, redirigir a algún lugar apropiado
            return HttpResponse("No tienes permiso para descargar este archivo.")
    except Archivo.DoesNotExist:
        # Manejar el caso en el que el archivo no existe en la base de datos
        return HttpResponse("El archivo no existe.")


@csrf_protect
@accepted_user_required
@login_required
def archivos_manage(request, archivo_id):
    usuario_actual = request.user
    archivo = get_object_or_404(Archivo, pk=archivo_id)

    # Verificar si el usuario actual tiene adquisición de este archivo
    if not adquisicion.objects.filter(user=usuario_actual, archivo=archivo).exists():
        raise Http404("No tienes permiso para acceder a este archivo.")

    usuarios = CustomUser.objects.all().exclude(id=usuario_actual.id)
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

@csrf_protect
@accepted_user_required
@login_required
def compartir_archivo(request, archivo_id):
    usuario_propietario = request.user
    hora_actual = datetime.datetime.now()
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
            texto_analisis = f"El usuario '{request.user.username}' ha desecho el compartido del archivo '{archivo.nombre_archivo}'   "
            usuarios_destinatarios = [CustomUser.objects.get(pk=usuario_id).username for usuario_id in usuarios_seleccionados]
            texto_analisis += " a algún/os usuario/s "
            texto_analisis += ', '.join(usuarios_destinatarios)
        
        for grupo_id in grupos_compartidos:
            if str(grupo_id) not in grupos_seleccionados:
                Compartido.objects.filter(archivo=archivo, grupo_destinatario_id=grupo_id).delete()
            texto_analisis = f"El usuario '{request.user.username}'  ha desecho el compartido del archivo '{archivo.nombre_archivo}' a "
            # Agregar nombres de grupos seleccionados
            grupos_destinatarios = [Group.objects.get(pk=grupo_id).name for grupo_id in grupos_seleccionados]
            texto_analisis += " grupos "
            texto_analisis += ', '.join(grupos_destinatarios)
            


        
        # Compartir con usuarios seleccionados
        for usuario_id in usuarios_seleccionados:
            usuario_destinatario = CustomUser.objects.get(pk=usuario_id)
            Compartido.objects.get_or_create(
                usuario_propietario=usuario_propietario,
                usuario_destinatario=usuario_destinatario,
                archivo=archivo
            )
            texto_analisis = f"El usuario '{request.user.username}' ha compartido el archivo '{archivo.nombre_archivo}'   "
            usuarios_destinatarios = [CustomUser.objects.get(pk=usuario_id).username for usuario_id in usuarios_seleccionados]
            texto_analisis += " a los usuarios: "
            texto_analisis += ', '.join(usuarios_destinatarios)

        
        # Compartir con grupos seleccionados
        for grupo_id in grupos_seleccionados:
            grupo_destinatario = Group.objects.get(pk=grupo_id)
            Compartido.objects.get_or_create(
                usuario_propietario=usuario_propietario,
                grupo_destinatario=grupo_destinatario,
                archivo=archivo
            )
            texto_analisis = f"El usuario '{request.user.username}' ha compartido el archivo '{archivo.nombre_archivo}' a "
            # Agregar nombres de grupos seleccionados
            grupos_destinatarios = [Group.objects.get(pk=grupo_id).name for grupo_id in grupos_seleccionados]
            texto_analisis += " a los grupos: "
            texto_analisis += ', '.join(grupos_destinatarios)

    

        archivo_mongo = {
            "hora": hora_actual,
            "user_id": request.user.id,
            "mensaje": texto_analisis
        }
        
        try:
            collection.insert_one(archivo_mongo)
            print("Documento insertado en MongoDB Atlas exitosamente!")

            messages.success(request, 'Archivo compartido exitosamente.')

            return redirect('archivos')
        except Exception as e:
            print("Error al insertar documento en MongoDB Atlas:", e)

            messages.error(request, 'Error al compartir el archivo. Por favor, inténtelo de nuevo.')

            return redirect('archivos')
        else:
            pass
    
        messages.success(request, 'Archivo compartido exitosamente.')

        return redirect('archivos')
    else:
        pass
    
@csrf_protect
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
    
    
    archivos_compartidos_por_grupo =  Compartido.objects.filter(usuario_propietario=usuario_actual, grupo_destinatario__isnull = False)
    
    archivos_compartidos_por_usuario = Compartido.objects.filter(usuario_propietario=usuario_actual, grupo_destinatario__isnull = True )
    
    
    return render(request, 'compartido.html', {
        'archivos_compartidos_al_usuario': archivos_compartidos_al_usuario,
        'archivos_compartidos_por_usuario': archivos_compartidos_por_usuario,
        'archivos_compartidos_por_grupo': archivos_compartidos_por_grupo
    })


@csrf_protect
@accepted_user_required
@login_required
def descargar_archivo_compartido(request, archivo_id):
    # Obtener el objeto Archivo basado en su ID
    archivo = get_object_or_404(Archivo, pk=archivo_id)
    
    # Verificar si el usuario tiene permisos para acceder al archivo compartido
    if not Compartido.objects.filter(usuario_destinatario=request.user, archivo=archivo).exists():
        raise Http404("No tienes permiso para acceder a este archivo.")
    
    # Aquí debes implementar la lógica para obtener la ruta del archivo en tu sistema de archivos
    # Supongamos que la ruta del archivo se almacena en el atributo 'ruta' del modelo Archivo
    ruta_archivo = os.path.join(settings.MEDIA_ROOT2, archivo.id_APB2TAL, archivo.nombre_archivo)
    
    # Abrir el archivo para lectura en modo binario
    clave = cargar_clave()
    fernet = Fernet(clave)
    with open(ruta_archivo, 'rb') as f:
        encrypted_contenido = f.read()
        contenido_archivo = fernet.decrypt(encrypted_contenido)
    
    # Configurar la respuesta HTTP con el contenido del archivo
    response = HttpResponse(contenido_archivo, content_type='application/octet-stream')
    
    # Configurar las cabeceras HTTP para la descarga del archivo
    response['Content-Disposition'] = 'attachment; filename="{0}"'.format(archivo.nombre_archivo)
    
    return response

@csrf_protect
@accepted_user_required
@login_required
def eliminar_archivo_compartido(request, archivo_id):
    # Obtener el archivo compartido por su ID y el usuario actual
    try:
        compartido = Compartido.objects.get(id=archivo_id, usuario_propietario=request.user)
    except Compartido.DoesNotExist:
        # Manejar el caso en el que no se encuentra el archivo compartido
        # Redireccionar a donde corresponda, por ejemplo, a una página de error
        return redirect('compartido')  # Redirigir a la página de archivos compartidos
    
    # Eliminar el archivo compartido
    compartido.delete()
    
    # Después de eliminar, redirigir a la página de archivos compartidos
    return redirect('compartido')

@csrf_protect
@accepted_user_required
@login_required
def compartido_archivo_info(request, archivo_id):
    usuario_actual = request.user
    archivo = get_object_or_404(Archivo, pk=archivo_id)

    # Verificar si el usuario actual tiene acceso compartido a este archivo
    if not Compartido.objects.filter(usuario_destinatario=usuario_actual, archivo=archivo).exists():
        raise Http404("No tienes permiso para acceder a este archivo compartido.")

    return render(request, 'compartido_archivo_info.html', {
        'usuario_actual': usuario_actual,
        'archivo': archivo,
    })



@accepted_user_required
@login_required
def mis_grupos(request):
    
    usuario = request.user  # Obtener el usuario actual


    return render(request, 'mis_grupos.html', {'usuario': usuario})



@accepted_user_required
@login_required
def grupo_info(request, name):
    # Obtener el usuario actual
    usuario_actual = request.user

    # Obtener el grupo por su nombre
    grupo_seleccionado = Group.objects.get(name=name)

    # Obtener la descripción del grupo
    descripcion_grupo = grupo_seleccionado.description.description

    # Verificar si el usuario actual pertenece al grupo seleccionado
    if not usuario_actual.groups.filter(name=name).exists():
        raise Http404("No tienes permiso para acceder a este grupo.")

    # Filtrar los archivos compartidos solo para el grupo específico seleccionado
    archivos_compartidos_al_grupo = Compartido.objects.filter(grupo_destinatario=grupo_seleccionado)

    return render(request, 'grupo_info.html', {
        'usuario_actual': usuario_actual,
        'group_name': name,
        'group': grupo_seleccionado,
        'descripcion_grupo': descripcion_grupo,
        'archivos_compartidos_al_grupo': archivos_compartidos_al_grupo,
    })



@csrf_protect
@accepted_user_required
@login_required
def descargar_archivo_grupo(request, group_name, archivo_id):
    # Obtener el archivo
    archivo = get_object_or_404(Archivo, pk=archivo_id)
    
    # Obtener el grupo
    grupo = get_object_or_404(Group, name=group_name)
    
    # Verificar si el usuario actual pertenece al grupo
    if not request.user.groups.filter(name=group_name).exists():
        raise Http404("No tienes permiso para acceder a este archivo.")

    # Verificar si el archivo pertenece al grupo
    if not Compartido.objects.filter(grupo_destinatario=grupo, archivo=archivo).exists():
        raise Http404("El archivo no está compartido en este grupo.")

    # Construir la ruta completa al archivo
    ruta_archivo = os.path.join(settings.MEDIA_ROOT2, str(archivo.id_APB2TAL), archivo.nombre_archivo)

    # Verificar si el archivo existe en el sistema de archivos
    if not os.path.exists(ruta_archivo):
        raise Http404("El archivo no existe.")
    
    clave = cargar_clave()
    fernet = Fernet(clave)
    with open(ruta_archivo, 'rb') as f:
        encrypted_contenido = f.read()
        contenido_archivo = fernet.decrypt(encrypted_contenido)

    # Crear una respuesta HTTP con el contenido del archivo
    response = HttpResponse(contenido_archivo, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{archivo.nombre_archivo}"'

    return response




