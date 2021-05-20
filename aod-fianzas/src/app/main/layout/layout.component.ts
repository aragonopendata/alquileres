import { Component, OnInit } from '@angular/core';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.scss']
})
export class LayoutComponent implements OnInit {
  searchString: string = '';
  featureSelect: FeatureSelect|undefined;

  constructor() { }

  ngOnInit(): void {
  }

  updateMap(searchString: string) {
    this.searchString = searchString;
  }

  updatePopup(featureSelect: FeatureSelect) {
    this.featureSelect = featureSelect;
  }

}
