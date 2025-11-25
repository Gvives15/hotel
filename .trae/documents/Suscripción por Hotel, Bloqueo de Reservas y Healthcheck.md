## Bloque 1 – Modelo Hotel: plan, estado de suscripción y helper

- Archivo: `app/administration/models.py`
- Acciones:
  - Agregar constantes de choices: `PLAN_STARTER`, `PLAN_GROW`, `PLAN_CHOICES`; `SUB_TRIAL`, `SUB_ACTIVE`, `SUB_BLOCKED`, `SUB_CANCELLED`, `SUBSCRIPTION_STATUS_CHOICES`.
  - Añadir campos al modelo `Hotel`: `plan_name`, `subscription_status`, `trial_until`, `is_blocked` (mantener si existe).
  - Añadir helper:
    - `@property def can_accept_new_bookings(self) -> bool` que retorne `subscription_status in {SUB_TRIAL, SUB_ACTIVE} and not is_blocked`.
- Migraciones:
  - Ejecutar `makemigrations` y `migrate` para persistir nuevos campos.

## Bloque 2 – Sincronizar suscripción ↔ bloqueado (Superadmin)

- Archivo: `app/administration/models.py`
- Acciones:
  - Añadir método `sync_block_from_subscription(self)` con reglas:
    - `trial/active` → `is_blocked = False`
    - `blocked/cancelled` → `is_blocked = True`
- Archivo: `app/core/views.py` (vistas Superadmin de hoteles)
- Acciones:
  - En la vista de edición/guardado de Hotel (si hay `ModelForm`): antes de `hotel.save()` llamar `hotel.sync_block_from_subscription()`.
  - Si no hay `ModelForm`, al procesar POST donde se actualiza `subscription_status`, invocar `sync_block_from_subscription()` y luego `save()`.
  - Mantener flujo actual de `superadmin_block_hotel`/`superadmin_unblock_hotel` para acciones directas de bloqueo.

## Bloque 3 – Bloqueo de creación de reservas para hoteles no habilitados

- Web pública (portal por slug):
  - Archivo: `app/core/views.py`
  - Ubicación: en la vista que crea la reserva directa (ej. `hotel_confirm_reservation_view`) y en el flujo multi‑paso donde se ejecuta el `Booking.objects.create(...)` (hay un bloque desde ~`app/core/views.py:931` con creación de booking).
  - Acción:
    - Antes de `Booking.objects.create(...)`, obtener `hotel` y validar:
      - `if not hotel.can_accept_new_bookings: messages.error(...); redirect` hacia home del hotel (`client_index_hotel`).

- Panel interno:
  - Archivo: `app/bookings/views.py`
  - Ubicación: función `create_booking_final` u otras vistas de creación manual.
  - Acción:
    - Antes de crear el booking, obtener el hotel (del contexto/panel slug) y validar `can_accept_new_bookings` con mensaje de error y redirect a list de reservas del panel por hotel.

- API (Django Ninja):
  - Archivo: `app/bookings/api.py`
  - Ubicación: endpoint de creación (por ejemplo `create_booking_api` o equivalente mencionado en docs).
  - Acción:
    - Resolver hotel desde request/payload.
    - `if not hotel.can_accept_new_bookings: raise HttpError(403, "Este hotel no está aceptando reservas nuevas.")`.

## Bloque 4 – Healthcheck `/health/`

- Archivo: `app/core/views.py`
- Acciones:
  - Añadir `health_view(request)` que ejecuta `SELECT 1` vía `connection.cursor()` y retorna `JsonResponse({"status": "ok"|"error"})`.
- Archivo: `config/urls.py`
- Acciones:
  - Importar `health_view` y añadir `path("health/", health_view, name="health")`.

## Bloque 5 – Superadmin: ver y cambiar plan/estado

- Django Admin (rápido):
  - Archivo: `app/administration/admin.py`
  - Acciones:
    - Registrar `HotelAdmin` con `list_display = ("name", "plan_name", "subscription_status", "is_blocked")`, `list_filter`, `search_fields` y `fields` incluyendo los nuevos campos.

- Panel Superadmin (opcional si se desea UI fuera del admin):
  - Archivo: `templates/superadmin/hotels_list.html` y `templates/superadmin/hotel_detail.html`
  - Acciones:
    - Mostrar columnas/etiquetas de `plan_name` y `subscription_status`.
    - En detalle, agregar un pequeño formulario (select de `subscription_status`) que al guardar llame a la vista que aplica `sync_block_from_subscription()`
    - Reutilizar estilos existentes.

## Bloque 6 – Seed `seed_o11ce.py` alineado

- Archivo: `app/core/management/commands/seed_o11ce.py`
- Acciones:
  - Al crear/obtener hoteles `o11ce` y `demo-mini`, setear `plan_name` y `subscription_status` en `defaults`.
  - Tras crear, invocar `sync_block_from_subscription()` y `save()` para reflejar bloqueo/desbloqueo.
  - Mantener lógica existente de habitaciones y reservas.

## Bloque 7 – IA: log de uso vinculado a hotel

- Archivo: `app/core/views.py` (endpoints `/superadmin/api/ia/analisis/` y similares)
- Acciones:
  - Al final de cada request (success o error), crear `ActionLog` con `user`, `action="superadmin_ia_analisis"`, `description` con `scope`, `hotel_id`, `status`. Si el endpoint recibe `hotel_id`, incluirlo en `ActionLog.hotel` si está disponible.

## Consideraciones técnicas de integración

- Ubicaciones confirmadas:
  - Hotel y administración están en `app/administration/` (modelo `Hotel` y admin).
  - Creación de reservas existe en `app/core/views.py` (portal/slug) y `app/bookings/views.py` (`create_booking_final`) y endpoints API en `app/bookings/api.py`.
  - Seed `seed_o11ce.py` ya existe y crea hoteles, habitaciones y reservas.
- Estilos/UI:
  - Evitar tocar estilos globales; añadir campos/controles respetando templates y clases existentes.
- Validación unificada:
  - La regla de negocio se centraliza en `Hotel.can_accept_new_bookings` y se utiliza en todos los puntos de creación.

## Orden de ejecución

1. Bloque 1: modelo y helper + migraciones.
2. Bloque 2: sincronización al guardar en Superadmin.
3. Bloque 3: validación en portal, panel y API.
4. Bloque 4: healthcheck.
5. Bloque 5: admin para gestionar plan/estado.
6. Bloque 6: seed alineado.
7. Bloque 7: logs IA.

¿Confirmo y avanzo con los cambios en estos archivos siguiendo este orden?