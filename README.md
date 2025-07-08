# Streaming Profile Manager

Este proyecto es una aplicación Django que automatiza la creación y eliminación de perfiles en plataformas de streaming como Disney+ y MAX.

## Prerrequisitos

- Docker
- Docker Compose

## Instalación

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd streaming
```

2. Construye y ejecuta los contenedores:
```bash
docker-compose up --build
```

## Uso

Una vez que el servidor esté en funcionamiento, puedes acceder a los siguientes endpoints:

### Disney+
- Crear perfil: `http://localhost:8000/disney/create`
- Eliminar perfil: `http://localhost:8000/disney/delete`

### MAX
- Crear perfil: `http://localhost:8000/max/create`
- Eliminar perfil: `http://localhost:8000/max/delete`

Todos los endpoints esperan una petición POST con un JSON que contenga:
- Para crear perfiles:
```json
{
    "email": "tu@email.com",
    "password": "tu_contraseña"
}
```

- Para eliminar perfiles:
```json
{
    "email": "tu@email.com",
    "password": "tu_contraseña",
    "profile": "nombre_del_perfil"
}
```

## Estructura del Proyecto

```
├── Dockerfile           # Configuración de la imagen Docker
├── docker-compose.yml   # Configuración de servicios Docker
├── requirements.txt     # Dependencias de Python
├── manage.py           # Script de administración de Django
├── scraper/            # Configuración principal del proyecto Django
└── streaming/          # Aplicación principal con la lógica de negocio
```

## Notas Importantes

1. **Compatibilidad con Apple Silicon**: El proyecto está configurado para usar Chromium en lugar de Google Chrome para garantizar la compatibilidad con arquitecturas ARM64.

2. **Docker Desktop**: Asegúrate de que el directorio del proyecto esté compartido en las preferencias de Docker Desktop para evitar errores de montaje.

3. **Puertos**: El servidor Django se ejecuta en el puerto 8000. Asegúrate de que este puerto esté disponible en tu sistema.

## Solución de Problemas

Si encuentras el error "mounts denied" en macOS:
1. Abre Docker Desktop
2. Ve a Preferencias > Resources > File Sharing
3. Agrega la ruta del proyecto
4. Aplica y reinicia Docker Desktop

Alternativamente, puedes mover el proyecto a un directorio que ya esté compartido por defecto (como dentro de tu directorio home).

