import { Component } from '@angular/core';
import { LayoutComponent } from "./main/layout/layout.component"

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss'],
    imports: [LayoutComponent]
})
export class AppComponent {
  title = 'aod-fianzas';
}
