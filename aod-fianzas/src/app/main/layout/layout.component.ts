import { Component } from '@angular/core';
import { FooterComponent } from '../footer/footer.component';
import { RouterModule

 } from '@angular/router';
@Component({
    selector: 'app-layout',
    templateUrl: './layout.component.html',
    styleUrls: ['./layout.component.scss'],
    imports: [FooterComponent, RouterModule]
})
export class LayoutComponent {

}
