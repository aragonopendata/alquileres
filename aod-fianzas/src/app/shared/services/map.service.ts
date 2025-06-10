import { Injectable } from '@angular/core';
import { Map, Overlay, View } from 'ol';
import { TileWMS } from 'ol/source';
import VectorSource from 'ol/source/Vector';
import { boundingExtent } from 'ol/extent';
import Projection from 'ol/proj/Projection';
import TileLayer from 'ol/layer/Tile';
import { GeoJSON } from 'ol/format';
import VectorLayer from 'ol/layer/Vector';
import { environment } from 'src/environments/environment';
import { IgearService } from './igear.service';
import { TipoBusqueda } from '../models/tipo-busqueda.enum';
import { ObjectId } from '../models/object-id.model';
import { Observable, of } from 'rxjs';
import { Coordinate } from 'ol/coordinate';
import { map, mergeMap, switchMap } from 'rxjs/operators';
import { Style, Stroke } from 'ol/style';
import { WFSResponse } from '../models/wfs-response.model';

@Injectable({
  providedIn: 'root'
})
export class MapService {

  constructor(private igearService: IgearService) { }

  /**
   *
   * @ngdoc method
   * @name MapService.initMap
   * @description Inicia el mapa de Aragón
   * @param {string=} target
   * @returns {Map=}
   */
  initMap(target: string, overlay: Overlay): Map {
    const extent = boundingExtent(environment.aragonBoundingBox);
    const projection = new Projection({
      code: environment.epsgCode,
      units: 'm'
    });
    const options = {
      projection: projection,
    };
    const layer = new TileLayer({
      source: new TileWMS({
        url: environment.urlWMSServer,
        params: {
          LAYERS: environment.wmsLayers,
          VERSION: environment.wmsVersion
        },
        projection: projection
      })
    });
    const olMap = new Map({
      target: target,
      view: new View(options),
      overlays: [overlay],
    });
    olMap.addLayer(layer);
    olMap.getView().fit(extent);
    return olMap;
  }

