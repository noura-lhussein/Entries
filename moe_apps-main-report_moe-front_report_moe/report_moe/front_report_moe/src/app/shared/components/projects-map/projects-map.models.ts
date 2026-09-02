/** Lean map marker shape — kept in shared to avoid importing feature modules. */
export type ProjectMapStatus = 'draft' | 'active' | 'on_hold' | 'completed' | 'cancelled';

export interface ProjectMapPoint {
  id: number;
  name_ar: string;
  name_en?: string;
  code: string;
  status: ProjectMapStatus | string;
  latitude: number;
  longitude: number;
  community_name?: string;
  governorate_name?: string;
}
