import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { WFSResponse } from 'src/app/shared/models/wfs-response.model';
import { MapService } from 'src/app/shared/services/map.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  @Output() searchEvent = new EventEmitter<WFSResponse>();
  isSearching: boolean = true;
  isDone: boolean = false;
  isError: boolean = false;
  searchText!: string;
  errorStatus!: string;

  constructor(private mapService: MapService) { }

  ngOnInit(): void {
  }

  onSearch(searchString: string): void {
    this.searchText = `Localizando ${searchString}...`;
    this.isError = false;
    this.isDone = false;
    this.isSearching = false;
    this.mapService.getObjectId(searchString).subscribe(
      objectId => {
        if (objectId.objectId !== undefined) {
          this.searchText = 'Cargando datos de alquileres...';
          this.mapService.getWFSFeatures(objectId.objectId, objectId.typename, 'fianzas', 1000).subscribe(
            wfsResponse => {
              this.searchText = searchString;
              this.isDone = true;
              this.searchEvent.emit(wfsResponse);
            })
        } else {
          this.errorStatus = 'No se han encontrado resultados. Por favor, revise su consulta';
          this.isError = true;
        }
      },
      error => {
        this.errorStatus = 'Ha habido un fallo en la consulta. Por favor, intentelo de nuevo';
        this.isError = true;
      });
  }



}
