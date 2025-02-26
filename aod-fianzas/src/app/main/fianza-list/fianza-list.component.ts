import { Component, OnInit, Input, OnChanges, SimpleChanges } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment'; 

@Component({
  selector: 'app-fianza-list',
  templateUrl: './fianza-list.component.html',
  styleUrls: ['./fianza-list.component.scss']
})

export class FianzaListComponent implements OnInit, OnChanges {

  @Input() selectedMunicipality: string = '';
  @Input() selectedStreet: string = '';

  fianzas: any[] = [
    // Add more fianza objects as needed
  ];

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
  }

  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes.selectedMunicipality || changes.selectedStreet) {
      this.filterFianzas();
    }
  }
  //results are like   {
  //   "anyo": 2023,
  //   "codigo_provincia": "22",
  //   "clave_calle": "24130",
  //   "nombre_calle": "MAYOR",
  //   "nombre_municipio": "ABIZANDA",
  //   "tipo": "Vivienda",
  //   "anyo_devolucion": "2023",
  //   "total_rentas_str": null,
  //   "total_importes": "180",
  //   "total_devolucion": "",
  //   "total_rentas": 180
  // },
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
      // console.log(this.fianzas)      
    }
    
  }

}
