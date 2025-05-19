import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FianzaListComponent } from './fianza-list.component';

describe('FianzaListComponent', () => {
  let component: FianzaListComponent;
  let fixture: ComponentFixture<FianzaListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
    imports: [FianzaListComponent]
})
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(FianzaListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
