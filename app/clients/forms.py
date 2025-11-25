from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Client


UserModel = get_user_model()

class ClientRegistrationForm(UserCreationForm):
    """Formulario personalizado para registro de clientes con validaciones mejoradas"""
    
    # Campos adicionales
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre'
        }),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu apellido'
        }),
        label='Apellido'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com'
        }),
        label='Email'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+54 9 11 1234-5678'
        }),
        label='Teléfono'
    )
    
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Dirección completa'
        }),
        label='Dirección'
    )
    
    nationality = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe para buscar tu país...'
        }),
        label='País de origen'
    )

    class Meta:
        model = UserModel
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario único'
            }),
        }
        labels = {
            'username': 'Usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de contraseñas
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña'
        })

    def clean_username(self):
        """Validación personalizada para nombre de usuario"""
        username = self.cleaned_data.get('username')
        
        if UserModel.objects.filter(username=username).exists():
            raise ValidationError(
                "Este nombre de usuario ya está en uso. Por favor, elige otro nombre de usuario único."
            )
        
        # Validar que no sea muy corto
        if len(username) < 3:
            raise ValidationError(
                "El nombre de usuario debe tener al menos 3 caracteres."
            )
            
        return username

    def clean_email(self):
        """Validación personalizada para email"""
        email = self.cleaned_data.get('email')
        
        # Verificar si el email ya existe en User
        if UserModel.objects.filter(email=email).exists():
            raise ValidationError(
                "Ya existe una cuenta registrada con este correo electrónico. "
                "Si ya tienes una cuenta, puedes iniciar sesión o recuperar tu contraseña."
            )
        
        # Verificar si el email ya existe en Client
        if Client.objects.filter(email=email).exists():
            raise ValidationError(
                "Este correo electrónico ya está registrado en nuestro sistema. "
                "Por favor, utiliza un correo electrónico diferente."
            )
            
        return email

    def clean_phone(self):
        """Validación personalizada para teléfono"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Remover espacios y caracteres especiales para validación
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            if len(clean_phone) < 8:
                raise ValidationError(
                    "El número de teléfono debe tener al menos 8 dígitos."
                )
                
        return phone

    def save(self, commit=True):
        """Guardar usuario con datos adicionales"""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
        return user