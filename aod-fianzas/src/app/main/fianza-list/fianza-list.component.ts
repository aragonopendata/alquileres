import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { AlquileresApiService } from 'src/app/shared/services/alquileres-api.service';
import { FianzaItem } from 'src/app/shared/models/fianza-item.model';
import { Subject, Subscription } from 'rxjs';
import { switchMap, filter } from 'rxjs/operators';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
    selector: 'app-fianza-list',
    templateUrl: './fianza-list.component.html',
    styleUrls: ['./fianza-list.component.scss'],
    imports: [NgFor, NgIf],
    standalone: true
})

export class FianzaListComponent implements OnChanges, OnInit, AfterViewChecked, OnDestroy {

  @Input() selectedMunicipality = '';
  @Input() selectedStreet = '';
  @ViewChild('chart', { read: ElementRef }) chartRef!: ElementRef;

  private _stats: FianzaItem[] = [];
  stats: { anyo: number; minRenta: number; maxRenta: number; mediaRenta: number; eslocal: string; nfianzas: number }[] = [];
  chart!: Chart;
  shouldUpdateChart = false;

  private filterTrigger$ = new Subject<{ municipality: string; street: string }>();
  private subscription!: Subscription;

  constructor(private alquileresService: AlquileresApiService) { }

  private refreshStats(): void {
    this.stats = this._stats.map(item => ({
      anyo: item.anyo,
      minRenta: item.min_renta,
      maxRenta: item.max_renta,
      mediaRenta: item.media_renta,
      eslocal: item.eslocal,
      nfianzas: item.nfianzas
    }));
  }

  ngOnInit(): void {
    this.subscription = this.filterTrigger$.pipe(
      filter(({ municipality, street }) => !!municipality && !!street),
      switchMap(({ municipality, street }) =>
        this.alquileresService.fetchStats(municipality, street)
      )
    ).subscribe({
      next: (data: FianzaItem[]) => {
        this._stats = data;
        this.refreshStats();
        if (this._stats.length > 0) {
          this.shouldUpdateChart = true;
        }
      },
      error: (error) => {
        console.error('Error fetching data from api.', error);
      }
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['selectedMunicipality']) {
      this._stats = [];
      this.refreshStats();
    }

    if (changes['selectedMunicipality'] || changes['selectedStreet']) {
      this.filterStats();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldUpdateChart && this.chartRef) {
      this.updateChart();
      this.shouldUpdateChart = false;
    }
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  filterStats(): void {
    this.filterTrigger$.next({ municipality: this.selectedMunicipality, street: this.selectedStreet });
  }

  updateChart(): void {
    const labelSet = new Set<number>();
    let labels: number[] = [];
    const dataAux: Record<number, { vivienda: number; locales: number }> = {};
    const dataVivienda: (number | typeof NaN)[] = [];
    const dataLocales: (number | typeof NaN)[] = [];

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
