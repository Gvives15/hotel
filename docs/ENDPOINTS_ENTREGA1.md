# 📋 Endpoints Backend - Entrega 1

## 🚀 Descripción General

Esta documentación describe los endpoints implementados para la **Entrega 1** del sistema O11CE usando **Django Ninja**.

---

## 📍 Endpoints Disponibles

### 1. `GET /habitaciones-disponibles/`

**App:** `rooms`  
**Función:** Devuelve habitaciones disponibles entre dos fechas para cierta cantidad de personas.

#### 🔧 Parámetros Query:
- `fecha_inicio` (date): Fecha de inicio de la búsqueda
- `fecha_fin` (date): Fecha de fin de la búsqueda  
- `personas` (int): Número de personas para la reserva

#### 📋 Lógica:
1. **Filtra habitaciones** que tengan `estado = 'libre'`
2. **Verifica capacidad** que `capacidad >= personas`
3. **Excluye reservas superpuestas** entre las fechas especificadas
4. **Retorna lista** de habitaciones disponibles con detalles

#### 📄 Ejemplo de Request:
```
GET /api/habitaciones-disponibles/?fecha_inicio=2025-01-15&fecha_fin=2025-01-18&personas=2
```

#### 📄 Ejemplo de Response:
```json
{
  "success": true,
  "message": "Se encontraron 3 habitaciones disponibles",
  "rooms": [
    {
      "id": 1,
      "number": "101",
      "type": "Doble",
      "capacity": 2,
      "price": 150.00,
      "description": "Habitación doble con vista al mar",
      "floor": 1
    }
  ],
  "total_rooms": 3
}
```

---

### 2. `POST /reservas/crear-con-cliente/`

**App:** `bookings`  
**Función:** Crea el cliente si no existe y luego la reserva, validando disponibilidad.

#### 🔧 Parámetros Body:
```json
{
  "nombre": "Juan Pérez",
  "email": "juan@mail.com",
  "telefono": "123456789",
  "dni": "11222333",
  "habitacion_id": 5,
  "fecha_inicio": "2025-08-20",
  "fecha_fin": "2025-08-25",
  "solicitudes_especiales": "Cama extra si es posible"
}
```

#### 📋 Lógica:
1. **Valida fechas** (inicio < fin)
2. **Busca o crea cliente** por email
3. **Verifica disponibilidad** de la habitación
4. **Valida no hay reservas superpuestas**
5. **Crea reserva** con estado `confirmada`
6. **Actualiza estado** de la habitación

#### 📄 Ejemplo de Response:
```json
{
  "success": true,
  "message": "Reserva creada exitosamente. Cliente creado.",
  "booking_id": 15,
  "client_id": 8,
  "total_price": 750.00
}
```

---

### 3. `POST /manda_email_cliente/` (Opcional)

**App:** `core`  
**Función:** Envía un email de confirmación con los datos de la reserva.

#### 🔧 Parámetros Body:
```json
{
  "reserva_id": 15
}
```

#### 📋 Lógica:
1. **Obtiene datos** de la reserva y cliente
2. **Verifica** que la reserva esté confirmada
3. **Genera email** con detalles completos
4. **Simula envío** (configurable para email real)

#### 📄 Ejemplo de Response:
```json
{
  "success": true,
  "message": "Email de confirmación enviado exitosamente a juan@mail.com"
}
```

---

## 🛠️ Configuración Técnica

### 📁 Estructura de Archivos:
```
app/
├── rooms/
│   ├── api.py          # Endpoint habitaciones disponibles
├── bookings/
│   ├── api.py          # Endpoint crear reserva
├── core/
│   ├── api.py          # Endpoint email
└── config/
    ├── urls.py         # Configuración de routers
    └── settings.py     # Configuración de API
```

### 🔧 Dependencias:
- **Django Ninja**: Framework para APIs
- **Django**: Framework web
- **SQLite**: Base de datos (configurable)

---

## 🧪 Testing

### Script de Pruebas:
```bash
python test_endpoints.py
```

### Pruebas Manuales:
1. **Habitaciones disponibles**: Verificar filtrado correcto
2. **Crear reserva**: Validar creación de cliente y reserva
3. **Email**: Confirmar simulación de envío

---

## 📊 Estados de Respuesta

### ✅ Éxito:
```json
{
  "success": true,
  "message": "Operación exitosa",
  "data": {...}
}
```

### ❌ Error:
```json
{
  "success": false,
  "message": "Descripción del error",
  "data": null
}
```

---

## 🔍 Validaciones Implementadas

### Habitaciones Disponibles:
- ✅ Fechas coherentes (inicio < fin)
- ✅ Número de personas > 0
- ✅ Estado habitación = 'libre'
- ✅ Sin reservas superpuestas

### Crear Reserva:
- ✅ Cliente existe o se crea
- ✅ Habitación disponible
- ✅ Fechas válidas
- ✅ Sin conflictos de reserva
- ✅ Transacción atómica

### Email:
- ✅ Reserva existe
- ✅ Reserva confirmada
- ✅ Datos completos

---

## 🚀 Próximos Pasos

1. **Configurar email real** en `settings.py`
2. **Agregar autenticación** si es necesario
3. **Implementar más validaciones** según necesidades
4. **Agregar logging** para debugging
5. **Optimizar consultas** de base de datos

---

## 📞 Soporte

Para dudas o problemas con los endpoints, revisar:
- Logs del servidor Django
- Respuestas de error detalladas
- Validaciones en los modelos
- Configuración de la base de datos 