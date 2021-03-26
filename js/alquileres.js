"use strict";

// TODO: hacer que el CORS sea configurable en runtime con una alerta si detecta
// que pudiera estar fallando la petición por eso. 

// TODO: el archivo es muy largo. No vendría mal separarlo por temática.

// -------------
//
// Configuración
//
// -------------

// --
// Servicios externos
// --

// TODO hacer configurable en runtime. 

const APP_DEBUG = true
const APP_USE_DEV_SERVERS = false

// Para obtener los datos de las fianzas
var URL_SITA = "https://idearagon.aragon.es/SITA_WMS";

// Para obtener el object id de un código postal
var URL_SERVICIO_CP = "https://idearagon.aragon.es/SimpleSearchService/typedSearchService";

// Para obtener las features dentro de un código postal (object id)
var URL_SERVICIO_BUSQUEDA_ESPACIAL = "https://idearagon.aragon.es/SpatialSearchService/services";

var URL_SERVICIO_ALQUILERES ="https://idearagon.aragon.es/Visor2D";

// Configuración de la fuente de imágenes de fondo
const MAPA_WMS_URL =
  "https://idearagon.aragon.es/arcgis/services/AragonReferencia/Basico_NEW/MapServer/WMSServer";
const MAPA_WMS_LAYERS = "0,2,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19";
const MAPA_WMS_VERSION = "1.1.1";

if (APP_USE_DEV_SERVERS) {
  URL_SERVICIO_ALQUILERES = "https://idearagondes.aragon.es/Visor2D";
  URL_SERVICIO_BUSQUEDA_ESPACIAL = "https://idearagondes.aragon.es/SpatialSearchService/services";
  URL_SITA = "https://idearagondes.aragon.es/SITA_WMS";
  URL_SERVICIO_CP = "https://idearagondes.aragon.es/SimpleSearchService/typedSearchService";
}

// Tiempo que esperar antes de dar por perdida una petición
const DEFAULT_REQUEST_TIMEOUT = 10000;

// --
// Textos
// --

const TEXT_ERROR_GENERIC =
  "Ha ocurrido un error inesperado. Inténtalo de nuevo más tarde."; // Mensaje a mostrar a los usuarios cuando pasa algo raro, falla una petición, etc. TODO mejorar
  
// --
// Otros
// --

// Valor mínimo a partir del que mostrar datos.
// En algunos sitios mostraría alquileres de 3 €, por eso se ha puesto mínimo 5.
const POPUP_VALUE_TO_SHOW = 5;

// -------------

// Caché de resultados:
//
// Si lo ususarios buscan un CP que ya hemos obtenido en la misma sesión,
// mandarles a la ubicación sin hacer ninguna petición.
// la clave es el número del código postal, en formato string
// el valor es el bounding box obtenido del código postal
//
// Fuente: https://slynova.io/create-a-simple-cache-system/
const cache = new Map();

// --
// Tooltip/popup alquileres
// --

// Elementos
var container = document.getElementById("popup");
var content = document.getElementById("popup-content");

// Esta overlay es la que se usa para mostrar el tooltip al pasar el ratón sobre
// una calle con datos de alquileres.
var overlay = new ol.Overlay({
  element: container,
  autoPan: false,
  autoPanAnimation: {
    duration: 250,
  },
});

// Búsqueda
var searchField = document.getElementById("search");
var resultsHolder = document.getElementById("results");
var searchLabel = document.getElementById("search-label");

// Convierte XML (imperfecto, con algunas cosillas mal) a JSON
// porque los conversores que vienen con JS son muy tiquismiquis.
let xmlToJson = (xml) => {
  let obj = {};
  if (xml.nodeType == 1) {
    if (xml.attributes.length > 0) {
      obj["@attributes"] = {};
      for (let j = 0; j < xml.attributes.length; j++) {
        let attribute = xml.attributes.item(j);
        obj["@attributes"][attribute.nodeName] = attribute.nodeValue;
      }
    }
  } else if (xml.nodeType == 3) {
    obj = xml.nodeValue;
  }
  if (xml.hasChildNodes()) {
    for (let i = 0; i < xml.childNodes.length; i++) {
      let item = xml.childNodes.item(i);
      let nodeName = item.nodeName;
      if (typeof obj[nodeName] == "undefined") {
        obj[nodeName] = xmlToJson(item);
      } else {
        if (typeof obj[nodeName].push == "undefined") {
          let old = obj[nodeName];
          obj[nodeName] = [];
          el.style.display = "none";
          obj[nodeName].push(old);
        }
        obj[nodeName].push(xmlToJson(item));
      }
    }
  }
  return obj;
};

