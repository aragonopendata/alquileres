"use strict";

// Popup
var container = document.getElementById("popup");
var content = document.getElementById("popup-content");
var closer = document.getElementById("popup-closer");

var overlay = new ol.Overlay({
  element: container,
  autoPan: true,
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
          obj[nodeName] = [];
          obj[nodeName].push(old);
        }
        obj[nodeName].push(xmlToJson(item));
      }
    }
  }
  return obj;
};

let getObjectID = (cp) => {
  let objectID = null;
  const url = new URL(
    "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SimpleSearchService/typedSearchService"
  );
  const params = new URLSearchParams();
  params.set("texto", cp);
  params.set("type", "v111_codigo_postal");
  params.set("app", "DV");
  url.search = params.toString();
  let xhr = new XMLHttpRequest();
  xhr.open("GET", url.toString(), false);
  xhr.send();
  if (xhr.status == 200) {
    let data = xmlToJson(xhr.responseXML);
    console.log(data);
    let response =
      data["SOAP-ENV:Envelope"]["SOAP-ENV:Body"].SearchResponse.SearchResult
        .List["#text"];
    objectID = response.split("#")[3];
  }
  return objectID;
};

let getCQLFilter = (objectID, capa, distancia) => {
  let cqlFilter = `objectid=${objectID}`;
  const url = new URL(
    "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SpatialSearchService/services"
  );
  const params = new URLSearchParams();
  params.set("SERVICE", "DV");
  params.set("TYPENAME", "carto.v111_codigo_postal");
  params.set("CQL_FILTER", `OBJECTID=${objectID}`);
  params.set("PROPERTYNAME", "OBJECTID");
  params.set("TYPENAME_CONN", "DV");
  let xhr = new XMLHttpRequest();
  xhr.open("POST", url.toString(), false);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send(params.toString());
  if (xhr.status == 200) {
    let data = JSON.parse(xhr.responseText);
    console.log(data);
    for (let resultado of data.resultados) {
      if (resultado.distancia === distancia && resultado.capa.includes(capa)) {
        for (let feature of resultado.featureCollection.features) {
          // cqlFilter += cqlFilter !== '' ? ' OR ' : '';
          cqlFilter += ` OR objectid=${feature.properties.objectid}`;
        }
        break;
      }
    }
  }
  return cqlFilter;
};

let getWFS = (endpoint, capa, wms_srs, cqlFilter) => {
  let data = null;
  const url = new URL(endpoint);
  const params = new URLSearchParams();
  params.set("service", "WFS");
  params.set("version", "1.0.0");
  params.set("request", "GetFeature");
  params.set("typename", capa);
  params.set("outputFormat", "application/json");
  params.set("srsname", wms_srs);
  params.set("CQL_FILTER", cqlFilter);
  let xhr = new XMLHttpRequest();
  xhr.open("POST", url.toString(), false);
  xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhr.send(params.toString());
  if (xhr.status == 200) {
    data = JSON.parse(xhr.responseText);
    console.log(data);
  }
  return data;
};

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

let layerFianzas = new ol.layer.Tile({
  source: new ol.source.TileWMS({
    url: "https://idearagon.aragon.es/SITA_WMS",
    params: {
      LAYERS: "fianzas",
      VERSION: "1.0.0",
    },
    projection: map_projection,
  }),
});
// map.addLayer(layerFianzas);

let objectID = getObjectID("50001");
let cqlFilter = getCQLFilter(objectID, "fianzas", 1000);
let fianzasWfs = getWFS(
  "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/SITA_WMS",
  "fianzas",
  WMS_SRS,
  cqlFilter
);
let cpWfs = getWFS(
  "https://cors-anywhere.herokuapp.com/https://idearagon.aragon.es/Visor2D",
  "v111_codigo_postal",
  WMS_SRS,
  `objectid=${objectID}`
);
let bbox = getBBox(cpWfs.features);

let geojsonFormat = new ol.format.GeoJSON();
let features = geojsonFormat.readFeatures(JSON.stringify(fianzasWfs));

let vector = new ol.layer.Vector({
  source: new ol.source.Vector({
    format: geojsonFormat,
    features: features,
  }),
  features: geojsonFormat.readFeatures(JSON.stringify(fianzasWfs)),
});

map.addLayer(vector);

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
  var contenidoPopup = `
<span class="font-bold text-lg leading-none">${info.via_loc}</span>
<div class="pt-2 flex gap-5">
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
    <div class="pt-2 flex-col gap-3">
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.vivienda_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.vivienda_max
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">máx.</span>
      </div>
    </div>
  </div>
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
    <div class="pt-2 flex-col gap-3">
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.local_min
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">mín.</span>
      </div>
      <div>
        <span class="font-semibold text-lg">${formatter.format(
          info.local_max
        )}</span>
        <span class="text-gray-600 text-sm tracking-tighter">máx.</span>
      </div>
    </div>
  </div>
</div>
<p class="pt-3 text-sm text-gray-600">Datos de 2019</p>`;

  content.innerHTML = contenidoPopup;
  overlay.setPosition(coordinate);

  console.log(info);
};

map.on("pointermove", (evt) => {
  var pixel = map.getEventPixel(evt.originalEvent);
  map.forEachFeatureAtPixel(pixel, function (feature, resolution) {
    evt.element = feature;
    onFeatureSelectFuncion(evt);
  });
});

map.getView().fit(bbox, map.getSize());
