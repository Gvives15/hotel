# Documentación de la API O11CE

## Descripción General

La API O11CE es una API REST completa para el sistema de gestión hotelera. Proporciona endpoints para gestionar habitaciones, reservas, clientes, mantenimiento y limpieza.

## URLs de Documentación

### 1. Swagger UI
- **URL**: `/api/docs`
- **Descripción**: Interfaz interactiva para probar la API
- **Características**: Permite ejecutar requests directamente desde el navegador

### 2. ReDoc
- **URL**: `/api/redoc`
- **Descripción**: Documentación alternativa con mejor presentación
- **Características**: Mejor para leer la documentación

### 3. Scalar
- **URL**: `/api/scalar`
- **Descripción**: Interfaz moderna y elegante para la documentación
- **Características**: Diseño moderno con tema oscuro por defecto

### 4. OpenAPI JSON
- **URL**: `/api/openapi.json`
- **Descripción**: Especificación OpenAPI en formato JSON
- **Uso**: Para herramientas de terceros o generación de clientes

## Información de la API
- **URL**: `/api/info`
- **Descripción**: Información general sobre la API

## Endpoints Principales

### Habitaciones (`/api/rooms/`)
- `GET /api/rooms/` - Listar todas las habitaciones
- `POST /api/rooms/` - Crear nueva habitación
- `GET /api/rooms/{id}/` - Obtener habitación específica
- `PUT /api/rooms/{id}/` - Actualizar habitación
- `DELETE /api/rooms/{id}/` - Eliminar habitación

### Reservas (`/api/bookings/`)
- `GET /api/bookings/` - Listar todas las reservas
- `POST /api/bookings/` - Crear nueva reserva
- `GET /api/bookings/{id}/` - Obtener reserva específica
- `PUT /api/bookings/{id}/` - Actualizar reserva
- `DELETE /api/bookings/{id}/` - Eliminar reserva

## Autenticación

La API utiliza autenticación basada en tokens. Para endpoints protegidos, incluye el header:

```
Authorization: Bearer <tu-token>
```

## Ejemplos de Uso

### Crear una habitación
```bash
curl -X POST "http://localhost:8000/api/rooms/" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "101",
    "type": "SINGLE",
    "floor": 1,
    "price_per_night": 100.00,
    "is_available": true
  }'
```

### Crear una reserva
```bash
curl -X POST "http://localhost:8000/api/bookings/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "client_name": "Juan Pérez",
    "client_email": "juan@example.com",
    "check_in_date": "2024-01-15",
    "check_out_date": "2024-01-17",
    "total_price": 200.00
  }'
```

## Configuración de Desarrollo

### Servidores Disponibles
- **Desarrollo**: `http://localhost:8000/api`
- **Producción**: `https://api.o11ce.com/api`

### Variables de Entorno
```bash
# Configuración de la API
API_TITLE="O11CE API"
API_VERSION="1.0.0"
DEBUG=True
```

## Características de Scalar

### Configuración Personalizada
- **Tema**: Oscuro por defecto
- **Layout**: Moderno
- **Búsqueda**: Tecla 'K' para activar
- **Sidebar**: Habilitada
- **Modelos**: Visibles

### Personalización del Tema
El tema de Scalar está personalizado con los colores de O11CE:
- Color principal: `#009485`
- Modo oscuro habilitado
- Diseño moderno y limpio

## Herramientas de Desarrollo

### Generación de Clientes
Puedes generar clientes automáticamente usando el endpoint OpenAPI:

```bash
# Generar cliente Python
openapi-generator generate -i http://localhost:8000/api/openapi.json -g python -o ./client

# Generar cliente JavaScript
openapi-generator generate -i http://localhost:8000/api/openapi.json -g javascript -o ./client
```

### Testing
```bash
# Ejecutar tests
python manage.py test

# Ejecutar tests específicos
python manage.py test app.rooms.tests
```

## Soporte

Para soporte técnico, contacta a:
- **Email**: soporte@o11ce.com
- **Equipo**: Equipo O11CE

## Licencia

Este proyecto está bajo la licencia MIT. Ver detalles en: https://opensource.org/licenses/MIT 