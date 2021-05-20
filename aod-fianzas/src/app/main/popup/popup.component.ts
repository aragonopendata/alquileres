import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';

@Component({
  selector: 'app-popup',
  templateUrl: './popup.component.html',
  styleUrls: ['./popup.component.scss']
})
export class PopupComponent implements OnInit, OnChanges {
  @Input() featureSelect: FeatureSelect|undefined;

  constructor() { }

  ngOnInit(): void {
  }

  ngOnChanges(changes: SimpleChanges) {
    this.featureSelect = changes.featureSelect.currentValue;
  }

}
