import { Component, OnInit } from '@angular/core';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
import { NgIf } from '@angular/common';
import { ListsearchComponent } from '../listsearch/listsearch.component';
import { HeaderComponent } from '../header/header.component';
import { MapComponent } from '../map/map.component';
import { FooterComponent } from '../footer/footer.component';

@Component({
    selector: 'app-layout',
    templateUrl: './layout.component.html',
    styleUrls: ['./layout.component.scss'],
    imports: [NgIf, ListsearchComponent, HeaderComponent, MapComponent, FooterComponent]
})
export class LayoutComponent implements OnInit {
  wfsResponse!: WFSResponse;
  showListSearch: boolean = false;

  constructor() { }

  ngOnInit(): void {
  }

  updateMap(wfsResponse: WFSResponse): void {
    this.wfsResponse = wfsResponse;
  }

  toggleComponents(): void {
    this.showListSearch = !this.showListSearch;
  }

}
