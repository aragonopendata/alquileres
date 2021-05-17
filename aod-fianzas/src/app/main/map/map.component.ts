import { Component, OnInit } from '@angular/core';
import { Map } from 'ol';
import { MapService } from 'src/app/shared/services/map.service';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit {
  target: string = 'map';
  map: Map = new Map({});

  constructor(private mapService: MapService) { }

  ngOnInit(): void {
    this.map = this.mapService.initMap(this.target);
    
    this.mapService.getObjectId('50001').subscribe(objectId => {
      if (objectId.objectId !== undefined) {
        this.mapService.addLayer(this.map, objectId.objectId, environment.typenameCP, 'fianzas', 1000)
      }
    });
  }

}
