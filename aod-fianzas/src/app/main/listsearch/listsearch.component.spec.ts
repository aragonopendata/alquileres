import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListsearchComponent } from './listsearch.component';

describe('ListsearchComponent', () => {
  let component: ListsearchComponent;
  let fixture: ComponentFixture<ListsearchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [ListsearchComponent]
})
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ListsearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
