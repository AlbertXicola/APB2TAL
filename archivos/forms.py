from django import forms
from .models import *

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'important', 'completed']
        widgets = {

            'title' : forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write a title'}),
            'description' : forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write a description'}),
            'important' : forms.CheckboxInput(attrs={'class': 'form-check-input ',}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input '}),
        }
    
    
        
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django_recaptcha.fields import ReCaptchaField

class CustomUserCreationForm(UserCreationForm):
    captcha = ReCaptchaField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        #fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'captcha']


class RepoForm(forms.Form):
    repo_url = forms.URLField(
        label="URL del repositorio",
        max_length=200,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/usuario/repositorio.git'
        })
    )
