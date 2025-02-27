import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AlquileresApiService {

  constructor(private http: HttpClient) { }

  fetchMunicipalities(): Observable<any[]> {
    const URL = `${environment.urlApi}/municipality`;
    return this.http.get<any[]>(URL).pipe(
      catchError(this.handleError)
    );
  }

  fetchStreets(municipality: string): Observable<any[]> {
    const URL = `${environment.urlApi}/municipality/${municipality}/street`;
    return this.http.get<any[]>(URL).pipe(
      catchError(this.handleError)
    );
  }

  fetchResults(municipality: string, street: string): Observable<any[]> {
    const URL = `${environment.urlApi}/municipality/${municipality}/street/${street}`;
    return this.http.get<any[]>(URL).pipe(
      catchError(this.handleError)
    );
  }
  
  private handleError(error: any): Observable<never> {
    // console.error('An error occurred:', error.message);

    return throwError(error.url);
  }
}
