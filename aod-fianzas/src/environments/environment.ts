// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  epsgCode: 'EPSG:25830',
  aragonBoundingBox: [[571580, 4412223], [812351, 4756639]],
  wmsVersion: '1.1.1',
  wmsLayers: '0,2,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19',
  urlWMSServer: 'https://idearagon.aragon.es/arcgis/services/AragonReferencia/Basico_NEW/MapServer/WMSServer',
  urlSitaWMS: 'https://idearagon.aragon.es/SITA_WMS',
  urlVisor2D: 'https://idearagon.aragon.es/Visor2D',
  urlTypedSearchService: 'https://idearagon.aragon.es/SimpleSearchService/typedSearchService',
  urlSpatialSearchService: 'https://idearagon.aragon.es/SpatialSearchService/services',
  typedSearchCP: 'v111_codigo_postal',
  typedSearchDIRECCION: 'TroidesV',
  typedSearchLOCALIDAD: 'Localidad',
  typenameCP: 'carto.v111_codigo_postal',
  typenameDIRECCION: 'carto.t111_troidesvisor',
  typenameLOCALIDAD: '',
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.
