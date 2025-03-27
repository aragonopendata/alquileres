import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { NgFor } from '@angular/common';
import { FianzaListComponent } from '../fianza-list/fianza-list.component';
import { AlquileresApiService } from 'src/app/shared/services/alquileres-api.service';
import { FormsModule } from '@angular/forms';

interface  Municipality {
  nombre_municipio: string;
}

interface Street {
  nombre_calle: string;
}


@Component({
    selector: 'app-listsearch',
    templateUrl: './listsearch.component.html',
    styleUrls: ['./listsearch.component.scss'],
    imports: [NgFor, FianzaListComponent, FormsModule]
})
export class ListsearchComponent implements OnInit {

  municipalities: Municipality[] = [];
  streets: Street[] = [];
  selectedMunicipality = '';
  selectedStreet = '';

  @Output() selectionChanged = new EventEmitter<{ municipality: string, street: string }>();

  constructor(private alquileresService: AlquileresApiService) { }

  ngOnInit(): void {
    this.fetchMunicipalities();
  }

  fetchMunicipalities(): void {
    this.alquileresService.fetchMunicipalities().subscribe(data => {
      this.municipalities = data;
    },
      error => {
      console.error('Error fetching municipalities from api. ', error);
    });
  }


  fetchStreets(municipality: string): void {
    this.alquileresService.fetchStreets(municipality).subscribe(data => {
      this.streets = data;
    },
      error => {
      console.error('Error fetching streets from api. ', error);
    });
  }

  onMunicipalityChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const municipality = selectElement.value;
    this.selectedMunicipality = municipality;

    this.selectedStreet = '';
    this.streets = [];
    this.fetchStreets(municipality);
    console.log(this.selectedStreet);
  }

  onStreetChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const selectedStreet = selectElement.value;
    this.selectedStreet = selectedStreet;
    this.selectionChanged.emit({ municipality: this.selectedMunicipality, street: selectedStreet });
    console.log('Emitting {this.selectedMunicipality}{selectedStreet}.');
  }
}
