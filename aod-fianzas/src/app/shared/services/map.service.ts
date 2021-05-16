import { Injectable } from '@angular/core';
import { Map, View } from 'ol';
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
import { Observable } from 'rxjs';
import { Coordinate } from 'ol/coordinate';
import { map, switchMap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class MapService {

  constructor(private igearService: IgearService) { }

  /**
   * 
   * @ngdoc method
   * @name MapService.initMap
   * @description
   * @param {string=} target 
   * @returns {Map=}
   */
   initMap(target: string): Map {
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
    });
    olMap.addLayer(layer);
    olMap.getView().fit(extent);
    return olMap;
  }

  /**
   * 
   * @ngdoc method
   * @name MapService.addLayer
   * @description
   * @param {Map=} olMap 
   * @param {string=} ObjectId 
   * @param {string=} typename 
   * @param {string=} capa 
   * @param {number=} distancia 
   */
  addLayer(olMap: Map, ObjectId: string, typename: string, capa: string, distancia: number): void {
    this.igearService.spatialSearchService(ObjectId, typename)
      .pipe(switchMap(response => {
        let cqlFilter = typename === environment.typenameDIRECCION ? `ObjectId=${ObjectId} OR ` : '';
        for (let resultado of response.resultados) {
          if (resultado.distancia === distancia && resultado.capa.includes(capa)) {
            for (let feature of resultado.featureCollection.features) {
              const oid = feature.properties.ObjectId;
              cqlFilter += cqlFilter !== '' ? ` OR ObjectId=${oid}` : `ObjectId=${oid}`;
            }
            break;
          }
        }
        return this.igearService.sitaWMSGetFeature(capa, cqlFilter);
      }))
      .subscribe(response => {
        const extent = boundingExtent(this.getBBox(response.features));
        const geojsonFormat = new GeoJSON();
        const features = geojsonFormat.readFeature(JSON.stringify(response));
        const vectorLayer = new VectorLayer({
          source: new VectorSource({
            format: geojsonFormat,
            features: [features]
          })
        });
        olMap.addLayer(vectorLayer);
        olMap.getView().fit(extent);
      });
  }

  /**
   * 
   * @ngdoc method
   * @name MapService.getObjectId
   * @description
   * @param {string=} searchString 
   * @returns {Observable<ObjectId>=}
   */
  getObjectId(searchString: string): Observable<ObjectId> {
    const fields: string[] = searchString.toLowerCase().split(',');
    const tipoBusqueda = this.getTipoBusqueda(searchString);
    const texto: string = fields[0];
    let type: string = '';
    const muni: string = fields[1];
    if (tipoBusqueda === TipoBusqueda.CP) {
      type = environment.typedSearchCP;
    } else if (tipoBusqueda === TipoBusqueda.CALLE) {
      type = environment.typedSearchDIRECCION;
    } else if (tipoBusqueda === TipoBusqueda.LOCALIDAD) {
      type = environment.typedSearchLOCALIDAD;
    }
    return this.igearService.typedSearchService(texto, type, muni)
    .pipe(map((res:XMLDocument) => {
      const ObjectId: ObjectId = {
        objectId: res.getElementsByTagName('List')[0].textContent?.split('#')[3]
      }
      return ObjectId;
    }));
  }

  /**
   * 
   * @ngdoc method
   * @name MapService.getTipoBusqueda
   * @description
   * @param {string=} searchString 
   * @returns {TipoBusqueda=}
   */
  getTipoBusqueda(searchString: string): TipoBusqueda {
    let tipoBusqueda: TipoBusqueda = TipoBusqueda.SIN_DEFINIR;
    if (/^(?:0?[1-9]|[1-4]\d|5[0-2])\d{3}$/.test(searchString)) {
      tipoBusqueda = TipoBusqueda.CP;
    } else if (/^[^\d]+\s\d+,[^\d]+?$/.test(searchString)) {
      const fields = searchString.split(',')
      if (fields.length == 2 && fields[1].trim().length > 0) {
        tipoBusqueda = TipoBusqueda.CALLE;
      }
    } else if (/^[^\d]+$/.test(searchString)) {
      if (searchString.trim().length > 0) {
        tipoBusqueda = TipoBusqueda.LOCALIDAD;
      }
    }
    return tipoBusqueda;
  }

  /**
   * 
   * @ngdoc method
   * @name MapService.getSearchResultCount
   * @description
   * @param {XMLDocument=} searchResult 
   * @returns {Number=}
   */
  getSearchResultCount(searchResult: XMLDocument): Number {
    const count: number = Number(searchResult.getElementsByTagName('Count')[0].textContent);
    return count;
  }

  /**
   * 
   * @ngdoc method
   * @name MapService.getBBox
   * @description
   * @param {any=} features 
   * @returns {Coordinate=}
   */
  getBBox(features: any): Coordinate[] {
    let bbox = [[Infinity, Infinity], [-Infinity, -Infinity]];
    for (let feature of features) {
      if (feature.geometry.type == "Polygon") {
        for (let row of feature.geometry.coordinates) {
          for (let coordinate of row) {
            bbox[0][0] = coordinate[0] < bbox[0][0] ? coordinate[0] | 0 : bbox[0][0];
            bbox[1][0] = coordinate[0] > bbox[1][0] ? coordinate[0] | 0 : bbox[1][0];
            bbox[0][1] = coordinate[1] < bbox[0][1] ? coordinate[1] | 0 : bbox[0][1];
            bbox[1][1] = coordinate[1] > bbox[1][1] ? coordinate[1] | 0 : bbox[1][1];
          }
        }
      }
    }
    return bbox;
  }

}
