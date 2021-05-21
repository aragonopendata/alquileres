import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit, OnChanges {
  @Input() searchStatus: string = '';
  @Output() searchEvent = new EventEmitter<string>();
  isSearching: boolean = true;
  isDone: boolean = false;
  searchText!: string;

  constructor() { }

  ngOnInit(): void {
  }

  ngOnChanges(chages: SimpleChanges): void {
    if (chages.searchStatus.currentValue === '') {
      this.isSearching = true;
    } else if (chages.searchStatus.currentValue === 'FIN') {
      this.searchStatus = '';
      this.isDone = true;
    } else {
      this.isSearching = false;
    }
  }

  onSearch(searchString: string): void {
    this.searchText = searchString;
    this.searchEvent.emit(searchString);
  }

}
