#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from app.clients.models import Client

def check_users():
    print("=== VERIFICACIÓN DE USUARIOS ===")
    print(f"Total usuarios en la base de datos: {User.objects.count()}")
    print()
    
    print("Últimos 10 usuarios registrados:")
    users = User.objects.all().order_by('-id')[:10]
    
    if not users:
        print("No hay usuarios registrados.")
        return
    
    for user in users:
        print(f"- ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Nombre: {user.first_name} {user.last_name}")
        print(f"  Activo: {user.is_active}")
        print(f"  Staff: {user.is_staff}")
        print(f"  Superuser: {user.is_superuser}")
        print(f"  Fecha registro: {user.date_joined}")
        
        # Verificar si tiene cliente asociado
        try:
            client = user.client
            print(f"  Cliente asociado: Sí (ID: {client.id})")
        except Client.DoesNotExist:
            print(f"  Cliente asociado: No")
        
        print(f"  Contraseña hash: {user.password[:20]}...")
        print()

if __name__ == "__main__":
    check_users()