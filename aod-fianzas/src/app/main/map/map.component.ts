import { AfterViewInit, Component, ElementRef, Input, ViewChild } from '@angular/core';
import { Map, Overlay } from 'ol';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
import { MapService } from 'src/app/shared/services/map.service';
import { PopupComponent } from '../popup/popup.component';
import { NgIf } from '@angular/common';

@Component({
    selector: 'app-map',
    templateUrl: './map.component.html',
    styleUrls: ['./map.component.scss'],
    imports: [NgIf, PopupComponent]
})
export class MapComponent implements AfterViewInit {
  @Input() wfsResponse!: WFSResponse;
  @ViewChild(PopupComponent, { read: ElementRef }) popupRef!: ElementRef;
  isDone = false;
  isPopupHide = true;
  target = 'map';
  olMap: Map = new Map({});
  overlay!: Overlay;
  featureSelect!: FeatureSelect;

  constructor(private mapService: MapService) { }

  ngAfterViewInit(): void {
    this.initMap();
  }

  // ngOnChanges(changes: SimpleChanges): void {
  //   this.updateMap();
  // }

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
      const featuresT:object [] = []
      const pixel = this.olMap.getEventPixel(evt.originalEvent);
      this.olMap.forEachFeatureAtPixel(pixel, (feature) => {
        featuresT.push(feature);
      })
      
      if (featuresT.length > 0){
        const feature = featuresT[0];
      
        const featureSelect = {
          evt: evt,
          feature: feature
        }
        
      this.updatePopup(featureSelect);
      }
         
      
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
