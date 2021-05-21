import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-layout',
  templateUrl: './layout.component.html',
  styleUrls: ['./layout.component.scss']
})
export class LayoutComponent implements OnInit {
  searchString: string = '';
  searchStatus: string = '';

  constructor() { }

  ngOnInit(): void {
  }

  updateMap(searchString: string): void {
    this.searchString = searchString;
  }

  onUpdateSearchStatus(searchStatus: string) {
    this.searchStatus = searchStatus;
  }

}
