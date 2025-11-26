# Documento Técnico del Proyecto

## Estructura General
- Archivo principal: `TECNICO.md` (formato Markdown, con índice y enlaces internos)
- Secciones: Introducción, Detalles Técnicos, Instalación y Configuración, Manual de Uso, Documentación para Desarrolladores, Troubleshooting
- Navegación: Tabla de contenidos + enlaces ancla por sección
- Diagramas: Incluidos con Mermaid (`flowchart` y `sequence`), y arquitectura en `graph TD`

## 1. Introducción
- Objetivos del proyecto: qué problema resuelve y KPIs clave
- Alcance funcional: módulos cubiertos (reservas, habitaciones, clientes, administración, IA)
- Requisitos previos: Python, Django, base de datos, Node opcional para assets
- Diagrama de arquitectura general: Mermaid `graph TD` con capas (Cliente → Django Templates → Django Views/API → DB → n8n/IA)

## 2. Detalles Técnicos
- Especificaciones de implementación: stack (Django 5, Templates, API, Rooms/Bookings/Clients), patrones usados, manejo de sesiones, seguridad
- Diagramas de flujo: procesos clave (reserva web, confirmación, cancelación, onboarding de hotel)
- Estructura de directorios y archivos: árbol del proyecto resaltando `app/core`, `app/bookings`, `app/administration`, `templates`, `static`, `config`
- Dependencias y versiones: lista con versión mínima recomendada y compatibilidad (Django, decouple, dj-database-url, corsheaders)

## 3. Guías de Instalación y Configuración
- Requisitos del sistema: OS, Python 3.11+, PostgreSQL/SQLite, navegador
- Pasos de instalación: crear venv, instalar requirements, migraciones, crear superusuario, ejecutar servidor
- Configuraciones recomendadas: `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `EMAIL_*`
- Variables de entorno: `DJANGO_SECRET_KEY`, `DATABASE_URL` opcional, `SQLITE_PATH`, `N8N_IA_WEBHOOK_URL`

## 4. Manual de Uso
- Funcionalidades principales: portal de reservas, gestión interna, dashboard, IA
- Ejemplos de uso: flujos de reserva y administración con rutas y pantallas
- Capturas de pantalla: referencias y descripciones de pantallas clave (portal, habitaciones, checkout)
- Limitaciones conocidas: puntos a mejorar (multimoneda, performance de imágenes, internacionalización)

## 5. Documentación para Desarrolladores
- Convenciones de código: Python/Django (nomenclatura, imports, templates), CSS del diseño Booking-like
- Guía de contribución: branching, PRs, estilo de commits, revisión
- Proceso de testing: tipos de tests (unit, integración), cómo ejecutarlos
- Pipeline CI/CD: propuesta con acciones (lint, tests, build, deploy) y gates

## 6. Troubleshooting
- Problemas comunes y soluciones: estáticos 404, migraciones, env vars, CSRF, correos
- Pasos de diagnóstico: logs, comandos, checklist

## Entregables
- `TECNICO.md` con todos los contenidos
- Diagramas Mermaid incrustados
- Índice navegable con enlaces

¿Confirmas que proceda a generar el documento `TECNICO.md` con esta estructura y contenido?