import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, type ApiParams } from '../../core/services/api.service';
import type {
  MasterFkOption,
  MasterListResponse,
  MasterRegistryResponse,
} from './master-data.models';

@Injectable({ providedIn: 'root' })
export class MasterDataService {
  private api = inject(ApiService);
  private base = 'master-data';

  getRegistry(): Observable<MasterRegistryResponse> {
    return this.api.get<MasterRegistryResponse>(`${this.base}/registry/`);
  }

  list(
    slug: string,
    params?: {
      search?: string;
      page?: number;
      page_size?: number;
      sort?: string;
      direction?: string;
      status?: string;
    },
  ): Observable<MasterListResponse> {
    return this.api.get<MasterListResponse>(`${this.base}/${slug}/`, params as ApiParams);
  }

  get(slug: string, pk: string | number): Observable<Record<string, unknown>> {
    return this.api.get<Record<string, unknown>>(`${this.base}/${slug}/${pk}/`);
  }

  create(slug: string, body: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.api.post<Record<string, unknown>>(`${this.base}/${slug}/`, body);
  }

  update(
    slug: string,
    pk: string | number,
    body: Record<string, unknown>,
  ): Observable<Record<string, unknown>> {
    return this.api.patch<Record<string, unknown>>(`${this.base}/${slug}/${pk}/`, body);
  }

  delete(slug: string, pk: string | number): Observable<void> {
    return this.api.delete<void>(`${this.base}/${slug}/${pk}/`);
  }

  options(slug: string): Observable<{ options: MasterFkOption[] }> {
    return this.api.get<{ options: MasterFkOption[] }>(`${this.base}/${slug}/options/`);
  }

  byEntity(entityType: string): Observable<{
    entity_type: string;
    slug: string;
    label_ar: string;
    label_en: string;
    can_write: boolean;
  }> {
    return this.api.get(`${this.base}/by-entity/${entityType}/`);
  }
}
