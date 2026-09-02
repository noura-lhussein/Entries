import { CommonModule } from '@angular/common';
import { Component, Input, OnDestroy, forwardRef, inject, signal } from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';
import { Subscription } from 'rxjs';
import { FormSelectComponent } from '../form-select/form-select.component';
import { TranslationService } from '../../services/translation.service';
import { LocationsService } from '../../services/locations.service';

@Component({
  selector: 'app-location-picker',
  standalone: true,
  imports: [CommonModule, FormsModule, FormSelectComponent],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => LocationPickerComponent),
      multi: true,
    },
  ],
  template: `
    <div class="location-picker">
      <app-form-select
        [label]="t('locations.governorate')"
        [placeholder]="t('budget.reference.select-placeholder')"
        [required]="required"
        [options]="governorateOptions()"
        [ngModel]="governorateId()"
        (ngModelChange)="onGovernorateChange($event)"
        [disabled]="disabled"
      />
      <app-form-select
        [label]="t('locations.district')"
        [placeholder]="t('budget.reference.select-placeholder')"
        [required]="required"
        [options]="districtOptions()"
        [ngModel]="districtId()"
        (ngModelChange)="onDistrictChange($event)"
        [disabled]="disabled || !governorateId()"
      />
      <app-form-select
        [label]="t('locations.subdistrict')"
        [placeholder]="t('budget.reference.select-placeholder')"
        [required]="required"
        [options]="subdistrictOptions()"
        [ngModel]="subdistrictId()"
        (ngModelChange)="onSubdistrictChange($event)"
        [disabled]="disabled || !districtId()"
      />
      <app-form-select
        [label]="t('locations.community')"
        [placeholder]="t('budget.reference.select-placeholder')"
        [required]="required"
        [options]="communityOptions()"
        [ngModel]="communityId()"
        (ngModelChange)="onCommunityChange($event)"
        [disabled]="disabled || !subdistrictId()"
      />
    </div>
  `,
  styles: [
    `
      .location-picker {
        display: contents;
      }
    `,
  ],
})
export class LocationPickerComponent implements ControlValueAccessor, OnDestroy {
  private locations = inject(LocationsService);
  private translation = inject(TranslationService);
  private subs = new Subscription();

  @Input() required = false;
  @Input() disabled = false;

  t = (key: string) => this.translation.t(key);

  governorateId = signal<number | null>(null);
  districtId = signal<number | null>(null);
  subdistrictId = signal<number | null>(null);
  communityId = signal<number | null>(null);

  governorateOptions = signal<{ value: number; label: string }[]>([]);
  districtOptions = signal<{ value: number; label: string }[]>([]);
  subdistrictOptions = signal<{ value: number; label: string }[]>([]);
  communityOptions = signal<{ value: number; label: string }[]>([]);

  private onChange: (value: number | null) => void = () => undefined;
  onTouched: () => void = () => undefined;

  constructor() {
    this.subs.add(
      this.locations.listGovernorateOptions().subscribe({
        next: (items) =>
          this.governorateOptions.set(items.map((item) => ({ value: item.id, label: item.name }))),
      }),
    );
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe();
  }

  writeValue(value: number | null): void {
    this.communityId.set(value);
    if (!value) {
      this.resetHierarchy();
      return;
    }
    this.hydrateFromCommunity(value);
  }

  registerOnChange(fn: (value: number | null) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  onGovernorateChange(value: number | null): void {
    this.governorateId.set(value);
    this.districtId.set(null);
    this.subdistrictId.set(null);
    this.communityId.set(null);
    this.districtOptions.set([]);
    this.subdistrictOptions.set([]);
    this.communityOptions.set([]);
    this.emit(null);
    if (!value) return;
    this.subs.add(
      this.locations.listDistrictOptions({ governorate: value }).subscribe({
        next: (items) =>
          this.districtOptions.set(items.map((item) => ({ value: item.id, label: item.name }))),
      }),
    );
  }

  onDistrictChange(value: number | null): void {
    this.districtId.set(value);
    this.subdistrictId.set(null);
    this.communityId.set(null);
    this.subdistrictOptions.set([]);
    this.communityOptions.set([]);
    this.emit(null);
    if (!value) return;
    this.subs.add(
      this.locations.listSubDistrictOptions({ district: value }).subscribe({
        next: (items) =>
          this.subdistrictOptions.set(items.map((item) => ({ value: item.id, label: item.name }))),
      }),
    );
  }

  onSubdistrictChange(value: number | null): void {
    this.subdistrictId.set(value);
    this.communityId.set(null);
    this.communityOptions.set([]);
    this.emit(null);
    if (!value) return;
    this.loadCommunities(value, null);
  }

  onCommunityChange(value: number | null): void {
    this.communityId.set(value);
    this.emit(value);
  }

  private hydrateFromCommunity(communityId: number): void {
    this.subs.add(
      this.locations.getCommunity(communityId).subscribe({
        next: (detail) => {
          this.governorateId.set(detail.governorate_id);
          this.districtId.set(detail.district_id);
          this.subdistrictId.set(detail.subdistrict);
          this.locations.listDistrictOptions({ governorate: detail.governorate_id }).subscribe({
            next: (districts) =>
              this.districtOptions.set(
                districts.map((item) => ({ value: item.id, label: item.name })),
              ),
          });
          this.locations.listSubDistrictOptions({ district: detail.district_id }).subscribe({
            next: (subs) =>
              this.subdistrictOptions.set(
                subs.map((item) => ({ value: item.id, label: item.name })),
              ),
          });
          this.loadCommunities(detail.subdistrict, communityId);
        },
      }),
    );
  }

  private loadCommunities(subdistrictId: number, selectId: number | null): void {
    this.subs.add(
      this.locations.listCommunityOptions({ subdistrict: subdistrictId }).subscribe({
        next: (items) => {
          this.communityOptions.set(items.map((item) => ({ value: item.id, label: item.name })));
          if (selectId) {
            this.communityId.set(selectId);
          }
        },
      }),
    );
  }

  private resetHierarchy(): void {
    this.governorateId.set(null);
    this.districtId.set(null);
    this.subdistrictId.set(null);
    this.districtOptions.set([]);
    this.subdistrictOptions.set([]);
    this.communityOptions.set([]);
  }

  private emit(value: number | null): void {
    this.onChange(value);
    this.onTouched();
  }
}
