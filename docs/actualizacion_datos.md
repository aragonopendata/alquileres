# Actualización de datos de alquileres en Aragón

## Descripción general
Este documento describe el proceso de actualización anual de los datos de alquileres de Aragón. El proceso implica la creación y transformación de varias tablas para optimizar el rendimiento de la aplicación.

## Requisitos previos
Para ejecutar este proceso necesitamos acceso a las siguientes fuentes de datos:
- `fianzapos`: Tabla histórica ubicada en la base de datos idearagon
- `callejero`: Recurso 163 de GAODCORE
- `fianzapos_2024`: Datos actualizados del recurso 100 de GAODCORE

## Proceso de actualización

### 1. Preparación del entorno
- Todas las tablas se crean en el esquema `opendata_usr`
- Se recomienda realizar el proceso en una base de datos local antes de exportar a producción
- Durante el proceso se crean tablas intermedias que no se utilizarán en producción

### 2. Creación de tablas intermedias
El proceso se divide en tres pasos principales, ejecutados en orden:

1. **fianzapos_app**: Tabla inicial que extrae los campos relevantes de `fianzapos_2024`
   - Contiene información básica de las fianzas
   - Incluye campos como año, provincia, calle, municipio y valores económicos

2. **fianzapos_data_app**: Tabla que relaciona los datos nuevos con la tabla histórica
   - Realiza un join con la tabla `fianzapos` original
   - Normaliza los nombres de calles y municipios
   - Añade el campo `c_mun_via` para la relación con el callejero

3. **fianzas_all_app**: Tabla que agrupa y calcula estadísticas
   - Calcula valores mínimos, máximos y medios de rentas
   - Clasifica los registros por tipo (vivienda/local)
   - Cuenta el número de fianzas por grupo

### 3. Creación de la tabla final
La tabla final `fianzas_app` se crea mediante:
- Join con el callejero para obtener información geográfica
- Filtrado de años (2000-2024)
- Creación de índice para optimizar búsquedas por municipio

## Exportación a producción
La tabla `fianzas_app` es la única que debe exportarse a la base de datos de producción, ya que es la que utiliza la aplicación para mostrar los datos.

