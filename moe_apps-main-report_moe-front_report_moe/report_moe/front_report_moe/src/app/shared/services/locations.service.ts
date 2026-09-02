import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, type ApiParams } from '../../core/services/api.service';
import type { Paginated } from '../../core/models';
import type { BudgetSelectOption } from '../../features/project-budget/project-budget.models';

export interface LocationOption extends BudgetSelectOption {
  code?: string;
  governorate?: number;
  district?: number;
  subdistrict?: number;
  latitude?: number | string | null;
  longitude?: number | string | null;
}

export interface LocationNode extends LocationOption {
  name_ar?: string;
  name_en?: string;
  is_active?: boolean;
}

@Injectable({ providedIn: 'root' })
export class LocationsService {
  private api = inject(ApiService);
  private base = '/locations';

  listGovernorateOptions(params?: ApiParams): Observable<LocationOption[]> {
    return this.api.get<LocationOption[]>(`${this.base}/governorates/options/`, params);
  }

  listDistrictOptions(params?: ApiParams): Observable<LocationOption[]> {
    return this.api.get<LocationOption[]>(`${this.base}/districts/options/`, params);
  }

  listSubDistrictOptions(params?: ApiParams): Observable<LocationOption[]> {
    return this.api.get<LocationOption[]>(`${this.base}/subdistricts/options/`, params);
  }

  listCommunityOptions(params?: ApiParams): Observable<LocationOption[]> {
    return this.api.get<LocationOption[]>(`${this.base}/communities/options/`, params);
  }

  listGovernorates(params?: ApiParams): Observable<Paginated<LocationNode>> {
    return this.api.get<Paginated<LocationNode>>(`${this.base}/governorates/`, params);
  }

  listDistricts(params?: ApiParams): Observable<Paginated<LocationNode>> {
    return this.api.get<Paginated<LocationNode>>(`${this.base}/districts/`, params);
  }

  listSubDistricts(params?: ApiParams): Observable<Paginated<LocationNode>> {
    return this.api.get<Paginated<LocationNode>>(`${this.base}/subdistricts/`, params);
  }

  listCommunities(params?: ApiParams): Observable<Paginated<LocationNode>> {
    return this.api.get<Paginated<LocationNode>>(`${this.base}/communities/`, params);
  }

  getCommunity(id: number): Observable<{
    id: number;
    subdistrict: number;
    subdistrict_code?: string;
    code?: string;
    district_id: number;
    governorate_id: number;
    latitude?: number | string | null;
    longitude?: number | string | null;
  }> {
    return this.api.get(`${this.base}/communities/${id}/`);
  }
}
