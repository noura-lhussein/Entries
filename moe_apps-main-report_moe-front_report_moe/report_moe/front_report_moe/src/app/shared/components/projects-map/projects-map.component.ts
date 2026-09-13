import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
  signal,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import {
  MAP_REGION,
  MAP_TILE_ATTRIBUTION,
  MAP_TILE_URL,
} from '../../../core/config/map-region.config';
import type { ProjectMapPoint } from './projects-map.models';

const STATUS_COLORS: Record<string, string> = {
  draft: '#64748b',
  active: '#16a34a',
  on_hold: '#d97706',
  completed: '#4f46e5',
  cancelled: '#dc2626',
};

@Component({
  selector: 'app-projects-map',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="projects-map"
      [class.is-fullscreen]="fullscreen()"
      [class.is-zoom-locked]="zoomLocked()"
    >
      <div class="map-toolbar">
        @if (lockZoomUntilMapClick) {
          <button
            type="button"
            class="map-tool-btn"
            (click)="toggleZoomLock()"
            [title]="zoomLocked() ? unlockZoomLabel : relockZoomLabel"
          >
            <span class="material-icons" aria-hidden="true">
              {{ zoomLocked() ? 'lock_open' : 'lock' }}
            </span>
            <span class="map-tool-label">{{
              zoomLocked() ? unlockZoomLabel : relockZoomLabel
            }}</span>
          </button>
        }
        <button
          type="button"
          class="map-tool-btn"
          (click)="fitAll()"
          [disabled]="!points.length"
          [title]="fitAllLabel"
        >
          <span class="material-icons" aria-hidden="true">my_location</span>
          <span class="map-tool-label">{{ fitAllLabel }}</span>
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

      @if (zoomLocked()) {
        <div class="zoom-lock-hint">
          <span class="material-icons" aria-hidden="true">lock</span>
          <span>{{ zoomLockHintLabel }}</span>
        </div>
      }

      <div #mapHost class="map-host" dir="ltr" [style.height.px]="mapHeight"></div>

      @if (!points.length) {
        <div class="map-empty">
          <p>{{ emptyLabel }}</p>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './projects-map.component.scss',
})
export class ProjectsMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  @Input() points: ProjectMapPoint[] = [];
  @Input() mapHeight = 420;
  @Input() statusLabelFn: (status: string) => string = (s) => s;
  @Input() openProjectLabel = 'View project';
  @Input() fitAllLabel = 'Fit all';
  @Input() fullscreenLabel = 'Fullscreen';
  @Input() exitFullscreenLabel = 'Exit fullscreen';
  @Input() emptyLabel = 'No projects with coordinates';
  /** Same behavior as project form map: disable scroll/touch zoom until the map is clicked. */
  @Input() lockZoomUntilMapClick = true;
  @Input() zoomLockHintLabel = 'Click the map to enable zoom';
  @Input() unlockZoomLabel = 'Enable zoom';
  @Input() relockZoomLabel = 'Lock zoom';

  @Output() projectOpen = new EventEmitter<number>();

  fullscreen = signal(false);
  zoomLocked = signal(false);

  private map?: L.Map;
  private layer = L.layerGroup();
  private mapReady = false;
  private zoomInteractionUnlocked = false;
  private readonly onFullscreenChange = () => {
    this.fullscreen.set(!!document.fullscreenElement);
    setTimeout(() => this.map?.invalidateSize(), 120);
  };

  ngAfterViewInit(): void {
    this.initMap();
    this.renderPoints();
    document.addEventListener('fullscreenchange', this.onFullscreenChange);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['points'] && this.mapReady) {
      this.renderPoints();
    }
    if (changes['lockZoomUntilMapClick'] && this.mapReady) {
      this.applyZoomInteractionState();
    }
  }

  ngOnDestroy(): void {
    document.removeEventListener('fullscreenchange', this.onFullscreenChange);
    this.map?.remove();
    this.map = undefined;
  }

  fitAll(): void {
    if (!this.map || !this.points.length) return;
    const bounds = L.latLngBounds(
      this.points.map((p) => [p.latitude, p.longitude] as [number, number]),
    );
    this.map.fitBounds(bounds.pad(0.15), { maxZoom: 12 });
  }

  toggleZoomLock(): void {
    if (!this.lockZoomUntilMapClick) return;
    if (this.zoomLocked()) {
      this.unlockZoomInteraction();
      return;
    }
    this.relockZoomInteraction();
  }

  toggleFullscreen(): void {
    const root = this.mapHost.nativeElement.closest('.projects-map') as HTMLElement | null;
    if (!root) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void root.requestFullscreen();
    }
  }

  private initMap(): void {
    if (this.map) return;

    this.map = L.map(this.mapHost.nativeElement, {
      center: MAP_REGION.defaultCenter,
      zoom: MAP_REGION.defaultZoom,
      minZoom: MAP_REGION.minZoom,
      maxBounds: MAP_REGION.maxBounds,
      maxBoundsViscosity: 0.85,
      scrollWheelZoom: false,
      zoomControl: false,
    });

    L.tileLayer(MAP_TILE_URL, {
      attribution: MAP_TILE_ATTRIBUTION,
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(this.map);

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);
    this.layer.addTo(this.map);

    this.map.on('click', () => this.unlockZoomInteraction());
    this.map.on('dragstart', () => this.unlockZoomInteraction());

    this.mapReady = true;
    this.applyZoomInteractionState();
    setTimeout(() => this.map?.invalidateSize(), 80);
  }

  private unlockZoomInteraction(): void {
    if (this.zoomInteractionUnlocked) return;
    this.zoomInteractionUnlocked = true;
    this.applyZoomInteractionState();
  }

  private relockZoomInteraction(): void {
    this.zoomInteractionUnlocked = false;
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

  private renderPoints(): void {
    if (!this.map || !this.mapReady) return;

    this.layer.clearLayers();

    for (const point of this.points) {
      if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) continue;

      const color = STATUS_COLORS[point.status] ?? '#64748b';
      const marker = L.circleMarker([point.latitude, point.longitude], {
        radius: 8,
        color: '#fff',
        weight: 2,
        fillColor: color,
        fillOpacity: 0.92,
      });

      const popup = L.DomUtil.create('div', 'project-map-popup');
      popup.innerHTML = `
        <strong class="popup-title"></strong>
        <div class="popup-meta"></div>
        <div class="popup-status"></div>
        <button type="button" class="popup-open"></button>
      `;
      (popup.querySelector('.popup-title') as HTMLElement).textContent =
        point.name_ar || point.name_en || point.code;
      (popup.querySelector('.popup-meta') as HTMLElement).textContent = [
        point.code,
        point.community_name || point.governorate_name,
      ]
        .filter(Boolean)
        .join(' · ');
      (popup.querySelector('.popup-status') as HTMLElement).textContent = this.statusLabelFn(
        point.status,
      );
      const openBtn = popup.querySelector('.popup-open') as HTMLButtonElement;
      openBtn.textContent = this.openProjectLabel;
      openBtn.addEventListener('click', (event) => {
        event.preventDefault();
        this.unlockZoomInteraction();
        this.projectOpen.emit(point.id);
      });

      marker.bindPopup(popup, { maxWidth: 260 });
      marker.on('click', () => this.unlockZoomInteraction());
      this.layer.addLayer(marker);
    }

    if (this.points.length) {
      this.fitAll();
    } else {
      this.map.setView(MAP_REGION.defaultCenter, MAP_REGION.defaultZoom);
    }
  }
}
