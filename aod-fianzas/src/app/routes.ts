import { Routes } from '@angular/router'
import { MapSearchComponent } from './main/map-search/map-search.component';
import { ListsearchComponent } from './main/listsearch/listsearch.component';


const routeConfig : Routes = [
    { 
        path: '',
        component: MapSearchComponent,
        title: 'Home page'
    },
    { 
        path: 'simple',
        component: ListsearchComponent,
        title: 'Simple Search'
    },
];

export default routeConfig;