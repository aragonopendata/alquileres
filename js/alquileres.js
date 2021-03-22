"use strict";

const URL_SITA =
  "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SITA_WMS";

// Popup
var container = document.getElementById("popup");
var content = document.getElementById("popup-content");
var closer = document.getElementById("popup-closer");

// Búsqueda
var searchField = document.getElementById("search");
var resultsHolder = document.getElementById("results");

var overlay = new ol.Overlay({
  element: container,
  autoPan: false,
  autoPanAnimation: {
    duration: 250,
  },
});

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
          obj[nodeName] = [];el.style.display = 'none';
          obj[nodeName].push(old);
        }
        obj[nodeName].push(xmlToJson(item));
      }
    }
  }
  return obj;
};

function getObjectIdByCP(cp) {
  return new Promise(function (resolve, reject) {
    var request = new XMLHttpRequest();

    const url = new URL(
      "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SimpleSearchService/typedSearchService"
    );
    url.searchParams.append("texto", cp);
    url.searchParams.append("type", "v111_codigo_postal");
    url.searchParams.append("app", "DV");

    request.open("GET", url, true);

    request.onload = function () {
      if (this.status >= 200 && this.status < 400) {
        let data = xmlToJson(this.responseXML);
        let response =
          data["SOAP-ENV:Envelope"]["SOAP-ENV:Body"].SearchResponse.SearchResult
            .List["#text"];
        resolve(response.split("#")[3]);
      } else {
        reject("error");
      }
    };

    request.onerror = function () {
      reject("error en la solicitud");
    };

    request.send();
  });
}

function getCQLFilter(objectId, capa, distancia) {
  return new Promise(function (resolve, reject) {
    var request = new XMLHttpRequest();

    const url = new URL(
      "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SpatialSearchService/services"
    );

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
        reject("error");
      }
    };

    request.onerror = function () {
      reject("error en la solicitud");
    };

    request.send();
  });
}

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
        reject("error");
      }
    };

    request.onerror = function () {
      reject("error en la solicitud");
    };

    const params = new URLSearchParams();
    params.set("service", "WFS");
    params.set("version", "1.0.0");
    params.set("request", "GetFeature");
    params.set("typename", capa);
    params.set("outputFormat", "application/json");
    params.set("srsname", wms_srs);
    params.set("CQL_FILTER", cqlFilter);

    request.send(params);
  });
}


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

let WMS_SRS = "EPSG:25830";
let map_projection = new ol.proj.Projection({
  code: WMS_SRS,
  units: "m",
});
let options = {
  projection: map_projection,
};
let map = new ol.Map({
  target: "map",
  view: new ol.View(options),
  overlays: [overlay],
});

let layerAragon = new ol.layer.Tile({
  source: new ol.source.TileWMS({
    url:
      "https://idearagon.aragon.es/arcgis/services/AragonReferencia/Basico_NEW/MapServer/WMSServer",
    params: {
      LAYERS: "0,2,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19",
      VERSION: "1.1.1",
    },
    projection: map_projection,
  }),
});
map.addLayer(layerAragon);

// Capa para las líneas de calles con datos
let mapVectorLayer = new ol.layer.Vector({});

function showSearchField(show) {
  search.disabled = !show;
  if(!show){
    search.classList.add("hidden")
    resultsHolder.classList.remove("hidden")
  } else {
    search.classList.remove("hidden")
    resultsHolder.classList.add("hidden")
    search.focus()
  }
}

function updateLoadingText(text) {
  resultsHolder.innerHTML = `
  <div type="button" class="inline-flex items-center px-4 py-2text-base leading-6 font-medium rounded-md" disabled="">
  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
  ${text}
</div>
`
}

function showSearchSucccess(codigoPostal) {
  resultsHolder.innerHTML = `<form class="flex items-center gap-5" onsubmit="event.preventDefault(); showSearchField(true)">
  <div class="flex flex-col">
    <span class="text-gray-700">Código postal</span>
    <span class="font-bold text-3xl">${codigoPostal}</span>
  </div>
  <div>
    <button type="submit" class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
      Buscar otro
    </button>
  </div>
</form>`
}

// Al enviar el formulario de búsqueda
function buscar() {
  var codigoPostal = searchField.value

  showSearchField(false)
  updateLoadingText(`<p>Localizando ${codigoPostal}...</p>`)

  getObjectIdByCP(codigoPostal).then(function (objectId) {
    getCQLFilter(objectId, "fianzas", 1000).then(function (cqlFilter) {
      updateLoadingText(`<p>Cargando datos de alquileres...</p>`)
      getWfsAsync(
        "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/Visor2D",
        "v111_codigo_postal",
        WMS_SRS,
        `objectid=${objectId}`
      ).then(function(cpWfs){
        let bbox = getBBox(cpWfs.features);
        map.getView().fit(bbox, map.getSize());
      });
      getWfsAsync(URL_SITA, "fianzas", WMS_SRS, cqlFilter).then(function (
        fianzasWfs
      ) {
        let geojsonFormat = new ol.format.GeoJSON();
        let features = geojsonFormat.readFeatures(JSON.stringify(fianzasWfs));
      
        let vector = new ol.layer.Vector({
          source: new ol.source.Vector({
            format: geojsonFormat,
            features: features,
          }),
          features: geojsonFormat.readFeatures(JSON.stringify(fianzasWfs)),
          style: function(feature, resolution) {
            return new ol.style.Style({
              stroke: new ol.style.Stroke({
                  color: '#68a4b4',
                  width: 3
              })
            })
          }
        });
        map.addLayer(vector);
        showSearchSucccess(codigoPostal)
      });
    });
  });
}

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

  var formatter = new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  });

  var coordinate = evt.coordinate;
  var hdms = ol.coordinate.toStringHDMS(ol.proj.toLonLat(coordinate));

  // TODO: sacar a su propia función, es muy largo aquí.
  var contenidoPopup = `
<span class="font-bold text-lg leading-none">${info.via_loc}</span>
<div class="pt-2 flex gap-5">
`;

  var hayDatos = false; // si ni viviendas ni locales tienen media > 0, mostrar solo un mensajito que ponga que no hay datos recientes

  // Av. Pirineos
  if (info.vivienda_media > 5) {
    hayDatos = true;
    contenidoPopup += `
  <div>
    <p class="flex items-center gap-1 text-gray-800">
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
    if (info.vivienda_min > 0) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.vivienda_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>`;
    }

    // Solo mostrar máximo si hay valor
    if (info.vivienda_max > 0) {
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

  if (info.local_media > 5) {
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
    if (info.local_min > 0) {
      contenidoPopup += `
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.local_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>`;
    }

    // Solo mostrar máximo si hay valor
    if (info.local_max > 0) {
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

map.on("pointermove", (evt) => {
  var pixel = map.getEventPixel(evt.originalEvent);
  map.forEachFeatureAtPixel(pixel, function (feature, resolution) {
    evt.element = feature;
    onFeatureSelectFuncion(evt);
  });
});

map.on("click", (evt) => {
  var pixel = map.getEventPixel(evt.originalEvent);
  map.forEachFeatureAtPixel(pixel, function (feature, resolution) {
    evt.element = feature;
    onFeatureSelectFuncion(evt);
  });
});

// Por defecto, cargar Aragón
var bbox_aragon = [571580, 4412223, 812351, 4756639];
map.getView().fit(bbox_aragon, map.getSize());

window.onresize = function()
{
  setTimeout( function() { map.updateSize();}, 200);
}
map.updateSize();
