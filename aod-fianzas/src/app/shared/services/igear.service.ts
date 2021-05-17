import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from "rxjs/operators";
import { environment } from 'src/environments/environment';
import { SpatialSearchResults } from '../models/spatial-search-results.model';

@Injectable({
  providedIn: 'root'
})
export class IgearService {

  constructor(private http: HttpClient) { }

  /**
   * 
   * @param texto 
   * @param type 
   * @param muni 
   * @returns 
   */
   typedSearchService(texto: string, type: string, muni?: string): Observable<XMLDocument> {
    let params = new HttpParams()
      .set('texto', texto)
      .set('type', type)
      .set('app', 'DV');
    if (muni !== undefined) {
      params = params.set('muni', muni);
    }
    const options: Object = {
      params: params,
      responseType: 'text'
    };
    return this.http.get<string>(environment.urlTypedSearchService, options)
      .pipe(map(xml => new DOMParser().parseFromString(xml, 'text/xml')));
  }

  /**
   * 
   * @param objectId 
   * @param typename 
   * @returns 
   */
  spatialSearchService(objectId: string, typename: string): Observable<SpatialSearchResults> {
    const body = new HttpParams()
      .set('SERVICE', 'DV')
      .set('TYPENAME', typename)
      .set('CQL_FILTER', `OBJECTID=${objectId}`)
      .set('PROPERTYNAME', 'OBJECTID')
      .set('TYPENAME_CONN', 'DV');
    return this.http.post<SpatialSearchResults>(environment.urlSpatialSearchService, body)
  }

  /**
   * 
   * @param capa 
   * @param cqlFilter 
   * @returns 
   */
  sitaWMSGetFeature(capa: string, cqlFilter: string): Observable<any> {
    const body = new HttpParams()
      .set('service', 'WFS')
      .set('version', '1.0.0')
      .set('request', 'GetFeature')
      .set('typename', capa)
      .set('outputFormat', 'application/json')
      .set('srsname', environment.epsgCode)
      .set('CQL_FILTER', cqlFilter);
    return this.http.post<any>(environment.urlSitaWMS, body);
  }

}
