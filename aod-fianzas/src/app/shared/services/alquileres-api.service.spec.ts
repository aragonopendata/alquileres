import { TestBed } from '@angular/core/testing';

import { AlquileresApiService } from './alquileres-api.service';

describe('AlquileresApiService', () => {
  let service: AlquileresApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AlquileresApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