// TODO documentar
function getObjectIdByCP(cp) {
  return new Promise(function (resolve, reject) {
    let request = new XMLHttpRequest();

    const url = new URL(URL_SERVICIO_CP);
    url.searchParams.append("texto", cp);
    url.searchParams.append("type", "v111_codigo_postal");
    url.searchParams.append("app", "DV");

    request.open("GET", url, true);

    request.onload = function () {
      if (this.status >= 200 && this.status < 400) {
        let data = xmlToJson(this.responseXML);

        let searchResult =
          data["SOAP-ENV:Envelope"]["SOAP-ENV:Body"].SearchResponse
            .SearchResult;

        // Si no hay resultados para el CP, abortamos
        let count = searchResult.Count["#text"];
        if (count < 1) {
          reject("No hay datos para el código postal.");
        }

        let response = searchResult.List["#text"];
        try {
          resolve(response.split("#")[3]);
        } catch (err) {
          reject("Ha ocurrido un error al buscar.");
        }
      } else {
        reject("El servicio no está disponible en estos momentos.");
      }
    };

    request.onerror = function () {
      reject("No se ha podido conectar con el servicio.");
    };

    request.timeout = DEFAULT_REQUEST_TIMEOUT;
    request.send();
  });
}

// TODO documentar
function getCQLFilter(objectId, capa, distancia) {
  return new Promise(function (resolve, reject) {
    var request = new XMLHttpRequest();

    const url = new URL(URL_SERVICIO_BUSQUEDA_ESPACIAL);

    url.searchParams.append("SERVICE", "DV");
    url.searchParams.append("TYPENAME", "carto.v111_codigo_postal");
    url.searchParams.append("CQL_FILTER", `OBJECTID=${objectId}`);
    url.searchParams.append("PROPERTYNAME", "OBJECTID");
    url.searchParams.append("TYPENAME_CONN", "DV");

    request.open("POST", url, true);
    request.setRequestHeader(
      "Content-Type",
      "application/x-www-form-urlencoded; charset=UTF-8"
    );

    let cqlFilter = `objectid=${objectId}`;

    request.onload = function () {
      if (this.status >= 200 && this.status < 400) {
        let data = JSON.parse(this.response);
        for (let resultado of data.resultados) {
          if (
            resultado.distancia === distancia &&
            resultado.capa.includes(capa)
          ) {
            for (let feature of resultado.featureCollection.features) {
              // cqlFilter += cqlFilter !== '' ? ' OR ' : '';
              cqlFilter += ` OR objectid=${feature.properties.objectid}`;
            }
            break;
          }
        }
        resolve(cqlFilter);
      } else {
        reject(TEXT_ERROR_GENERIC); // TODO mejorar error
      }
    };

    request.onerror = function () {
      reject(TEXT_ERROR_GENERIC); // TODO mejorar error
    };

    request.timeout = DEFAULT_REQUEST_TIMEOUT;
    request.send();
  });
}

// TODO documentar
function getWfsAsync(endpoint, capa, wms_srs, cqlFilter) {
  return new Promise(function (resolve, reject) {
    var request = new XMLHttpRequest();

    const url = new URL(endpoint);

    request.open("POST", url, true);
    request.setRequestHeader(
      "Content-Type",
      "application/x-www-form-urlencoded; charset=UTF-8"
    );

    request.onload = function () {
      if (this.status >= 200 && this.status < 400) {
        resolve(JSON.parse(this.response));
      } else {
        reject(TEXT_ERROR_GENERIC); // TODO mejorar error
      }
    };

    request.onerror = function () {
      reject(TEXT_ERROR_GENERIC); // TODO mejorar error
    };

    const params = new URLSearchParams();
    params.set("service", "WFS");
    params.set("version", "1.0.0");
    params.set("request", "GetFeature");
    params.set("typename", capa);
    params.set("outputFormat", "application/json");
    params.set("srsname", wms_srs);
    params.set("CQL_FILTER", cqlFilter);

    request.timeout = DEFAULT_REQUEST_TIMEOUT;
    request.send(params);
  });
}

