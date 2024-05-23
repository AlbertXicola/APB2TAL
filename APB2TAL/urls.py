"""
URL configuration for APB2TAL project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from archivos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('terminos/', views.terminos, name='terminos'),
    path('about/', views.about, name='about'),
    path('project/', views.project, name='project'),

    path('administrar/', views.administrar, name='administrar'),
    path('administrar/registros_admin/', views.registros_admin, name='registros_admin'),

    path('administrar/usuarios/', views.administrar_usuarios, name='administrar_usuarios'),
    path('administrar/usuarios/<int:id>/', views.admi_usuario, name='admi_usuario'),

    path('archivos/', views.archivos, name='archivos'),
    path('archivos/analizar/', views.archivos_analiz, name='archivos_analiz'),
    path('archivos/<int:archivo_id>/', views.archivos_manage, name='archivos_manage'),
    path('archivos/eliminar/<int:archivo_id>/', views.eliminar_archivo, name='eliminar_archivo'),
    path('archivos/descargar/<int:archivo_id>/', views.descargar_archivo, name='descargar_archivo'),
    path('archivos_manage/<int:archivo_id>/', views.archivos_manage, name='archivos_manage'),
    path('compartir_archivo/<int:archivo_id>/', views.compartir_archivo, name='compartir_archivo'),
    path('eliminar-compartido/', views.eliminar_compartido, name='eliminar_compartido'),


    path('compartido/descargar/<int:archivo_id>/', views.descargar_archivo_compartido, name='descargar_archivo_compartido'),
    path('compartido/eliminar/<int:archivo_id>/', views.eliminar_archivo_compartido, name='eliminar_archivo_compartido'),
    path('compartido/archivo/<int:archivo_id>/', views.compartido_archivo_info, name='compartido_archivo_info'),


    path('compartido/', views.compartido, name='compartido'),
    path('administrar/grupos/', views.administrar_grupos, name='administrar_grupos'),
    path('administrar/grupos/create', views.crear_grupo, name='crear_grupo'),
    path('administrar/grupos/<int:id>/', views.admi_grupo, name='admi_grupo'),
    

    path('contacta/', views.contacta, name='contacta'),
    path('contacta/administracion/', views.contact_admin, name='contact_admin'),
    path('contacta/buzon/', views.buzon, name='buzon'),
    path('eliminar-mensaje/<int:mensaje_id>/', views.eliminar_mensaje, name='eliminar_mensaje'),

    
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),

    path('registros/', views.registros, name='registros'),


    path('grupos/', views.mis_grupos, name= 'mis_grupos'),
    path('grupos/<str:name>/', views.grupo_info, name='grupo_info'),
    path('grupos/<str:group_name>/<int:archivo_id>/', views.descargar_archivo_grupo, name='descargar_archivo_grupo'),

    path('signup/', views.signup, name='signup'),
    path('validar_username/', views.validar_username, name='validar_username'),

    path('signout/', views.signout, name='signout'),
    path('signin/', views.signin, name='signin'),
    
    path('tasks/', views.tasks, name='tasks'),
    path('tasks_completed/', views.tasks_completed, name='tasks_completed'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/complete', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/delete', views.delete_task, name='delete_task'),

]

