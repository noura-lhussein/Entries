import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { ApiService } from './api.service';

export interface GeocodeResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
}

@Injectable({ providedIn: 'root' })
export class GeocodingService {
  private api = inject(ApiService);

  searchPlaces(query: string): Observable<GeocodeResult[]> {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      return of([]);
    }
    return this.api.get<GeocodeResult[]>('/geocode/search/', { q: trimmed });
  }
}