// Obtener la bounding box de un array de features.
// El resultado se le puede pasar a map.fit() para centrar el mapa en su
// ubicación aproximada.
let getBBox = (features) => {
  let bbox = [Infinity, Infinity, -Infinity, -Infinity];
  for (let feature of features) {
    if (feature.geometry.type == "Polygon") {
      for (let row of feature.geometry.coordinates) {
        for (let coordinate of row) {
          bbox[0] = coordinate[0] < bbox[0] ? coordinate[0] | 0 : bbox[0];
          bbox[2] = coordinate[0] > bbox[2] ? coordinate[0] | 0 : bbox[2];
          bbox[1] = coordinate[1] < bbox[1] ? coordinate[1] | 0 : bbox[1];
          bbox[3] = coordinate[1] > bbox[3] ? coordinate[1] | 0 : bbox[3];
        }
      }
    }
  }
  return bbox;
};

// Ajustes para el mapa
let WMS_SRS = "EPSG:25830"; // Esto tiene que ir así.
let map_projection = new ol.proj.Projection({
  code: WMS_SRS,
  units: "m",
});
let options = {
  projection: map_projection,
};

// Definición del mapa de OpenLayers como tal
var map = new ol.Map({
  target: "map",
  view: new ol.View(options),
  overlays: [overlay],
});

// La capa donde se ve el nombre de las calles, municipio, etc.
let layerAragon = new ol.layer.Tile({
  source: new ol.source.TileWMS({
    url: MAPA_WMS_URL,
    params: {
      LAYERS: MAPA_WMS_LAYERS,
      VERSION: MAPA_WMS_VERSION,
    },
    projection: map_projection,
  }),
});
map.addLayer(layerAragon);

// Capa para las líneas de calles con datos
let mapVectorLayer = new ol.layer.Vector({});

// Ocultar o mostrar el buscador.
// Cuando se oculta, se muestra el contenedor de los resultados.
function showSearchField(show) {
  search.disabled = !show;
  if (!show) {
    searchField.classList.add("hidden");
    searchLabel.classList.add("hidden");
    resultsHolder.classList.remove("hidden");
  } else {
    searchField.classList.remove("hidden");
    searchLabel.classList.remove("hidden");
    resultsHolder.classList.add("hidden");
    search.focus();
  }
}

// Muestra un spinner que gira y un texto a su izquierda.
function updateLoadingText(text) {
  resultsHolder.innerHTML = `
  <div type="button" class="inline-flex items-center px-4 py-2 text-base leading-6 font-medium rounded-md" disabled="">
  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
  ${text}
</div>
`;
}

// Muestra el código postal en grande y un botón para volver al buscador.
// Usa el mismo contenedor que updateLoadingText, por lo que no puede aparecer
// al mismo tiempo.
function showSearchSucccess(codigoPostal) {
  resultsHolder.innerHTML = `<form class="flex items-center gap-5 pl-2 lg:pl-0" onsubmit="event.preventDefault(); showSearchField(true)">
  <div class="flex flex-col">
    <span class="text-gray-700 tracking-tight">Código postal</span>
    <span class="font-bold text-3xl font-tabular-lining">${codigoPostal}</span>
  </div>
  <div>
    <button type="submit" class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
      Buscar otro
    </button>
  </div>
</form>`;
}

// Para mostrar el cuadro de búsqueda con un texto en rojo y un iconito. Cuando
// algo ha salido mal o no se pasa la validación.
function showSearchError(message) {
  if (message == null) {
    message = "Ha ocurrido un error";
  }
  searchLabel.innerHTML = `
  <div class="mb-1 flex items-center gap-1 font-semibold tracking-tight text-red-500">
  <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
  </svg>
  <span>${message}</span>
</div>
  `;
  showSearchField(true);
}

// Quitar la capa que sale por encima del mapa al cargar para evitar que los
// usuarios se pongan a explorar por él si tener datos. Evita confusión. Creo.
function removeWelcomeOverlay() {
  let mapBlockingOverlay = document.getElementById("map-overlay");
  mapBlockingOverlay.classList.add("hidden");
  let mapElement = document.getElementById("map");
  mapElement.classList.remove("opacity-10");
}