  /**
   *
   * @ngdoc method
   * @name MapService.addLayer
   * @description Agrega una nueva capa al mapa a partir de la respuesta del servicio WFS
   * @param {Map=} olMap
   * @param {string=} capa
   * @param {WFSResponse=} wfsResponse
   */
  addLayer(olMap: Map, capa: string, wfsResponse: WFSResponse) {
    const className = `${capa}-layer`;
    const extent = boundingExtent(this.getBBox(wfsResponse.features));

    const geojsonFormat = new GeoJSON();

    try {
      const features = geojsonFormat.readFeatures(JSON.stringify(wfsResponse));

      const vectorLayer = new VectorLayer({
        source: new VectorSource({
          format: geojsonFormat,
          features: features,
        }),
        style: new Style({
          stroke: new Stroke({
            color: 'blue',
            width: 3
          })
        }),
        className: className
      });

      olMap.getLayers().getArray().filter(layer => layer.getClassName() === className)
        .forEach(layer => olMap.removeLayer(layer));

      olMap.addLayer(vectorLayer);

      olMap.getView().fit(extent);

    } catch (error) {
      console.error("Error processing features:", error);
    }
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getObjectId
   * @description Obtiene el ObjectId a partir del texto de busqueda
   * @param {string=} searchString
   * @returns {Observable<ObjectId>=}
   */
  getObjectId(searchString: string): Observable<ObjectId> {
    const fields: string[] = searchString.toLowerCase().split(',');
    const tipoBusqueda = this.getTipoBusqueda(searchString);
    const texto: string = fields[0];
    let service: Observable<ObjectId> = of({
      objectId: undefined,
      typename: ''
    } as ObjectId);
    if (tipoBusqueda === TipoBusqueda.CP) {
      service = this.getObjectIdByCP(texto, environment.typedSearchCP);
    /*} else if (tipoBusqueda === TipoBusqueda.CALLE) {
      service = this.getObjectIdByDireccion(texto, environment.typedSearchDIRECCION, muni);
    */
    } else if (tipoBusqueda === TipoBusqueda.LOCALIDAD) {
      service = this.getObjectIdByLocalidad(texto, environment.typedSearchLOCALIDAD);
    }
    return service;
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getObjectIdByCP
   * @description Obtiene el ObjectId para un CP
   * @param {string=} texto
   * @param {string=} type
   * @returns {Observable<ObjectId>=}
   */
  getObjectIdByCP(texto: string, type: string): Observable<ObjectId> {
    return this.igearService.typedSearchService(texto, type)
      .pipe(map((res: XMLDocument) => {
        const objectId: ObjectId = {
          objectId: res.getElementsByTagName('List')[0].textContent?.split('#')[3],
          typename: environment.typenameCP
        }
        return objectId;
      }));
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getObjectIdByDireccion
   * @description Obtiene el ObjectId para una dirección
   * @param {string=} texto
   * @param {string=} type
   * @param {string=} muni
   * @returns
   */
  getObjectIdByDireccion(texto: string, type: string, muni: string): Observable<ObjectId> {
    return this.igearService.typedSearchService(texto, type, muni)
      .pipe(mergeMap((res: XMLDocument) => {
        const c_mun_via = res.getElementsByTagName('List')[0].textContent?.split('#')[3];
        const cqlFilter = `c_mun_via='${c_mun_via}'`;
        return this.igearService.visor2Dservice(type, cqlFilter)
      }),
        map((res: any) => {
          const objectId = {
            objectId: undefined,
            typename: environment.typenameDIRECCION
          };
          if (res.totalFeatures > 0) {
            objectId.objectId = res.features[0].properties.objectid;
          }
          return objectId;
        }));
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getObjectIdByLocalidad
   * @description Obtiene el ObjectId para una localidad
   * @param {string=} texto
   * @param {string=} type
   * @param {string=} muni
   * @returns {Observable<ObjectId>=}
   */
  getObjectIdByLocalidad(texto: string, type: string): Observable<ObjectId> {
    return this.igearService.typedSearchService(texto, type)
      .pipe(map((res: XMLDocument) => {
        const listElements = res.getElementsByTagName('List');

        if (listElements.length === 0) {
          return {
            objectId: undefined,
            typename: environment.typenameLOCALIDAD
          } as ObjectId;
        }

        const textContent = listElements[0].textContent;

        if (!textContent) {
          return {
            objectId: undefined,
            typename: environment.typenameLOCALIDAD
          } as ObjectId;
        }

        const parts = textContent.split('#');
        const extractedObjectId = parts[3];

        const objectId: ObjectId = {
          objectId: extractedObjectId,
          typename: environment.typenameLOCALIDAD
        }
        return objectId;
      }));
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getTipoBusqueda
   * @description Obtiene el tipo de búsqueda a partir del texto de busqueda
   * @param {string=} searchString
   * @returns {TipoBusqueda=}
   */
  getTipoBusqueda(searchString: string): TipoBusqueda {
    let tipoBusqueda: TipoBusqueda = TipoBusqueda.SIN_DEFINIR;

    const cpRegex = /^(?:0?[1-9]|[1-4]\d|5[0-2])\d{3}$/;
    const calleRegex = /^[\w\s]+,[^\d]+?$/;
    const localidadRegex = /^[^\d,]+$/;

    if (cpRegex.test(searchString)) {
      tipoBusqueda = TipoBusqueda.CP;
    } else if (calleRegex.test(searchString)) {
      const fields = searchString.split(',')
      if (fields.length == 2 && fields[1].trim().length > 0) {
        tipoBusqueda = TipoBusqueda.CALLE;
      }
    } else if (localidadRegex.test(searchString)) {
      if (searchString.trim().length > 0) {
        tipoBusqueda = TipoBusqueda.LOCALIDAD;
      }
    }
    return tipoBusqueda;
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getWFSFeatures
   * @description Obtiene la respuesta WFS a partir del ObjectId
   * @param {string=} ObjectId
   * @param {string=} typename
   * @param {string=} capa
   * @param {number=} distancia
   * @returns {Observable<WFSResponse>=}
   */
  getWFSFeatures(ObjectId: string, typename: string, capa: string, distancia: number): Observable<WFSResponse> {
    return this.igearService.spatialSearchService(ObjectId, typename)
      .pipe(switchMap(response => {
        let cqlFilter = typename === environment.typenameCP ? `objectid=${ObjectId}` : '';

        for (const resultado of response.resultados) {
          if (resultado.distancia === distancia && resultado.capa.includes(capa)) {
            for (const feature of resultado.featureCollection.features) {
              const oid = feature.properties.objectid;
              cqlFilter += cqlFilter !== '' ? ` OR objectid=${oid}` : `objectid=${oid}`;
            }
            break;
          }
        }

        return this.igearService.sitaWMSGetFeature(capa, cqlFilter);
      }));
  }

  /**
   *
   * @ngdoc method
   * @name MapService.getBBox
   * @description Obtiene el boundingbox a partir de la geometría de la búsqueda
   * @param {any=} features
   * @returns {Coordinate=}
   */
  getBBox(features: any): Coordinate[] {
    // Handle empty/invalid input
    if (!features || features.length === 0) {
      return environment.aragonBoundingBox; // Fallback to default view
    }

    // Initialize with Aragon bounding box limits instead of Infinity
    const aragonBounds = environment.aragonBoundingBox;
    let minX = aragonBounds[1][0]; // Start with max X from Aragon
    let maxX = aragonBounds[0][0]; // Start with min X from Aragon
    let minY = aragonBounds[1][1]; // Start with max Y from Aragon
    let maxY = aragonBounds[0][1]; // Start with min Y from Aragon

    for (const feature of features) {
      if (!feature.geometry) {
        continue; // Skip features without geometry
      }

      // Extract coordinates from ANY geometry type
      const coords = this.extractCoordinatesFromGeometry(feature.geometry);

      for (const coord of coords) {
        if (coord.length >= 2) {
          const x = coord[0];
          const y = coord[1];

          minX = Math.min(minX, x);
          maxX = Math.max(maxX, x);
          minY = Math.min(minY, y);
          maxY = Math.max(maxY, y);
        }
      }
    }

    // Fallback if no valid coordinates found (bounds haven't changed from initial values)
    if (minX === aragonBounds[1][0] && maxX === aragonBounds[0][0] &&
        minY === aragonBounds[1][1] && maxY === aragonBounds[0][1]) {
      return environment.aragonBoundingBox;
    }

    return [[minX, minY], [maxX, maxY]];
  }

  /**
   * Helper method to extract coordinates from LineString and MultiLineString geometries only
   */
  private extractCoordinatesFromGeometry(geometry: any): number[][] {
    const coordinates: number[][] = [];

    switch (geometry.type) {
      case 'LineString':
        coordinates.push(...geometry.coordinates);
        break;

      case 'MultiLineString':
        for (const lineString of geometry.coordinates) {
          coordinates.push(...lineString);
        }
        break;

      // All other geometry types are ignored
      default:
        // Skip unsupported geometry types
        break;
    }

    return coordinates;
  }
}

