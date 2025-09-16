# Hotel O11CE - Interfaz Web

## Descripción

Sistema de gestión hotelera con interfaz web moderna y responsiva. Incluye todas las funcionalidades del backend a través de una interfaz gráfica intuitiva.

## Características

### 🎨 Diseño Moderno
- Interfaz responsiva que funciona en desktop, tablet y móvil
- Diseño con gradientes y animaciones suaves
- Iconografía Font Awesome
- Tipografía Poppins para mejor legibilidad

### 🔐 Sistema de Autenticación
- Login seguro con validación
- Registro de nuevos usuarios
- Gestión de perfiles de usuario
- Sesiones persistentes

### 📊 Dashboard Principal
- Estadísticas en tiempo real
- Acciones rápidas
- Reservas recientes
- Estado de habitaciones
- Alertas de mantenimiento
- Programación de limpieza

### 🏨 Módulos Principales
- **Habitaciones**: Gestión completa de habitaciones
- **Reservas**: Sistema de reservas y check-in/out
- **Clientes**: Base de datos de clientes
- **Limpieza**: Programación y seguimiento de limpieza
- **Mantenimiento**: Gestión de solicitudes de mantenimiento
- **Administración**: Configuraciones del sistema
- **Reportes**: Análisis y estadísticas

## Instalación y Configuración

### 1. Requisitos Previos
```bash
# Asegúrate de tener Python 3.8+ instalado
python --version

# Instala las dependencias
pip install -r requirements.txt
```

### 2. Configuración de la Base de Datos
```bash
# Ejecuta las migraciones
python manage.py makemigrations
python manage.py migrate

# Crea un superusuario
python manage.py createsuperuser
```

### 3. Ejecutar el Servidor
```bash
# Inicia el servidor de desarrollo
python manage.py runserver

# El sistema estará disponible en:
# http://localhost:8000
```

## Estructura de Archivos

```
templates/
├── base.html              # Template base con estilos
├── login.html             # Página de login
├── register.html          # Página de registro
├── dashboard.html         # Dashboard principal
├── profile.html           # Perfil de usuario
└── settings.html          # Configuración del sistema
```

## Uso del Sistema

### 1. Acceso Inicial
- Ve a `http://localhost:8000`
- Si no tienes cuenta, haz clic en "Regístrate aquí"
- Completa el formulario de registro
- Inicia sesión con tus credenciales

### 2. Navegación
- **Dashboard**: Vista general del sistema
- **Sidebar**: Navegación entre módulos
- **Navbar**: Acceso rápido a perfil y configuración

### 3. Funcionalidades Principales

#### Dashboard
- Estadísticas en tiempo real
- Acciones rápidas para tareas comunes
- Vista de reservas recientes
- Estado de habitaciones
- Alertas de mantenimiento

#### Gestión de Habitaciones
- Ver todas las habitaciones
- Estado en tiempo real
- Filtros por tipo y estado
- Acciones rápidas

#### Sistema de Reservas
- Crear nuevas reservas
- Ver reservas existentes
- Check-in/out
- Historial de reservas

#### Gestión de Clientes
- Base de datos de clientes
- Información de contacto
- Historial de estancias
- Preferencias

#### Limpieza
- Programar tareas de limpieza
- Asignar empleados
- Seguimiento de estado
- Reportes de limpieza

#### Mantenimiento
- Reportar problemas
- Asignar prioridades
- Seguimiento de reparaciones
- Historial de mantenimiento

## Personalización

### Colores y Estilos
Los estilos están definidos en `templates/base.html` usando variables CSS:

```css
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #e74c3c;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    /* ... más variables */
}
```

### Agregar Nuevas Páginas
1. Crea un nuevo template en `templates/`
2. Extiende `base.html`
3. Agrega la vista en `app/core/views.py`
4. Configura la URL en `config/urls.py`

## API REST

El sistema también incluye una API REST completa:

- **Documentación**: `http://localhost:8000/api/docs`
- **Swagger UI**: `http://localhost:8000/api/scalar`
- **ReDoc**: `http://localhost:8000/api/redoc`

## Seguridad

- Autenticación requerida para todas las páginas
- Validación de formularios
- Protección CSRF
- Sesiones seguras
- Logout automático

## Responsive Design

El sistema es completamente responsivo:

- **Desktop**: Vista completa con sidebar
- **Tablet**: Sidebar colapsable
- **Móvil**: Menú hamburguesa y diseño optimizado

## Soporte

Para soporte técnico o reportar problemas:

1. Revisa la documentación de la API
2. Consulta los logs del servidor
3. Verifica la configuración de la base de datos
4. Contacta al equipo de desarrollo

## Tecnologías Utilizadas

- **Backend**: Django 5.2
- **API**: Django Ninja
- **Frontend**: HTML5, CSS3, JavaScript
- **Framework CSS**: Bootstrap 5.3
- **Iconos**: Font Awesome 6.4
- **Base de Datos**: SQLite (desarrollo)

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.
