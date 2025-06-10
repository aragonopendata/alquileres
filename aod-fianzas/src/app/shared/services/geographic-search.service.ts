import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environments/environment';

// Define interfaces matching backend models
export interface LocationSearchRequest {
  search_text: string;
}

export interface CRSProperties {
  name: string;
}

export interface CRS {
  type: string;
  properties: CRSProperties;
}

export interface FeatureProperties {
  c_mun_via?: string;
  objectid?: number;
  valores?: string;
  via_loc?: string;
  [key: string]: any; // Allow additional properties
}

export interface Feature {
  geometry?: any;
  geometry_name?: string;
  id: string;
  properties: FeatureProperties;
  type: string;
}

export interface GeographicWFSResponse {
  crs: CRS;
  features: Feature[];
  totalFeatures: number;
  type: string;
}

export interface LocationSearchResponse {
  success: boolean;
  search_text: string;
  search_type: 'CP' | 'LOCALIDAD' | 'CALLE' | 'SIN_DEFINIR';
  data?: GeographicWFSResponse;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class GeographicSearchService {

  constructor(private http: HttpClient) { }

  /**
   * Performs a geographic search using the backend consolidated endpoint
   * @param searchText Text to search for (postal code, municipality, or street)
   * @returns Observable<LocationSearchResponse>
   */
  searchLocation(searchText: string): Observable<LocationSearchResponse> {
    const request: LocationSearchRequest = {
      search_text: searchText
    };

    return this.http.post<LocationSearchResponse>(`${environment.backendUrl}/api/geographic-search`, request);
  }
} 