# Alquileres de Aragón

Aplicación web que muestra en un mapa los precios medios de los alquileres para un código postal de Aragón.

La fuente principal de los datos es el IGEAR y sus servicios de mapas web.

## Arquitectura

El proyecto consta de tres componentes principales:

- **Frontend**: Aplicación Angular 19 con mapas OpenLayers (`aod-fianzas/`)
- **Backend**: API FastAPI con servicios de búsqueda geográfica (`aod-fianzas-back/`)
- **Cache**: Redis para optimización de rendimiento de peticiones IGEAR

## Desarrollo Local

### Frontend (Angular)

```bash
cd aod-fianzas
npm install
ng serve  # http://localhost:4200
```

El frontend usa configuración en tiempo de ejecución desde `src/assets/config/config.json`:
- Para **ng serve**: Usa `config.json` (versionado) con configuración localhost
- Para **Docker**: El script `docker-entrypoint.sh` reemplaza `config.json` según ENVIRONMENT

### Backend (FastAPI)

```bash
cd aod-fianzas-back
pip install uv
uv sync
uvicorn main:app --reload  # http://localhost:8000
```

El backend se configura mediante la variable `ENVIRONMENT` en el archivo `.env`:
- `local`: Local development (usa IGEAR de producción, no requiere VPN)
- `des`: Desarrollo remoto (idearagondes.aragon.es, requiere VPN)
- `pre`: Preproducción (preidearagon.aragon.es, requiere VPN)
- `pro`: Producción (idearagon.aragon.es)

### Stack Completo con Docker

```bash
# 1. Configurar entorno en .env
# Editar ENVIRONMENT=local|des|pre|pro

# 2. Desplegar
docker compose up --build

# 3. Verificar despliegue
./verify-deployment.sh

# 4. Parar servicios
docker compose down
```

## Despliegue en Producción

### Docker (Recomendado)

El proyecto usa un solo archivo `docker-compose.yaml` configurado mediante variables de entorno en `.env`:

```bash
# 1. Editar .env y configurar ENVIRONMENT
# ENVIRONMENT=pro   # o des, pre, local

# 2. Desplegar
docker compose up -d --build

# 3. Verificar
./verify-deployment.sh
```

**Características**:
- ✅ Una sola compilación del frontend funciona en todos los entornos
- ✅ Configuración automática de URLs IGEAR según entorno
- ✅ CORS configurado automáticamente por entorno
- ✅ Script de verificación incluido (`./verify-deployment.sh`)
- ✅ Configuración centralizada en `.env`

Ver **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** para documentación completa de despliegue.

### Frontend (Despliegue Manual)

El frontend se compila una sola vez y funciona en todos los entornos:

```bash
cd aod-fianzas
ng build --configuration production --base-href /servicios/alquileres/
```

La configuración se gestiona mediante archivos JSON en `dist/aod-fianzas/browser/assets/config/`:
- `config.json`: Configuración por defecto (localhost para ng serve)
- `config.des.json`: Desarrollo remoto (plantilla)
- `config.pre.json`: Preproducción (plantilla)
- `config.pro.json`: Producción (plantilla)

**En Docker**, el script `docker-entrypoint.sh` reemplaza automáticamente `config.json` según la variable `ENVIRONMENT`.

**Para despliegue manual**, copie el archivo de configuración correspondiente:
```bash
# Preproducción
cp config.pre.json config.json

# Producción
cp config.pro.json config.json
```

### Backend (Despliegue Manual)

El backend se configura mediante variables de entorno:

```bash
cd aod-fianzas-back

# Configurar entorno en .env
echo "ENVIRONMENT=production" > .env

# Iniciar servidor
uvicorn main:app --host 0.0.0.0 --port 8000
```

Variables de entorno importantes:
- `ENVIRONMENT`: Entorno (local/des/pre/pro)
- `REDIS_HOST`: Host de Redis para caché
- `REDIS_ENABLED`: Habilitar/deshabilitar caché (true/false)
- `LOG_LEVEL`: Nivel de logs (DEBUG/INFO/WARNING/ERROR)


## Configuración Multi-Entorno

El proyecto soporta cuatro entornos con configuración automática:

| Entorno | Frontend API | Backend IGEAR | CORS | VPN |
|---------|-------------|--------------|------|-----|
| **local** | http://localhost:4202 | idearagon.aragon.es | localhost:4200,4201,4202 | No |
| **des** | https://desopendata.aragon.es/servicios/alquileres-api | idearagondes.aragon.es | desopendata.aragon.es | Sí |
| **pre** | https://preopendata.aragon.es/servicios/alquileres-api | preidearagon.aragon.es | preopendata.aragon.es | Sí |
| **pro** | https://opendata.aragon.es/servicios/alquileres-api | idearagon.aragon.es | opendata.aragon.es | No |

### Servicios IGEAR Utilizados

![image](https://user-images.githubusercontent.com/92776591/165341928-19d6b64b-6dff-4a03-8cf4-f52d01797da2.png)

El backend se conecta a los siguientes servicios del IGEAR (el dominio cambia según entorno):
- **TypedSearchService**: Resolución de entidades geográficas
- **SpatialSearchService**: Consultas espaciales
- **SITA WMS**: Servicio de mapas web
- **Visor2D**: Datos de visualización 2D

## CORS en Desarrollo Local

El CORS se configura automáticamente según el entorno:
- **Desarrollo**: Permite localhost:4200, 4201, 4202
- **Preproducción/Producción**: Permite el dominio correspondiente

Para configuración personalizada, edite `CORS_ORIGINS_OVERRIDE` en `aod-fianzas-back/.env`.

Si necesita control adicional de CORS en el navegador:
- Firefox: [CORS Everywhere](https://addons.mozilla.org/en-US/firefox/addon/cors-everywhere/)

## Documentación Adicional

- **[CLAUDE.md](CLAUDE.md)**: Guía completa para desarrollo con Claude Code
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)**: Documentación exhaustiva de despliegue Docker
- **[aod-fianzas/RUNTIME_CONFIG.md](aod-fianzas/RUNTIME_CONFIG.md)**: Configuración en tiempo de ejecución del frontend
- **[aod-fianzas-back/ENVIRONMENT_CONFIG.md](aod-fianzas-back/ENVIRONMENT_CONFIG.md)**: Configuración de entornos del backend
- **[TASK1.md](TASK1.md)**: Tracking de implementación de configuración multi-entorno

## Estructura del Proyecto

```
alquileres/
├── aod-fianzas/              # Frontend Angular 19
│   ├── src/
│   │   ├── app/
│   │   ├── assets/config/    # Configuración en tiempo de ejecución
│   │   │   ├── config.json        # Local (default)
│   │   │   ├── config.des.json    # Desarrollo
│   │   │   ├── config.pre.json    # Preproducción
│   │   │   └── config.pro.json    # Producción
│   │   └── environments/     # Configuración de compilación
│   └── Dockerfile
├── aod-fianzas-back/         # Backend FastAPI
│   ├── services/             # Servicios de negocio
│   ├── config.py             # Configuración con Pydantic (4 entornos)
│   ├── main.py               # Punto de entrada de la API
│   ├── .env                  # Variables de entorno (local)
│   └── Dockerfile
├── docker-compose.yaml       # Configuración Docker (lee de .env)
├── .env                      # Variables de entorno Docker
└── verify-deployment.sh      # Script de verificación
```

## Licencia

Licencia Pública de la Unión Europea v1.2.

## Financiación

Financiado con el Fondo Europeo de Desarrollo Regional.

