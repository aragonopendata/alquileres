import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, ViewChild } from '@angular/core';
import { Map, Overlay } from 'ol';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
import { MapService } from 'src/app/shared/services/map.service';
import { PopupComponent } from '../popup/popup.component';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.scss']
})
export class MapComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() wfsResponse!: WFSResponse;
  @ViewChild(PopupComponent, { read: ElementRef }) popupRef!: ElementRef;
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
    if (this.wfsResponse !== undefined) {
      this.mapService.addLayer(this.olMap, 'fianzas', this.wfsResponse);
      this.isDone = true;
    }
  }

  updatePopup(featureSelect: FeatureSelect): void {
    this.featureSelect = featureSelect;
    this.overlay.setPosition(featureSelect.evt.coordinate);
  }

}
