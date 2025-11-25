# API Reference

Documento generado automáticamente a partir del esquema OpenAPI de Django Ninja.
Fecha de generación: 2025-11-25 06:21 UTC

URL base usada en ejemplos: `http://localhost:8000`

> Ejecuta `python manage.py generate_api_reference --base-url <URL>` para regenerar este archivo.

## GET /api/emails/

**Descripción:** Get Email Logs
**Tags:** Emails
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros
Este endpoint no requiere parámetros de entrada.

### Respuestas
- **200**: OK

### Ejemplos
curl -X GET "http://localhost:8000/api/emails/"
http GET http://localhost:8000/api/emails/

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## GET /api/habitaciones-disponibles/

**Descripción:** Get Available Rooms
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros
**Query/Path parameters**
- `fecha_inicio` (requerido) — string (date). 
- `fecha_fin` (requerido) — string (date). 
- `personas` (requerido) — integer. 

### Respuestas
- **200**: OK
  - `success` (requerido): boolean. 
  - `message` (requerido): string. 
  - `rooms` (requerido): array. 
  - `total_rooms` (requerido): integer. 

### Ejemplos
curl -X GET "http://localhost:8000/api/habitaciones-disponibles/?fecha_inicio=2024-01-01&fecha_fin=2024-01-01&personas=1"
http GET http://localhost:8000/api/habitaciones-disponibles/?fecha_inicio=2024-01-01&fecha_fin=2024-01-01&personas=1

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## GET /api/info

**Descripción:** Api Info
**Tags:** Información
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros
Este endpoint no requiere parámetros de entrada.

### Respuestas
- **200**: OK

### Ejemplos
curl -X GET "http://localhost:8000/api/info"
http GET http://localhost:8000/api/info

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## POST /api/manda_email_bienvenida/

**Descripción:** Send Welcome Email
**Tags:** Emails
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros

**Cuerpo (JSON)**
- `client_id` (requerido): integer. 

### Respuestas
- **200**: OK
  - `success` (requerido): boolean. 
  - `message` (requerido): string. 
  - `email_log_id` (opcional): object. 
  - `recipient_email` (opcional): object. 
  - `subject` (opcional): object. 

### Ejemplos
curl -X POST "http://localhost:8000/api/manda_email_bienvenida/" \
  -H 'Content-Type: application/json' \
  -d '{
  "client_id": 1
}'

http POST http://localhost:8000/api/manda_email_bienvenida/ \
  client_id=1

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## POST /api/manda_email_cliente/

**Descripción:** Send Email To Client
**Tags:** Emails
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros

**Cuerpo (JSON)**
- `reserva_id` (requerido): integer. 

### Respuestas
- **200**: OK
  - `success` (requerido): boolean. 
  - `message` (requerido): string. 
  - `email_log_id` (opcional): object. 
  - `recipient_email` (opcional): object. 
  - `subject` (opcional): object. 

### Ejemplos
curl -X POST "http://localhost:8000/api/manda_email_cliente/" \
  -H 'Content-Type: application/json' \
  -d '{
  "reserva_id": 1
}'

http POST http://localhost:8000/api/manda_email_cliente/ \
  reserva_id=1

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## POST /api/reservas/crear-con-cliente/

**Descripción:** Create Booking With Client
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros

**Cuerpo (JSON)**
- `nombre` (requerido): string. 
- `email` (requerido): string. 
- `telefono` (opcional): object. 
- `dni` (requerido): string. 
- `habitacion_id` (requerido): integer. 
- `fecha_inicio` (requerido): string (date). 
- `fecha_fin` (requerido): string (date). 
- `solicitudes_especiales` (opcional): object. 

### Respuestas
- **200**: OK
  - `success` (requerido): boolean. 
  - `message` (requerido): string. 
  - `booking_id` (opcional): object. 
  - `client_id` (opcional): object. 
  - `total_price` (opcional): object. 

### Ejemplos
curl -X POST "http://localhost:8000/api/reservas/crear-con-cliente/" \
  -H 'Content-Type: application/json' \
  -d '{
  "nombre": "texto",
  "email": "usuario@correo.com",
  "telefono": "texto",
  "dni": "12345678",
  "habitacion_id": 1,
  "fecha_inicio": "2024-01-01",
  "fecha_fin": "2024-01-01",
  "solicitudes_especiales": "texto"
}'

http POST http://localhost:8000/api/reservas/crear-con-cliente/ \
  nombre="texto" \
  email="usuario@correo.com" \
  telefono="texto" \
  dni="12345678" \
  habitacion_id=1 \
  fecha_inicio="2024-01-01" \
  fecha_fin="2024-01-01" \
  solicitudes_especiales="texto"

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## POST /api/reservas/{booking_id}/reenviar-email/

**Descripción:** Resend Booking Confirmation Email
**Autenticación y roles:** No requiere autenticación explícita.

### Parámetros
**Query/Path parameters**
- `booking_id` (requerido) — integer. 

### Respuestas
- **200**: OK
  - Tipo: object

### Ejemplos
curl -X POST "http://localhost:8000/api/reservas/<booking_id>/reenviar-email/" \
  -H 'Content-Type: application/json' \
  -d '{}'

http POST http://localhost:8000/api/reservas/<booking_id>/reenviar-email/

### Respuestas de error comunes
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.
- 404: Recurso no encontrado si el identificador no existe.

## GET /api/superadmin/chart

**Descripción:** Superadmin Chart
**Tags:** Superadmin
**Autenticación y roles:** Requiere usuario autenticado con rol de superusuario.

### Parámetros
**Query/Path parameters**
- `metric` (opcional) — string. 
- `interval` (opcional) — string. 
- `start_date` (opcional) — object. 
- `end_date` (opcional) — object. 

### Respuestas
- **200**: OK

### Ejemplos
curl -X GET "http://localhost:8000/api/superadmin/chart?metric=texto&interval=texto&start_date=texto&end_date=texto"
http GET http://localhost:8000/api/superadmin/chart?metric=texto&interval=texto&start_date=texto&end_date=texto

### Respuestas de error comunes
- 403: Acceso denegado por falta de permisos o rol insuficiente.
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## GET /api/superadmin/hotels

**Descripción:** Superadmin Hotels
**Tags:** Superadmin
**Autenticación y roles:** Requiere usuario autenticado con rol de superusuario.

### Parámetros
Este endpoint no requiere parámetros de entrada.

### Respuestas
- **200**: OK

### Ejemplos
curl -X GET "http://localhost:8000/api/superadmin/hotels"
http GET http://localhost:8000/api/superadmin/hotels

### Respuestas de error comunes
- 403: Acceso denegado por falta de permisos o rol insuficiente.
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.

## GET /api/superadmin/kpis

**Descripción:** Superadmin Kpis
**Tags:** Superadmin
**Autenticación y roles:** Requiere usuario autenticado con rol de superusuario.

### Parámetros
Este endpoint no requiere parámetros de entrada.

### Respuestas
- **200**: OK

### Ejemplos
curl -X GET "http://localhost:8000/api/superadmin/kpis"
http GET http://localhost:8000/api/superadmin/kpis

### Respuestas de error comunes
- 403: Acceso denegado por falta de permisos o rol insuficiente.
- 400: Solicitud inválida o datos incompletos.
- 422: Error de validación en los datos enviados.
- 500: Error interno del servidor.
