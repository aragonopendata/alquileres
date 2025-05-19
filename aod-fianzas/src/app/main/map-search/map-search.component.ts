import { Component } from '@angular/core';
import { HeaderComponent } from '../header/header.component';
import { MapComponent } from '../map/map.component';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';


@Component({
  selector: 'app-map-search',
  imports: [ HeaderComponent, MapComponent],
  templateUrl: './map-search.component.html',
  styleUrl: './map-search.component.scss'
})
export class MapSearchComponent {

  wfsResponse!: WFSResponse;

  updateMap(wfsResponse: WFSResponse): void {
    this.wfsResponse = wfsResponse;
  }
  

}
