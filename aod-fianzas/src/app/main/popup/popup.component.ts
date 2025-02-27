import { AfterViewInit, Component, ElementRef, Input, OnChanges, OnInit, SimpleChanges, ViewChild } from '@angular/core';
import { FeatureSelect } from 'src/app/shared/models/feature-select.model';
import { PopupInfo } from 'src/app/shared/models/popup-info.model';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
    selector: 'app-popup',
    templateUrl: './popup.component.html',
    styleUrls: ['./popup.component.scss']
})
export class PopupComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() featureSelect!: FeatureSelect;
  @Input() isHide!: boolean;
  @ViewChild('chart', { read: ElementRef }) chartRef!: ElementRef;
  popupInfo: PopupInfo = {
    via_loc: '',
    anyo: 0,
    vivienda_min: '0',
    vivienda_max: '0',
    vivienda_media: '0',
    local_min: '0',
    local_max: '0',
    local_media: '0',
    raw: {}
  };
  chart!: Chart;

  constructor() { }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.featureSelect.currentValue !== undefined) {
      this.updateInfo(changes.featureSelect.currentValue);
      this.updateChart(this.popupInfo.raw);
    }
  }

  updateInfo(featureSelect: FeatureSelect): void {
    const feature = featureSelect.feature;
    const formatter = new Intl.NumberFormat("es-ES", {
      style: "currency",
      currency: "EUR",
      maximumFractionDigits: 0,
    });
    this.popupInfo.via_loc = feature.get('via_loc');
    for (let valor of JSON.parse(feature.get('valores'))) {
      if (valor.anyo >= this.popupInfo.anyo && valor.tipo === 1) {
        this.popupInfo.anyo = valor.anyo;
        this.popupInfo.vivienda_min = valor.min;
        this.popupInfo.vivienda_max = valor.max;
        this.popupInfo.vivienda_media = valor.media;
      } else if (valor.anyo >= this.popupInfo.anyo && valor.tipo === 2) {
        this.popupInfo.anyo = valor.anyo;
        this.popupInfo.local_min = valor.min;
        this.popupInfo.local_max = valor.max;
        this.popupInfo.local_media = valor.media;
      }
    }
    this.popupInfo.vivienda_min = formatter.format(parseFloat(this.popupInfo.vivienda_min));
    this.popupInfo.vivienda_max = formatter.format(parseFloat(this.popupInfo.vivienda_max));
    this.popupInfo.vivienda_media = formatter.format(parseFloat(this.popupInfo.vivienda_media));
    this.popupInfo.local_min = formatter.format(parseFloat(this.popupInfo.local_min));
    this.popupInfo.local_max = formatter.format(parseFloat(this.popupInfo.local_max));
    this.popupInfo.local_media = formatter.format(parseFloat(this.popupInfo.local_media));
    this.popupInfo.raw = JSON.parse(feature.get('valores'));
    this.isHide = false;
  }

  updateChart(data: any): void {
    let labelSet = new Set();
    let labels: any = [];
    let data_aux: any = {};
    let data_vivienda: any = [];
    let data_locales: any = [];

    for (let row of data) {
      if (!data_aux[row.anyo]) {
        labelSet.add(row.anyo);
        data_aux[row.anyo] = {
          vivienda: NaN,
          locales: NaN
        }
      }
      if (row.tipo == 1) {
        data_aux[row.anyo]['vivienda'] = row.media;
      } else {
        data_aux[row.anyo]['locales'] = row.media;
      }
    }
    labels = Array.from(labelSet);

    for (let label of labels) {
      data_vivienda.push(data_aux[label]['vivienda']);
      data_locales.push(data_aux[label]['locales']);
    }

    const skipped = (ctx: any, value: any) => ctx.p0.skip || ctx.p1.skip ? value : undefined;
    if (this.chart !== undefined) {
      this.chart.destroy();
    }
    let ctx = this.chartRef.nativeElement.getContext('2d');
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Vivienda',
          data: data_vivienda,
          borderColor: 'rgb(255, 99, 132)',
          segment: {
            borderDash: ctx => skipped(ctx, [6, 6]),
          }
        }, {
          label: 'Locales',
          data: data_locales,
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
            beginAtZero: true
          }
        }
      }
    });
  }

  onClosePopup(): void {
    this.isHide = true;
  }

}
