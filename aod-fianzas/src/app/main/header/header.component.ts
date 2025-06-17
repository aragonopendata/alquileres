import { Component, EventEmitter, Output } from '@angular/core';
// import { none } from 'ol/centerconstraint';

import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
import { GeographicSearchService, LocationSearchResponse } from 'src/app/shared/services/geographic-search.service';
import { NgIf } from '@angular/common';


@Component({
    selector: 'app-header',
    templateUrl: './header.component.html',
    styleUrls: ['./header.component.scss'],
    imports: [NgIf]
})
export class HeaderComponent {
  @Output() searchEvent = new EventEmitter<WFSResponse>();
  isSearching = true;
  isDone = false;
  isError = false;
  searchText!: string;
  errorStatus!: string;

  constructor(private geographicSearchService: GeographicSearchService) { }

  onSearch(searchString: string): void {
    this.searchText = `Localizando ${searchString}...`;
    this.isError = false;
    this.isDone = false;
    this.isSearching = false;
    
    this.geographicSearchService.searchLocation(searchString).subscribe({
      next: (response: LocationSearchResponse) => {
        if (response.success && response.data && response.data.features.length > 0) {
          this.searchText = searchString;
          this.isDone = true;
          
          // Convert backend response to frontend WFSResponse format
          const wfsResponse: WFSResponse = {
            crs: {
              type: response.data.crs.type,
              properties: [response.data.crs.properties] // Convert single object to array
            },
            features: response.data.features.map(feature => ({
              geometry: feature.geometry || {}, // Ensure geometry is not undefined
              geometry_name: feature.geometry_name || '',
              id: feature.id,
              properties: {
                c_mun_via: feature.properties.c_mun_via || '',
                objectid: feature.properties.objectid || 0,
                valores: feature.properties.valores || '',
                via_loc: feature.properties.via_loc || ''
              },
              type: feature.type
            })),
            totalFeatures: response.data.totalFeatures,
            type: response.data.type
          };
          
          this.searchEvent.emit(wfsResponse);
        } else {
          this.searchText = "";
          this.isError = true;
          this.errorStatus = response.message || `No se han encontrado resultados para la búsqueda ${searchString}. Por favor, revise su consulta.`;
          this.isDone = true;
        }
      },
      error: (error) => {
        this.searchText = "";
        this.isError = true;
        this.errorStatus = 'Ha habido un fallo en la consulta. Por favor, inténtelo de nuevo.';
        this.isDone = true;
        console.error('Geographic search error:', error);
      }
    });
  }

}
