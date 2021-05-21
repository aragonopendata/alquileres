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
  isError: boolean = false;
  searchText!: string;
  errorStatus!: string;

  constructor() { }

  ngOnInit(): void {
  }

  ngOnChanges(chages: SimpleChanges): void {
    if (chages.searchStatus.currentValue === '') {
      this.isSearching = true;
    } else if (chages.searchStatus.currentValue === 'FIN') {
      this.searchStatus = '';
      this.isDone = true;
    } else if (chages.searchStatus.currentValue === 'ERROR') {
      this.searchStatus = '';
      this.errorStatus = 'No se han encontrado resultados. Por favor, revise su consulta'
      this.isSearching = true;
      this.isError = true;
    } else {
      this.isSearching = false;
    }
  }

  onSearch(searchString: string): void {
    this.searchText = searchString;
    this.isError = false;
    this.searchEvent.emit(searchString);
  }

}