// Al enviar el formulario de búsqueda
// TODO documentar
function buscar() {
  // Limpiar el CP que hemos recibido
  let codigoPostal = searchField.value;
  codigoPostal = codigoPostal.replace(/\s+/g, ""); // Quitar espacios
  codigoPostal = codigoPostal.replace(".", ""); // Quitar puntos
  codigoPostal = codigoPostal.replace("-", ""); // Quitar guiones
  codigoPostal = codigoPostal.replace(",", ""); // Quitar comas?

  searchField.value = codigoPostal; // Guardamos el código de vuelta para que el usuario lo vea limpio

  if (codigoPostal == "") {
    showSearchError("Introduce un código postal de Aragón.");
    return;
  }

  // https://es.stackoverflow.com/a/110737, por Mariano
  if (!/^(?:0?[1-9]|[1-4]\d|5[0-2])\d{3}$/.test(codigoPostal)) {
    showSearchField(false);
    updateLoadingText(`<p>Comprobando código postal...</p>`);
    setTimeout(function () {
      showSearchError("Introduce un código postal de Aragón");
    }, 500); // Para dar tiempo a reaccionar al usuario si ha hecho cambios.
    return;
  }

  searchLabel.innerHTML = "Buscar por código postal"; // Reseteamos el mensaje de error si lo hubiera, para que la próxima vez que se muestre el cuadro de búsqueda, el label sea normal. TODO mover a showSearch?

  removeWelcomeOverlay(); // quitar la capa por encima con el mensajito de inicio

  // Ocultar la búsqueda y desactivarla para evitar doble envío
  showSearchField(false);
  updateLoadingText(`<p>Localizando el ${codigoPostal}...</p>`);

  // Comprobar si ya habíamos obtenido los datos del CP en caso afirmativo, no
  // hacemos ninguna petición y movemos inmediatamente el mapa a la ubicación
  if (cache.has(codigoPostal)) {
    map.getView().fit(cache.get(codigoPostal), map.getSize());
    showSearchSucccess(codigoPostal);
    return;
  }

  // Esta cadena de promesas es donde se hace prácticamente todo lo relacionado
  // con la búsqueda del código postal. Se ejecuta de forma asíncrona, pero para
  // evitar saltos raros y spam inintencionado, solo se puede buscar un CP a la vez.
  //
  // Esto es más o menos lo que hacemos ahora:
  //
  // 1. Solicitar el objectId en el mapa del código postal
  // 2. Solicitar los objectid de las calles dentro del CP y generar un filtro ,
  // 3. Solicitar el GeoJSON del objectId del código postal
  //     - Obtener el bounding box en base al GeoJSON
  //     - Mover el mapa al sitio
  // 4. Solicitar los datos para las calles aplicando el filtro
  //     - Pintar las líneas vectoriales
  //
  getObjectIdByCP(codigoPostal)
    .then(function (objectId) {
      getCQLFilter(objectId, "fianzas", 1000)
        .then(function (cqlFilter) {
          updateLoadingText(`<p>Cargando datos de alquileres...</p>`);
          getWfsAsync(
            URL_SERVICIO_ALQUILERES,
            "v111_codigo_postal",
            WMS_SRS,
            `objectid=${objectId}`
          )
            .then(function (cpWfs) {
              let bbox = getBBox(cpWfs.features);
              cache.set(codigoPostal, bbox);
              map.getView().fit(bbox, map.getSize());
            })
            .catch(function (error) {
              showSearchError("Introduce un código postal de Aragón");
            });
          getWfsAsync(URL_SITA, "fianzas", WMS_SRS, cqlFilter)
            .then(function (fianzasWfs) {
              let geojsonFormat = new ol.format.GeoJSON();
              let features = geojsonFormat.readFeatures(
                JSON.stringify(fianzasWfs)
              );

              let vector = new ol.layer.Vector({
                source: new ol.source.Vector({
                  format: geojsonFormat,
                  features: features,
                }),
                features: geojsonFormat.readFeatures(
                  JSON.stringify(fianzasWfs)
                ),
                style: function (feature, resolution) {
                  return new ol.style.Style({
                    stroke: new ol.style.Stroke({
                      color: "#68a4b4",
                      width: 3,
                    }),
                  });
                },
              });
              map.addLayer(vector);
              showSearchSucccess(codigoPostal);
            })
            .catch(function (error) {
              showSearchError("Introduce un código postal de Aragón");
            });
        })
        .catch(function (error) {
          showSearchError("No se pueden mostrar los datos en este momento");
        });
    })
    .catch(function (error) {
      showSearchError(error);
    });
}

