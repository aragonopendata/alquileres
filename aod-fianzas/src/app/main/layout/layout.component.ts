import { Component, OnInit } from '@angular/core';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.scss']
})
export class LayoutComponent implements OnInit {
  wfsResponse!: WFSResponse;

  constructor() { }

  ngOnInit(): void {
  }

  updateMap(wfsResponse: WFSResponse): void {
    this.wfsResponse = wfsResponse;
  }

}
