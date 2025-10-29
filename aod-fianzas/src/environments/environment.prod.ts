// RUNTIME CONFIGURATION OVERRIDE:
// The following properties are overridden at runtime by ConfigService loading from /assets/config/config.json:
// - urlApi, backendUrl: Loaded from config.apiUrl
// - urlTypedSearchService: Loaded from config.igearServices.typedSearchUrl
// - urlSpatialSearchService: Loaded from config.igearServices.spatialSearchUrl
// - urlSitaWMS: Loaded from config.igearServices.sitaWmsUrl
// - urlVisor2D: Loaded from config.igearServices.visor2dUrl
//
// Services using these URLs should inject ConfigService instead of using environment directly.
// This allows a single build to work across dev/pre/prod environments.

export const environment = {
  production: true,
  epsgCode: 'EPSG:25830',
  aragonBoundingBox: [[571580, 4412223], [812351, 4756639]],
  wmsVersion: '1.1.1',
  wmsLayers: '0,2,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19',
  urlWMSServer: 'https://idearagon.aragon.es/arcgis/services/AragonReferencia/Basico_NEW/MapServer/WMSServer',

  // RUNTIME OVERRIDDEN - See ConfigService for actual values
  urlSitaWMS: 'https://idearagon.aragon.es/SITA_WMS',
  urlVisor2D: 'https://idearagon.aragon.es/Visor2D',
  urlTypedSearchService: 'https://idearagon.aragon.es/SimpleSearchService/typedSearchService',
  urlSpatialSearchService: 'https://idearagon.aragon.es/SpatialSearchService/services',
  urlApi: 'https://opendata.aragon.es/servicios/alquileres-api',
  backendUrl: 'https://opendata.aragon.es/servicios/alquileres-api',

  typedSearchCP: 'v111_codigo_postal',
  typedSearchDIRECCION: 'TroidesV',
  typedSearchLOCALIDAD: 'Localidad',
  typenameCP: 'carto.v111_codigo_postal',
  typenameDIRECCION: 'carto.t111_troidesvisor',
  typenameLOCALIDAD: 'carto.t112_nucleos',
};
