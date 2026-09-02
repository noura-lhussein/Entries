import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  OnDestroy,
  ViewChild,
  effect,
  inject,
  signal,
} from '@angular/core';
import { UntypedFormGroup } from '@angular/forms';
import * as L from 'leaflet';
import {
  Subject,
  Subscription,
  catchError,
  debounceTime,
  distinctUntilChanged,
  merge,
  of,
  switchMap,
  tap,
} from 'rxjs';
import {
  MAP_REGION,
  MAP_TILE_ATTRIBUTION,
  MAP_TILE_URL,
} from '../../../core/config/map-region.config';
import { GeocodingService, type GeocodeResult } from '../../../core/services/geocoding.service';
import { LanguageService } from '../../services/language.service';

const DEFAULT_CENTER: L.LatLngExpression = MAP_REGION.defaultCenter;
const DEFAULT_ZOOM = MAP_REGION.defaultZoom;
const SELECTED_ZOOM = MAP_REGION.selectedZoom;
const COORD_PRECISION = 8;

@Component({
  selector: 'app-form-map-picker',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="field">
      <label *ngIf="label">{{ label }}</label>

      <div
        #mapShell
        class="map-shell"
        [class.is-fullscreen]="fullscreen()"
        [class.is-readonly]="readOnly"
      >
        <div class="search-overlay" *ngIf="!readOnly">
          <span class="search-icon material-icons" aria-hidden="true">search</span>
          <input
            class="search-input"
            type="search"
            dir="auto"
            [placeholder]="searchPlaceholder"
            [value]="searchQuery()"
            (input)="onSearchInput($event)"
            (keydown.enter)="submitSearch($event)"
            (focus)="searchFocused.set(true)"
            (blur)="onSearchBlur()"
            [attr.aria-label]="searchPlaceholder"
            autocomplete="off"
          />
          <ul
            *ngIf="searchFocused() && searchQuery().trim().length >= 2"
            class="search-results"
            role="listbox"
          >
            <li *ngIf="searching()" class="search-status">{{ searchLoadingLabel }}</li>
            <li
              *ngFor="let result of searchResults()"
              class="search-result"
              role="option"
              (mousedown)="selectSearchResult(result)"
            >
              <span class="result-pin material-icons" aria-hidden="true">location_on</span>
              <span class="result-text">{{ shortPlaceName(result.name) }}</span>
            </li>
            <li
              *ngIf="!searching() && searchAttempted() && searchResults().length === 0"
              class="search-status"
            >
              {{ searchNoResultsLabel }}
            </li>
          </ul>
        </div>

        <div class="map-toolbar">
          <button
            type="button"
            class="map-tool-btn"
            *ngIf="hasCoordinates()"
            (click)="focusMarker()"
            [title]="focusMarkerLabel"
          >
            <span class="material-icons" aria-hidden="true">place</span>
            <span class="map-tool-label">{{ focusMarkerLabel }}</span>
          </button>
          <button
            type="button"
            class="map-tool-btn"
            (click)="resetMapView()"
            [title]="resetViewLabel"
          >
            <span class="material-icons" aria-hidden="true">my_location</span>
            <span class="map-tool-label">{{ resetViewLabel }}</span>
          </button>
          <button
            type="button"
            class="map-tool-btn"
            (click)="toggleFullscreen()"
            [title]="fullscreen() ? exitFullscreenLabel : fullscreenLabel"
          >
            <span class="material-icons" aria-hidden="true">
              {{ fullscreen() ? 'fullscreen_exit' : 'fullscreen' }}
            </span>
            <span class="map-tool-label">{{
              fullscreen() ? exitFullscreenLabel : fullscreenLabel
            }}</span>
          </button>
        </div>

        <div class="zoom-lock-hint" *ngIf="zoomLocked()">
          <span class="material-icons" aria-hidden="true">lock</span>
          <span>{{ zoomLockHintLabel }}</span>
        </div>

        <div
          #mapHost
          class="map-host"
          dir="ltr"
          role="application"
          [style.height.px]="mapHeight"
          [style.minHeight.px]="minMapHeight"
          [attr.aria-label]="label"
        ></div>

        <div class="empty-overlay" *ngIf="readOnly && !hasCoordinates()">
          <span class="material-icons" aria-hidden="true">location_off</span>
          <p>{{ emptyCoordinatesLabel }}</p>
        </div>

        <div class="coords-overlay" *ngIf="showCoordinates && hasCoordinates()">
          <span class="coords-chip">
            {{ latitudeLabel }}: <strong>{{ latitudeDisplay() }}</strong>
          </span>
          <span class="coords-chip">
            {{ longitudeLabel }}: <strong>{{ longitudeDisplay() }}</strong>
          </span>
          <button type="button" class="coords-clear" *ngIf="!readOnly" (click)="clearCoordinates()">
            {{ clearLabel }}
          </button>
        </div>
      </div>

      <small *ngIf="hint && !readOnly" class="hint">{{ hint }}</small>
    </div>
  `,
  styleUrl: './form-map-picker.component.scss',
})
export class FormMapPickerComponent implements AfterViewInit, OnDestroy {
  private geocoding = inject(GeocodingService);
  private language = inject(LanguageService);

  private readonly onLanguageChange = effect(() => {
    this.language.lang();
    if (this.mapReady) {
      this.refreshMapSize();
    }
  });

  @Input({ required: true })
  set form(value: UntypedFormGroup) {
    this.formGroup = value;
    this.attachFormListeners();
  }

  @Input() latitudeControl = 'latitude';
  @Input() longitudeControl = 'longitude';
  @Input() label = '';
  @Input() hint = '';
  @Input() latitudeLabel = 'Latitude';
  @Input() longitudeLabel = 'Longitude';
  @Input() clearLabel = 'Clear';
  @Input() searchPlaceholder = 'Search for a city, town, or area…';
  @Input() searchNoResultsLabel = 'No results found';
  @Input() searchLoadingLabel = 'Searching…';
  @Input() resetViewLabel = 'Reset view';
  @Input() focusMarkerLabel = 'Focus location';
  @Input() fullscreenLabel = 'Fullscreen';
  @Input() exitFullscreenLabel = 'Exit fullscreen';
  @Input() emptyCoordinatesLabel = 'No coordinates set for this item';
  @Input() mapHeight = 420;
  @Input() minMapHeight = 280;
  @Input() showCoordinates = true;
  @Input() zoomLockHintLabel = 'Click map to enable zoom';
  @Input()
  set lockZoomUntilMapClick(value: boolean) {
    this._lockZoomUntilMapClick = value;
    this.applyZoomInteractionState();
  }
  get lockZoomUntilMapClick(): boolean {
    return this._lockZoomUntilMapClick;
  }

  private _readOnly = false;
  private _lockZoomUntilMapClick = true;
  @Input()
  set readOnly(value: boolean) {
    this._readOnly = value;
    this.applyReadOnlyState();
  }
  get readOnly(): boolean {
    return this._readOnly;
  }

  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;
  @ViewChild('mapShell', { static: true }) mapShell!: ElementRef<HTMLDivElement>;

  searchQuery = signal('');
  searchResults = signal<GeocodeResult[]>([]);
  searching = signal(false);
  searchAttempted = signal(false);
  searchFocused = signal(false);
  fullscreen = signal(false);
  zoomLocked = signal(false);

  private formGroup?: UntypedFormGroup;
  private map?: L.Map;
  private marker?: L.Marker;
  private coordsSub?: Subscription;
  private searchSub?: Subscription;
  private readonly searchInput$ = new Subject<string>();
  private syncingFromForm = false;
  private mapReady = false;
  private zoomInteractionUnlocked = false;
  private resizeObserver?: ResizeObserver;
  private onFullscreenChange = () => {
    this.fullscreen.set(!!document.fullscreenElement);
    this.refreshMapSize();
  };

  ngAfterViewInit(): void {
    document.addEventListener('fullscreenchange', this.onFullscreenChange);

    requestAnimationFrame(() => {
      this.initMap();
      this.mapReady = true;
      this.attachFormListeners();
      this.syncMarkerFromForm(true);
      this.observeMapResize();
    });

    this.searchSub = this.searchInput$
      .pipe(
        debounceTime(500),
        distinctUntilChanged(),
        tap((query) => {
          if (query.trim().length < 2) {
            this.searchResults.set([]);
            this.searchAttempted.set(false);
            this.searching.set(false);
          }
        }),
        switchMap((query) => {
          if (query.trim().length < 2) {
            return of([]);
          }
          this.searching.set(true);
          this.searchAttempted.set(true);
          return this.geocoding.searchPlaces(query).pipe(
            catchError(() => of([] as GeocodeResult[])),
            tap(() => this.searching.set(false)),
          );
        }),
      )
      .subscribe((results) => this.searchResults.set(results));
  }

  ngOnDestroy(): void {
    document.removeEventListener('fullscreenchange', this.onFullscreenChange);
    this.coordsSub?.unsubscribe();
    this.searchSub?.unsubscribe();
    this.searchInput$.complete();
    this.resizeObserver?.disconnect();
    this.map?.remove();
    this.map = undefined;
    this.marker = undefined;
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchQuery.set(value);
    this.searchInput$.next(value);
  }

  submitSearch(event: Event): void {
    event.preventDefault();
    const first = this.searchResults()[0];
    if (first) {
      this.selectSearchResult(first);
    }
  }

  onSearchBlur(): void {
    setTimeout(() => this.searchFocused.set(false), 150);
  }

  selectSearchResult(result: GeocodeResult): void {
    this.searchFocused.set(false);
    this.searchQuery.set(this.shortPlaceName(result.name));
    this.searchResults.set([]);
    this.setCoordinates(result.latitude, result.longitude, true);
  }

  shortPlaceName(name: string): string {
    const parts = name
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean);
    return parts.slice(0, 3).join('، ') || name;
  }

  resetMapView(): void {
    this.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM);
  }

  focusMarker(): void {
    const lat = this.readLatitude();
    const lng = this.readLongitude();
    if (lat == null || lng == null) return;
    this.flyTo(L.latLng(lat, lng), SELECTED_ZOOM);
  }

  toggleFullscreen(): void {
    const el = this.mapShell.nativeElement;
    if (!document.fullscreenElement) {
      void el.requestFullscreen?.();
    } else {
      void document.exitFullscreen?.();
    }
  }

  hasCoordinates(): boolean {
    return this.readLatitude() != null && this.readLongitude() != null;
  }

  latitudeDisplay(): string {
    const value = this.readLatitude();
    return value == null ? '—' : value.toFixed(COORD_PRECISION);
  }

  longitudeDisplay(): string {
    const value = this.readLongitude();
    return value == null ? '—' : value.toFixed(COORD_PRECISION);
  }

  clearCoordinates(): void {
    if (this.readOnly) return;
    this.latitudeCtrl?.setValue('');
    this.longitudeCtrl?.setValue('');
    if (this.marker) {
      this.marker.remove();
      this.marker = undefined;
    }
    this.flyTo(DEFAULT_CENTER, DEFAULT_ZOOM);
  }

  private get latitudeCtrl() {
    return this.formGroup?.get(this.latitudeControl) ?? null;
  }

  private get longitudeCtrl() {
    return this.formGroup?.get(this.longitudeControl) ?? null;
  }

  private attachFormListeners(): void {
    this.coordsSub?.unsubscribe();
    if (!this.formGroup || !this.mapReady) return;

    const latCtrl = this.formGroup.get(this.latitudeControl);
    const lngCtrl = this.formGroup.get(this.longitudeControl);
    if (!latCtrl || !lngCtrl) return;

    this.coordsSub = merge(latCtrl.valueChanges, lngCtrl.valueChanges).subscribe(() => {
      if (this.syncingFromForm) return;
      this.syncMarkerFromForm();
    });
    this.syncMarkerFromForm(true);
  }

  private initMap(): void {
    if (this.map) return;

    this.map = L.map(this.mapHost.nativeElement, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: MAP_REGION.minZoom,
      maxBounds: MAP_REGION.maxBounds,
      maxBoundsViscosity: 0.85,
      scrollWheelZoom: true,
      zoomControl: false,
    });

    L.tileLayer(MAP_TILE_URL, {
      attribution: MAP_TILE_ATTRIBUTION,
      maxZoom: 19,
      subdomains: 'abcd',
      updateWhenIdle: true,
      keepBuffer: 3,
    }).addTo(this.map);

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);
    L.control.scale({ position: 'bottomleft', metric: true, imperial: false }).addTo(this.map);

    this.map.on('click', (event: L.LeafletMouseEvent) => {
      this.unlockZoomInteraction();
      if (this.readOnly) return;
      this.setCoordinates(event.latlng.lat, event.latlng.lng, true);
    });

    this.applyReadOnlyState();
    this.applyZoomInteractionState();
    this.refreshMapSize();
  }

  private applyReadOnlyState(): void {
    if (!this.map) return;

    if (this.marker) {
      if (this.readOnly) {
        this.marker.dragging?.disable();
      } else {
        this.marker.dragging?.enable();
      }
    }
  }

  private unlockZoomInteraction(): void {
    if (this.zoomInteractionUnlocked) return;
    this.zoomInteractionUnlocked = true;
    this.applyZoomInteractionState();
  }

  private applyZoomInteractionState(): void {
    if (!this.map) return;
    const shouldLock = this.lockZoomUntilMapClick && !this.zoomInteractionUnlocked;
    this.zoomLocked.set(shouldLock);

    if (shouldLock) {
      this.map.scrollWheelZoom.disable();
      this.map.doubleClickZoom.disable();
      this.map.boxZoom.disable();
      this.map.touchZoom.disable();
      this.map.keyboard.disable();
      return;
    }

    this.map.scrollWheelZoom.enable();
    this.map.doubleClickZoom.enable();
    this.map.boxZoom.enable();
    this.map.touchZoom.enable();
    this.map.keyboard.enable();
  }

  private observeMapResize(): void {
    if (typeof ResizeObserver === 'undefined') return;

    this.resizeObserver = new ResizeObserver(() => this.refreshMapSize());
    this.resizeObserver.observe(this.mapHost.nativeElement);
    this.resizeObserver.observe(this.mapShell.nativeElement);
  }

  private refreshMapSize(): void {
    if (!this.map) return;

    const refresh = () => this.map?.invalidateSize({ animate: false, pan: false });
    refresh();
    requestAnimationFrame(refresh);
    setTimeout(refresh, 100);
    setTimeout(refresh, 350);
  }

  private flyTo(center: L.LatLngExpression, zoom: number): void {
    this.map?.flyTo(center, zoom, { duration: 0.75 });
    this.refreshMapSize();
  }

  private syncMarkerFromForm(fitView = false): void {
    const lat = this.readLatitude();
    const lng = this.readLongitude();
    if (lat == null || lng == null) {
      if (this.marker) {
        this.marker.remove();
        this.marker = undefined;
      }
      return;
    }

    const latLng = L.latLng(lat, lng);
    if (!this.marker) {
      this.marker = this.createMarker(latLng).addTo(this.map!);
    } else {
      this.marker.setLatLng(latLng);
    }

    if (fitView) {
      this.flyTo(latLng, SELECTED_ZOOM);
    }
  }

  private setCoordinates(lat: number, lng: number, fitView: boolean): void {
    if (this.readOnly) return;
    const latCtrl = this.latitudeCtrl;
    const lngCtrl = this.longitudeCtrl;
    if (!latCtrl || !lngCtrl) return;
    const normalizedLat = this.roundCoord(lat);
    const normalizedLng = this.roundCoord(lng);

    this.syncingFromForm = true;
    latCtrl.setValue(normalizedLat);
    lngCtrl.setValue(normalizedLng);
    this.syncingFromForm = false;

    const latLng = L.latLng(normalizedLat, normalizedLng);
    if (!this.marker) {
      this.marker = this.createMarker(latLng).addTo(this.map!);
    } else {
      this.marker.setLatLng(latLng);
    }

    if (fitView) {
      this.flyTo(latLng, SELECTED_ZOOM);
    }
  }

  private createMarker(latLng: L.LatLngExpression): L.Marker {
    const icon = L.divIcon({
      className: 'map-picker-marker-wrap',
      html: '<span class="map-picker-marker"></span>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    const marker = L.marker(latLng, { icon, draggable: !this.readOnly });
    if (!this.readOnly) {
      marker.on('dragend', () => {
        const point = marker.getLatLng();
        this.setCoordinates(point.lat, point.lng, false);
      });
    }
    return marker;
  }

  private readLatitude(): number | null {
    return this.parseCoord(this.latitudeCtrl?.value);
  }

  private readLongitude(): number | null {
    return this.parseCoord(this.longitudeCtrl?.value);
  }

  private parseCoord(value: unknown): number | null {
    if (value === '' || value === null || value === undefined) return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  private roundCoord(value: number): number {
    const factor = 10 ** COORD_PRECISION;
    return Math.round(value * factor) / factor;
  }
}
