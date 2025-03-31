import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { NgFor } from '@angular/common';
import { AlquileresApiService } from 'src/app/shared/services/alquileres-api.service';
import { FianzaItem } from 'src/app/shared/models/fianza-item.model';

@Component({
    selector: 'app-fianza-list',
    templateUrl: './fianza-list.component.html',
    styleUrls: ['./fianza-list.component.scss'],
    imports: [NgFor]
})

export class FianzaListComponent implements OnChanges {

  @Input() selectedMunicipality = '';
  @Input() selectedStreet = '';

  stats: FianzaItem[] = [];

  constructor(private http: HttpClient, private alquileresService: AlquileresApiService) { }

  ngOnChanges(changes: SimpleChanges): void {

    if (changes.selectedMunicipality) {
      this.stats = [];
    }
    
    if (changes.selectedMunicipality || changes.selectedStreet) {
      // this.filterFianzas()
      this.filterStats();
    }
  }

  filterStats(): void {
    if (this.selectedMunicipality && this.selectedStreet) {
      this.alquileresService.fetchStats(this.selectedMunicipality, this.selectedStreet)
        .subscribe((data: FianzaItem[]) => {
          console.log("Data filterstats: ", data);
          this.stats = data;

         // check that stats has more than 0 items
            if (this.stats.length > 0) {
            console.log('Stats have more than 0 items');
            } else {
            console.log('Stats have 0 items');
            }
          console.log("stats: ", this.stats);
        }, error => {
          console.error('Error fetching data from api.', error);
        });
    }
  }

}
