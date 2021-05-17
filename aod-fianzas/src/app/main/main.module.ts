import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LayoutComponent } from '../main/layout/layout.component';
import { HeaderComponent } from '../main/header/header.component';
import { FooterComponent } from '../main/footer/footer.component';
import { MapComponent } from '../main/map/map.component';



@NgModule({
  declarations: [
    LayoutComponent,
    HeaderComponent,
    FooterComponent,
    MapComponent
  ],
  imports: [
    CommonModule
  ],
  exports: [
    LayoutComponent
  ]
})
export class MainModule { }
