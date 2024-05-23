from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.db import models
# Create your models here.

class Task(models.Model):
  title = models.CharField(max_length=200)
  description = models.TextField(max_length=1000)
  created = models.DateTimeField(auto_now_add=True)
  datecompleted = models.DateTimeField(null=True, blank=True)
  completed = models.BooleanField(default=False)
  important = models.BooleanField(default=False)
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

  def __str__(self):
    return self.title + ' - ' + self.user.username
  
class Archivo(models.Model):
  id_APB2TAL = models.CharField(max_length=640, default=False)
  archivo_hash = models.CharField(max_length=640)
  nombre_archivo = models.CharField(max_length=255)
  positivos = models.IntegerField()
  current_time = models.DateTimeField(auto_now_add=True)
  tamaño = models.CharField(max_length=255, default=False)


  def __str__(self):
    return self.title 
  


class adquisicion(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
  group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
  archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE)
  
  def __str__(self):
    return self.title 


class Compartido(models.Model):
    usuario_propietario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='archivos_usuario_propietario', on_delete=models.CASCADE, null=True)
    grupo_propietario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='archivos_grupo_propietario', on_delete=models.CASCADE, null=True)
    usuario_destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='archivos_usuario_destino', on_delete=models.CASCADE, null=True)
    grupo_destinatario = models.ForeignKey(Group, related_name='archivos_grupo_destino', on_delete=models.CASCADE, null=True)
    
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE)
    
    def __str__(self):
     return None
   
   
   
   


class Mensajes(models.Model):
    enviador = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enviador_mensajes', on_delete=models.CASCADE, null=True)
    receptor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='receptor_mensajes', on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    tipomensaje = models.CharField(max_length=200, null=True)
    description = models.TextField(max_length=1000)
    leido = models.BooleanField(default=False)
    hora_envio = models.DateTimeField(auto_now_add=True, null=True)  # Agrega este campo
    
    def __str__(self):
        return self.title
    


  

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Modelo de usuario personalizado
class CustomUser(AbstractUser):
    is_accepted = models.BooleanField(
        _("accept status"),
        default=False,
        help_text=_("Designates whether this user is accepted."),
    )
    edad = models.IntegerField(default=None, null=True, blank=True)

    def __str__(self):
        return self.username
    
    
from django.contrib.auth.models import Group

class CustomGroup(Group):
    # Agrega campos adicionales aquí
    namenombre = models.CharField(_("name"), max_length=150, unique=True, default=None)
    description = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Grupo Personalizado'
        verbose_name_plural = 'Grupos Personalizados'