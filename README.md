# Alquileres de Aragón

Aplicación web que muestra un mapa los precios medios de los alquileres de un
código postal de Aragón.

La fuente principal de los datos es el IGEAR y sus servicios de mapas web.

## Despliegue

### Frontend

Es una web estática sin mayor complicación.

- No hay que ejecutar ningún archivo. 
- Se despliega la carpeta entera.
- No hay secretos ni variables de configuración.

(por ahora)

### Backend

> Está por ver qué servicio de búsqueda de códigos postales se acaba usando. Por
> ahora lo dejo sin documentar.

## Pendiente

Mejoras:

- Añadir comparación con datos de otros años (1,5d)
- Búsqueda por nombre de calle (2-3d)
- Poder cerrar el popup (0,25d)
- Navegar por el mapa, sin necesidad de introducir cp o calle, y al hacer clic,
  que se vean los datos de la zona. (?d)

Para la integración del nuevo portal de Aragón:

- Permitir embed con iframe
- Parámetros URL
    - Quitar cuadro de búsqueda/footer
    - Código postal por defecto

Otras tareas:

- PWA
- Separar JS y CSS a archivos propios
- Importar librerías con un gestor de dependencias (Tailwind, OpenLayers)
- Google Analytics
    - Mensaje de cookies
    - Página de cookies
- Footer con enlaces
    - Logo FEDER?
- Backend/bypass para obtención datos y búsqueda por CP
- Documentación, comentar más

## Licencia

Licencia Pública de la Unión Europea v1.2.

## Financiación

Financiado con el Fondo Europeo de Desarrollo Regional.
