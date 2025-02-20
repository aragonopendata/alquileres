import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LayoutComponent } from '../main/layout/layout.component';
import { HeaderComponent } from '../main/header/header.component';
import { FooterComponent } from '../main/footer/footer.component';
import { MapComponent } from '../main/map/map.component';
import { PopupComponent } from './popup/popup.component';
import { ListsearchComponent } from '../main/listsearch/listsearch.component';



@NgModule({
  declarations: [
    LayoutComponent,
    HeaderComponent,
    FooterComponent,
    MapComponent,
    PopupComponent,
    ListsearchComponent
  ],
  imports: [
    CommonModule
  ],
  exports: [
    LayoutComponent
  ]
})
export class MainModule { }