// TODO documentar
let onFeatureSelectFuncion = (evt) => {
  let feature = evt.element;
  let info = {
    via_loc: feature.get("via_loc"),
    anyo: 0,
    vivienda_min: 0,
    vivienda_max: 0,
    vivienda_media: 0,
    local_min: 0,
    local_max: 0,
    local_media: 0,
  };
  for (let valor of JSON.parse(feature.get("valores"))) {
    if (valor.anyo >= info.anyo && valor.tipo === 1) {
      info.anyo = valor.anyo;
      info.vivienda_min = valor.min;
      info.vivienda_max = valor.max;
      info.vivienda_media = valor.media;
    } else if (valor.anyo >= info.anyo && valor.tipo === 2) {
      info.anyo = valor.anyo;
      info.local_min = valor.min;
      info.local_max = valor.max;
      info.local_media = valor.media;
    }
  }

  // TODO documentar
  let formatter = new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  });

  let coordinate = evt.coordinate;
  let hdms = ol.coordinate.toStringHDMS(ol.proj.toLonLat(coordinate));

  // TODO: sacar a su propia función, es muy largo aquí.
  let contenidoPopup = `
<span class="font-bold text-lg leading-none">${info.via_loc}</span>
<div class="pt-2 flex gap-5">
`;

  let hayDatos = false; // si ni viviendas ni locales tienen media > 0, mostrar solo un mensajito que ponga que no hay datos recientes

  // TODO documentar
  if (info.vivienda_media > POPUP_VALUE_TO_SHOW) {
    hayDatos = true;
    contenidoPopup += `
  <div>
    <p class="flex items-center gap-1 text-gray-800 font-tabular-lining">
      <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
      Viviendas
      </p>
    <div>
      <span class="font-bold text-2xl">${formatter.format(
        info.vivienda_media
      )}</span>
      <span class="text-gray-600 tracking-tighter">media</span>
    </div>
    <div class="pt-2 flex-col gap-3">`;

    // Solo mostrar mínimo si hay valor
    if (info.vivienda_min > POPUP_VALUE_TO_SHOW) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.vivienda_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>`;
    }

    // Solo mostrar máximo si hay valor
    if (info.vivienda_max > POPUP_VALUE_TO_SHOW) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.vivienda_max
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">máx.</span>
      </div>`;
    }

    contenidoPopup += `
    </div>
  </div>`;
  }

  if (info.local_media > POPUP_VALUE_TO_SHOW) {
    hayDatos = true;
    contenidoPopup += `
  <div>
    <p class="flex items-center gap-1 text-gray-800">
      <svg class="w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
      Locales
      </p>
    <div>
      <span class="font-bold text-2xl">${formatter.format(
        info.local_media
      )}</span>
      <span class="text-gray-600 tracking-tighter">media</span>
    </div>
    <div class="pt-2 flex-col gap-3">`;

    // Solo mostrar mínimo si hay valor
    if (info.local_min > POPUP_VALUE_TO_SHOW) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.local_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>`;
    }

    // Solo mostrar máximo si hay valor
    if (info.local_max > POPUP_VALUE_TO_SHOW) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.local_max
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">máx.</span>
      </div>`;
    }

    contenidoPopup += `
    </div>
  </div>`;
  }

  // Parte de abajo de la tarjetita
  if (hayDatos) {
    contenidoPopup += `
  </div>
  <p class="pt-3 text-sm text-gray-600">Datos de 2019</p>`;
  } else {
    contenidoPopup += `
  </div>
  <p class="pt-3 text-sm text-gray-600">No hay datos recientes</p>`;
  }

  content.innerHTML = contenidoPopup;
  overlay.setPosition(coordinate);
};

// TODO documentar
map.on("pointermove", (evt) => {
  let pixel = map.getEventPixel(evt.originalEvent);
  map.forEachFeatureAtPixel(pixel, function (feature, resolution) {
    evt.element = feature;
    onFeatureSelectFuncion(evt);
  });
});

// TODO documentar
map.on("click", (evt) => {
  let pixel = map.getEventPixel(evt.originalEvent);
  map.forEachFeatureAtPixel(pixel, function (feature, resolution) {
    evt.element = feature;
    onFeatureSelectFuncion(evt);
  });
});

// Por defecto, cargar Aragón
let bbox_aragon = [571580, 4412223, 812351, 4756639];
map.getView().fit(bbox_aragon, map.getSize());

// TODO documentar
window.onresize = function () {
  setTimeout(function () {
    map.updateSize();
  }, 200);
};
map.updateSize();
