import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, ViewChild } from '@angular/core';
import { Map, Overlay } from 'ol';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';
import { MapService } from 'src/app/shared/services/map.service';
import { PopupComponent } from '../popup/popup.component';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() searchString: string = '';
  @ViewChild(PopupComponent, { read: ElementRef }) popupRef!: ElementRef;
  @Output() searchStatusEvent: EventEmitter<string> = new EventEmitter();
  isDone: boolean = false;
  isPopupHide: boolean = true;
  target: string = 'map';
  olMap: Map = new Map({});
  overlay!: Overlay;
  featureSelect!: FeatureSelect;

  constructor(private mapService: MapService) { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges): void {
    this.updateMap();
  }

  initMap(): void {
    this.overlay = new Overlay({
      element: this.popupRef.nativeElement,
      autoPan: false,
      autoPanAnimation: {
          duration: 250,
      },
    });
    this.olMap = this.mapService.initMap(this.target, this.overlay);
    this.olMap.on('click', (evt) => {
      let pixel = this.olMap.getEventPixel(evt.originalEvent);
      this.olMap.forEachFeatureAtPixel(pixel, (feature, resolution) => {
        const featureSelect = {
          evt: evt,
          feature: feature
        }
        this.updatePopup(featureSelect);
      })
    });
  }

  updateMap(): void {
    if (this.searchString !== '') {
      this.isDone = false;
      this.isPopupHide = true;
      this.searchStatusEvent.emit(`Localizando ${this.searchString}...`);
      this.mapService.getObjectId(this.searchString).subscribe(objectId => {
        this.searchStatusEvent.emit('Cargando datos de alquileres...');
        if (objectId.objectId !== undefined) {
          this.mapService.addLayer(this.olMap, objectId.objectId, objectId.typename, 'fianzas', 1000)
          .subscribe(olMap => {
            this.isDone = true;
            this.searchStatusEvent.emit('FIN');
          })
        }
      });
    }
  }

  updatePopup(featureSelect: FeatureSelect): void {
    this.featureSelect = featureSelect;
    this.overlay.setPosition(featureSelect.evt.coordinate);
  }

}
