from django.shortcuts import render, redirect
from django.http import HttpResponse
from pymongo import MongoClient
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login



''''
def mostrar_datos(request):
    # Conectarse a MongoDB
    client = MongoClient('localhost', 27018)
    db = client['django']  # Nombre de tu base de datos MongoDB
    collection = db['archivos']  # Nombre de tu colección MongoDB

    # Realizar la consulta
    documento = collection.find_one({})

    # Pasar los datos a la plantilla para mostrarlos
    return render(request, 'template.html', {'documento': documento})
'''

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
                password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('panel')
            
            except:
                return render(request, 'signup.html',{
                'form' : UserCreationForm,
                'error' : 'Username already exists'
                })
        return render(request, 'signup.html',{
            'form' : UserCreationForm,
            'error' : 'Passwords do not Match'
            })  

def panel(request):
        return render(request, 'panel.html')
