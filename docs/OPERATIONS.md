# Guía de Operaciones

Este documento resume los procedimientos recomendados para operar el sistema en distintos entornos, ejecutar migraciones y seeds, validar la salud del servicio y gestionar despliegues y respaldos.

## Entornos (dev/staging/prod)

### Variables de entorno clave
Configura estas variables antes de levantar el servicio en cualquier entorno:

- `DJANGO_SETTINGS_MODULE`: Ajusta al módulo de configuración correcto (p. ej., `config.settings` por defecto).
- `SECRET_KEY`: Clave secreta de Django (única y no comprometida).
- `DEBUG`: `True` en desarrollo, `False` en staging y producción.
- `ALLOWED_HOSTS`: Lista de dominios o IPs válidos para el entorno.
- `DATABASE_URL` o variables equivalentes de SQLite/otro motor si se usa configuración personalizada.
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS`: Para envío de correos en entornos que lo requieran.

### Desarrollo
1. Crear/activar un entorno virtual y instalar dependencias: `pip install -r requirements.txt`.
2. Verificar variables de entorno mínimas (`DEBUG=True`, `SECRET_KEY`, `ALLOWED_HOSTS=localhost` o similar).
3. Aplicar migraciones y cargar datos de ejemplo (ver secciones de migraciones y seeds).
4. Iniciar el servidor local: `python manage.py runserver 0.0.0.0:8000`.

### Staging
1. Ajustar `DEBUG=False` y `ALLOWED_HOSTS` al dominio de staging.
2. Configurar base de datos persistente (p. ej., PostgreSQL) y credenciales de correo reales o sandbox.
3. Ejecutar migraciones en la base de staging antes de desplegar código nuevo.
4. Sembrar datos mínimos si se requiere para pruebas funcionales (usuarios de prueba, habitaciones, etc.).
5. Levantar el servicio en modo gunicorn/uvicorn o el servidor usado en la plataforma de staging.

### Producción
1. `DEBUG=False`, `SECRET_KEY` exclusivo, y `ALLOWED_HOSTS` con el dominio productivo.
2. Usar base de datos gestionada y credenciales seguras; habilitar TLS en la capa de aplicación o en el balanceador.
3. Ejecutar migraciones en ventana de mantenimiento o con despliegues que apliquen migraciones automáticamente.
4. Sembrar solo datos estrictamente necesarios (usuarios admin iniciales, catálogos base) en coordinación con negocio.
5. Habilitar monitoreo de logs y métricas; configurar rotación de logs y backups automáticos.

## Migraciones

1. Crear nuevas migraciones cuando cambien los modelos: `python manage.py makemigrations`.
2. Revisar las migraciones generadas y versionarlas en el repositorio.
3. Aplicarlas en el entorno objetivo:
   - Local/Staging: `python manage.py migrate`.
   - Producción: aplicar mediante el proceso de despliegue automatizado o ejecutar `python manage.py migrate` con las variables de entorno del entorno productivo.
4. Confirmar el estado de la base tras aplicar migraciones revisando logs y probando endpoints críticos.

## Seeds de datos (`populate_data.py`)

El script `docs/populate_data.py` siembra datos iniciales (habitaciones, usuarios de prueba, etc.). Procedimiento recomendado:

1. Asegurar que la base esté migrada.
2. Ejecutar en el entorno deseado:
   ```bash
   python docs/populate_data.py
   ```
3. Para entornos de staging/producción, revisar y ajustar el script antes de ejecutarlo para evitar datos de prueba no deseados.
4. Validar que los datos aparezcan correctamente (consultar panel de admin o endpoints de lectura).

## Checklist de salud

- **Logs**: Revisar los logs de aplicación y del servidor (gunicorn/uvicorn, nginx) en busca de errores recientes.
- **Servicios**: Confirmar que los procesos web y de base de datos están activos (p. ej., `systemctl status <servicio>` o supervisión en la plataforma de despliegue).
- **Migraciones**: Verificar que no haya migraciones pendientes (`python manage.py showmigrations`).
- **Endpoints críticos**: Probar endpoints básicos (home, login, reserva) y revisar tiempos de respuesta.
- **Almacenamiento y disco**: Chequear espacio libre y rotación de logs.

## Respaldo y restauración de la base de datos

- **SQLite (por defecto del repo)**:
  - Respaldo: copiar `db.sqlite3` a una ubicación segura (idealmente con timestamp). Ejemplo: `cp db.sqlite3 backups/db-$(date +%F).sqlite3`.
  - Restaurar: reemplazar `db.sqlite3` por el respaldo deseado y aplicar migraciones si fuera necesario.
- **PostgreSQL u otro motor**:
  - Respaldo: usar herramientas nativas (`pg_dump`, `mysqldump`, etc.) con cron o pipeline CI para backups regulares.
  - Restaurar: `psql < respaldo.sql` (PostgreSQL) o comando equivalente, seguido de migraciones si aplica.
- Mantener respaldos en almacenamiento seguro (S3, buckets privados) con políticas de retención y cifrado.

## Estrategia de despliegue

### Vercel
- Este proyecto incluye `vercel.json`; se puede desplegar como app serverless configurando el entrypoint a `api/index.py` o similar según la configuración actual.
- Ajustar variables de entorno en el panel de Vercel (SECRET_KEY, base de datos remota, correo, etc.).
- Habilitar builds reproducibles con `requirements.txt` y, si aplica, comandos previos para migraciones (p. ej., hook o acción separada en CI que ejecute `python manage.py migrate` en una base gestionada).

### Servidor local/VM
- Usar gunicorn/uvicorn + nginx o similar.
- Instalar dependencias, aplicar migraciones, cargar seeds necesarios y arrancar el servicio como unidad systemd.
- Configurar supervisión (systemd, supervisor) y rotación de logs.

### Automatizaciones recomendadas
- Pipeline CI que ejecute tests y chequee migraciones antes de desplegar.
- Job/CD que, al desplegar a staging/producción, ejecute automáticamente `python manage.py migrate` contra la base del entorno.
- Tareas programadas para respaldos de base de datos y limpieza/rotación de logs.
- Alertas sobre fallos en despliegue, errores 5xx y espacio en disco.

## Referencias rápidas

- Ejecutar servidor: `python manage.py runserver 0.0.0.0:8000`
- Migraciones: `python manage.py makemigrations && python manage.py migrate`
- Seeds de datos: `python docs/populate_data.py`
- Chequeo de migraciones pendientes: `python manage.py showmigrations`

