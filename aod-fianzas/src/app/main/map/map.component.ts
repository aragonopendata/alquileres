import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { Map } from 'ol';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';
import { MapService } from 'src/app/shared/services/map.service';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit, OnChanges {
  @Input() searchString: string = '';
  @Output() featureSelectEvent = new EventEmitter<FeatureSelect>();
  target: string = 'map';
  olMap: Map = new Map({});

  constructor(private mapService: MapService) { }

  ngOnInit(): void {
    this.olMap = this.mapService.initMap(this.target);
  }

  ngOnChanges(changes: SimpleChanges) {
    this.updateMap();
  }

  updateMap() {
    if (this.searchString !== '') {
      this.mapService.getObjectId(this.searchString).subscribe(objectId => {
        if (objectId.objectId !== undefined) {
          this.mapService.addLayer(this.olMap, objectId.objectId, objectId.typename, 'fianzas', 1000)
          this.mapService.addListener(this.olMap, this.onFeatureSelectFuncion);
        }
      });
    }
  }

  onFeatureSelectFuncion(featureSelect: FeatureSelect) {
    this.featureSelectEvent.emit(featureSelect);
  }

}
