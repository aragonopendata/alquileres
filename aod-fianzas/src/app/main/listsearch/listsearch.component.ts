import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { HttpClient } from '@angular/common/http';


@Component({
  selector: 'app-listsearch',
  templateUrl: './listsearch.component.html',
  styleUrls: ['./listsearch.component.scss']
})
export class ListsearchComponent implements OnInit {

  municipalities: any[] = [];
  streets: any[] = [];
  selectedMunicipality: string = '';
  selectedStreet: string = '';

  @Output() selectionChanged = new EventEmitter<{ municipality: string, street: string }>();

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    this.fetchMunicipalities();
  }

  fetchMunicipalities(): void {
    const URL = "http://localhost:8000/municipality"
    this.http.get<any[]>(URL)
      .subscribe(data => {
        this.municipalities = data;
      }, error => {
        console.error('Error fetching municipalities', error);
      });
  }

  onMunicipalityChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const municipality = selectElement.value;    
    this.selectedMunicipality =municipality
    const URL_STREETS = `http://localhost:8000/municipality/${municipality}/street`
    this.http.get<any[]>(URL_STREETS)
      .subscribe(data => {
        this.streets = data;
      }, error => {
        console.error('Error fetching streets', error);
      });
  }

  onStreetChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const selectedStreet = selectElement.value;
    this.selectedStreet = selectedStreet
    this.selectionChanged.emit({ municipality: this.selectedMunicipality, street: selectedStreet });
    console.log("Emitting {this.selectedMunicipality}{selectedStreet}.")
  }
}
