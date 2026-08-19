import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

type ParamValue = string | number | boolean | null | undefined | string[];
export type ApiParams = { [key: string]: ParamValue };

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = environment.apiUrl.replace(/\/$/, '');

  private url(path: string): string {
    return `${this.base}/${path.replace(/^\//, '')}`;
  }

  private buildParams(params?: ApiParams): HttpParams {
    let p = new HttpParams();
    if (!params) return p;
    for (const [key, value] of Object.entries(params)) {
      if (value === null || value === undefined || value === '') continue;
      if (Array.isArray(value)) {
        if (value.length === 0) continue;
        p = p.set(key, value.map((v) => String(v)).join(','));
        continue;
      }
      p = p.set(key, String(value));
    }
    return p;
  }

  get<T>(path: string, params?: ApiParams): Observable<T> {
    return this.http.get<T>(this.url(path), { params: this.buildParams(params) });
  }

  getBlob(path: string, params?: ApiParams): Observable<Blob> {
    return this.http.get(this.url(path), {
      params: this.buildParams(params),
      responseType: 'blob',
    });
  }

  post<T>(path: string, body: unknown, params?: ApiParams): Observable<T> {
    return this.http.post<T>(this.url(path), body, { params: this.buildParams(params) });
  }

  /** Multipart upload; do not set Content-Type (browser sets boundary). */
  postFormData<T>(path: string, body: FormData, params?: ApiParams): Observable<T> {
    return this.http.post<T>(this.url(path), body, { params: this.buildParams(params) });
  }

  put<T>(path: string, body: unknown): Observable<T> {
    return this.http.put<T>(this.url(path), body);
  }

  patch<T>(path: string, body: unknown): Observable<T> {
    return this.http.patch<T>(this.url(path), body);
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(this.url(path));
  }
}
