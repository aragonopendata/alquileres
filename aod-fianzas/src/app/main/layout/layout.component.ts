import { Component } from '@angular/core';
// import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
// import { NgIf } from '@angular/common';
// import { ListsearchComponent } from '../listsearch/listsearch.component';
// import { HeaderComponent } from '../header/header.component';
// import { MapComponent } from '../map/map.component';
import { FooterComponent } from '../footer/footer.component';
import { MapSearchComponent

 } from '../map-search/map-search.component';
import { ListsearchComponent } from "../listsearch/listsearch.component";
@Component({
    selector: 'app-layout',
    templateUrl: './layout.component.html',
    styleUrls: ['./layout.component.scss'],
    imports: [MapSearchComponent, FooterComponent, ListsearchComponent]
})
export class LayoutComponent {
  // wfsResponse!: WFSResponse;
  showListSearch = false;

  // updateMap(wfsResponse: WFSResponse): void {
  //   this.wfsResponse = wfsResponse;
  // }

  toggleComponents(): void {
    this.showListSearch = !this.showListSearch;
  }

}
