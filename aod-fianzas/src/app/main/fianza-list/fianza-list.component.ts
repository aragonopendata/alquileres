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

  fianzas: any[] = [];
  stats: FianzaItem[] = [];

  constructor(private http: HttpClient, private alquileresService: AlquileresApiService) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.selectedMunicipality || changes.selectedStreet) {
      // this.filterFianzas();
      this.filterStats();
    }
  }


  filterFianzas(): void {
    // Implement your filtering logic here
    console.log('Selected municipality:', this.selectedMunicipality);
    console.log('Selected street:', this.selectedStreet);
    if (this.selectedMunicipality && this.selectedStreet) {
      const URL = `${environment.urlApi}/municipality/${this.selectedMunicipality}/street/${this.selectedStreet}`;
      this.http.get<any[]>(URL)
        .subscribe(data => {
          // loop through data and parse to a list of fianzas results
          this.fianzas = data.map(item => ({
            anyo: item.anyo,
            codigo_provincia: item.codigo_provincia,
            clave_calle: item.clave_calle,
            nombre_calle: item.nombre_calle,
            nombre_municipio: item.nombre_municipio,
            tipo: item.tipo,
            anyo_devolucion: item.anyo_devolucion,
            total_importes: item.total_importes,
            total_devolucion: item.total_devolucion,
            total_rentas: item.total_rentas

          }));

          console.log(`Data: ${this.fianzas}`)
        }, error => {
          console.error('Error fetching fianzas', error);
        });

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
