import { Component, OnInit, OnDestroy, Output, EventEmitter } from '@angular/core';
import { NgFor } from '@angular/common';
import { FianzaListComponent } from '../fianza-list/fianza-list.component';
import { AlquileresApiService } from 'src/app/shared/services/alquileres-api.service';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';

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
    imports: [NgFor, FianzaListComponent, FormsModule],
    standalone: true
})
export class ListsearchComponent implements OnInit, OnDestroy {

  municipalities: Municipality[] = [];
  streets: Street[] = [];
  selectedMunicipality = '';
  selectedStreet = '';

  @Output() selectionChanged = new EventEmitter<{ municipality: string, street: string }>();

  private municipalityChange$ = new Subject<string>();
  private subscription!: Subscription;

  constructor(private alquileresService: AlquileresApiService) { }

  ngOnInit(): void {
    this.fetchMunicipalities();
    this.subscription = this.municipalityChange$.pipe(
      switchMap(municipality => this.alquileresService.fetchStreets(municipality))
    ).subscribe({
      next: (data) => { this.streets = data; },
      error: (error) => { console.error('Error fetching streets from api. ', error); }
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  fetchMunicipalities(): void {
    this.alquileresService.fetchMunicipalities().subscribe({
      next: (data) => { this.municipalities = data; },
      error: (error) => { console.error('Error fetching municipalities from api. ', error); }
    });
  }


  fetchStreets(municipality: string): void {
    this.municipalityChange$.next(municipality);
  }

  onMunicipalityChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const municipality = selectElement.value;
    this.selectedMunicipality = municipality;

    this.selectedStreet = '';
    this.streets = [];
    this.fetchStreets(municipality);
  }

  onStreetChange(event: Event): void {
    const selectElement = event.target as HTMLSelectElement;
    const selectedStreet = selectElement.value;
    this.selectedStreet = selectedStreet;
    this.selectionChanged.emit({ municipality: this.selectedMunicipality, street: selectedStreet });
  }
}
