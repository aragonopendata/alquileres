import { Component, Input, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgFor, NgIf } from '@angular/common';
import { AlquileresApiService } from 'src/app/shared/services/alquileres-api.service';
import { FianzaItem } from 'src/app/shared/models/fianza-item.model';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
    selector: 'app-fianza-list',
    templateUrl: './fianza-list.component.html',
    styleUrls: ['./fianza-list.component.scss'],
    imports: [NgFor, NgIf]
})

export class FianzaListComponent implements OnChanges, AfterViewChecked {

  @Input() selectedMunicipality = '';
  @Input() selectedStreet = '';
  @ViewChild('chart', { read: ElementRef }) chartRef!: ElementRef;

  stats: FianzaItem[] = [];
  chart!: Chart;
  shouldUpdateChart = false;

  constructor(private http: HttpClient, private alquileresService: AlquileresApiService) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.selectedMunicipality) {
      this.stats = [];
    }

    if (changes.selectedMunicipality || changes.selectedStreet) {
      this.filterStats();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldUpdateChart && this.chartRef) {
      this.updateChart();
      this.shouldUpdateChart = false;
    }
  }

  filterStats(): void {
    if (this.selectedMunicipality && this.selectedStreet) {
      this.alquileresService.fetchStats(this.selectedMunicipality, this.selectedStreet)
        .subscribe((data: FianzaItem[]) => {
          this.stats = data;
          if (this.stats.length > 0) {
            this.shouldUpdateChart = true;
          }
        }, error => {
          console.error('Error fetching data from api.', error);
        });
    }
  }

  updateChart(): void {
    const labelSet = new Set();
    let labels: any = [];
    const dataAux: any = {};
    const dataVivienda: any = [];
    const dataLocales: any = [];

    for (const row of this.stats) {
      if (!dataAux[row.anyo]) {
        labelSet.add(row.anyo);
        dataAux[row.anyo] = {
          vivienda: NaN,
          locales: NaN
        };
      }
      if (row.eslocal === 'Vivienda') {
        dataAux[row.anyo]['vivienda'] = row.mediaRenta;
      } else if (row.eslocal === 'Local') {
        dataAux[row.anyo]['locales'] = row.mediaRenta;
      }
    }
    labels = Array.from(labelSet).sort();

    for (const label of labels) {
      dataVivienda.push(dataAux[label]['vivienda']);
      dataLocales.push(dataAux[label]['locales']);
    }

    const skipped = (ctx: any, value: any) => ctx.p0.skip || ctx.p1.skip ? value : undefined;
    if (this.chart !== undefined) {
      this.chart.destroy();
    }
    const ctx = this.chartRef.nativeElement.getContext('2d');
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Vivienda',
          data: dataVivienda,
          borderColor: 'rgb(255, 99, 132)',
          segment: {
            borderDash: ctx => skipped(ctx, [6, 6]),
          }
        }, {
          label: 'Locales',
          data: dataLocales,
          borderColor: 'rgb(54, 162, 235)',
          segment: {
            borderDash: ctx => skipped(ctx, [6, 6]),
          }
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Renta Media (€)'
            }
          }
        }
      }
    });
  }

}
