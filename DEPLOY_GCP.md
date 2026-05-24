# Despliegue en Google Cloud (Cloud Run + Cloud SQL)

El archivo **principal que debes modificar** para apuntar a tu base de datos de Google Cloud es:

- `simulaciones_pequiven/settings.py`

## Variables de entorno requeridas

Configura estas variables en tu servicio (Cloud Run / App Engine):

- `SECRET_KEY`
- `DEBUG` (usar `False` en producción)
- `ALLOWED_HOSTS` (ej: `tu-dominio.com,tu-servicio-xyz.a.run.app`)
- `DB_ENGINE` (por defecto: `django.db.backends.mysql`)
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT` (normalmente `3306`)

## Ejemplo de conexión Cloud SQL (MySQL)

Si usas Cloud SQL con IP privada o pública autorizada:

- `DB_HOST`: IP de tu instancia de Cloud SQL
- `DB_PORT`: `3306`

Si usas Cloud SQL Auth Proxy/Conector, el `DB_HOST` será el host local/proxy definido por tu entorno.

## Recomendaciones de producción

- Mantén `DEBUG=False`.
- Configura correctamente `ALLOWED_HOSTS`.
- No hardcodear secretos en el repositorio.
- Ejecutar migraciones al desplegar:

```bash
python manage.py migrate
```

