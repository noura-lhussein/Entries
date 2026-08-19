import { Component, Input, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { MatIconModule } from '@angular/material/icon';
import { ModalComponent } from '../modal/modal.component';
import { ButtonComponent } from '../button/button.component';
import { TranslationService } from '../../services/translation.service';
import { mediaAbsoluteUrl } from '../../../core/utils/media-url.util';

function asTrimmedString(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'string') return value.trim();
  return String(value).trim();
}

export function isStoredMediaUrl(val: unknown): boolean {
  const s = asTrimmedString(val);
  if (!s) return false;
  return s.startsWith('/media/') || s.startsWith('http://') || s.startsWith('https://');
}

function inferIsImageFromPath(s: string): boolean {
  return /\.(jpg|jpeg|png|gif|webp)(\?|#|$)/i.test(s);
}

function isPdfPath(s: string): boolean {
  return /\.pdf(\?|#|$)/i.test(s);
}

function fileMaterialIcon(path: string): string {
  const lower = path.toLowerCase();
  if (/\.pdf(\?|#|$)/.test(lower)) return 'picture_as_pdf';
  if (/\.(xls|xlsx)(\?|#|$)/.test(lower)) return 'table_chart';
  if (/\.(doc|docx)(\?|#|$)/.test(lower)) return 'description';
  if (/\.zip(\?|#|$)/.test(lower)) return 'folder_zip';
  if (/\.csv(\?|#|$)/.test(lower)) return 'text_snippet';
  if (/\.txt(\?|#|$)/.test(lower)) return 'article';
  return 'insert_drive_file';
}

@Component({
  selector: 'app-stored-media-value',
  standalone: true,
  imports: [CommonModule, MatIconModule, ModalComponent, ButtonComponent],
  template: `
    <span class="plain" *ngIf="mode() === 'empty'">—</span>
    <span class="plain" *ngIf="mode() === 'text'">{{ textValue() }}</span>

    <ng-container *ngIf="mode() === 'media'">
      <button
        type="button"
        class="media-trigger"
        [class.variant-table]="variant === 'table'"
        [class.variant-form]="variant === 'form'"
        (click)="openPreview()"
        [attr.aria-label]="t('builder.preview-open')"
      >
        <img *ngIf="showImageThumb()" [src]="absoluteUrl()" class="thumb" alt="" />
        <mat-icon *ngIf="!showImageThumb()" class="file-icon">{{ fileIcon() }}</mat-icon>
      </button>
    </ng-container>

    <app-modal
      [title]="modalTitle()"
      [visible]="previewOpen()"
      [size]="modalSize()"
      [closeOnBackdrop]="true"
      (close)="closePreview()"
    >
      <img *ngIf="previewKind() === 'image'" [src]="absoluteUrl()" class="preview-img" alt="" />
      <iframe
        *ngIf="previewKind() === 'pdf' && pdfTrustedUrl"
        [src]="pdfTrustedUrl"
        class="preview-frame"
        title="PDF"
      ></iframe>
      <div *ngIf="previewKind() === 'file'" class="preview-file-fallback">
        <mat-icon class="preview-big-icon">{{ fileIcon() }}</mat-icon>
        <p class="preview-hint">{{ t('builder.preview-file-hint') }}</p>
      </div>
      <div footer>
        <app-button
          [label]="t('form.back')"
          variant="ghost"
          (clicked)="closePreview()"
        ></app-button>
        <app-button
          [label]="t('builder.open-in-tab')"
          variant="primary"
          (clicked)="openInNewTab()"
        ></app-button>
      </div>
    </app-modal>
  `,
  styleUrl: './stored-media-value.component.scss',
})
export class StoredMediaValueComponent {
  private translation = inject(TranslationService);
  private sanitizer = inject(DomSanitizer);
  t = (key: string) => this.translation.t(key);

  private _raw = signal<unknown>(null);

  /** Raw value from API / form (path or URL). */
  @Input() set value(v: unknown) {
    this._raw.set(v);
    const s = asTrimmedString(v);
    if (!s || !isStoredMediaUrl(s)) {
      this.previewOpen.set(false);
      this.pdfTrustedUrl = null;
    }
  }

  @Input() variant: 'table' | 'form' = 'table';
  /** When set (form entry), forces image vs generic file before extension guess. */
  @Input() fileKind: 'image' | 'file' | null = null;

  /** Trusted URL for PDF iframe (set when opening preview). */
  pdfTrustedUrl: SafeResourceUrl | null = null;

  textValue = computed(() => asTrimmedString(this._raw()));

  mode = computed<'empty' | 'text' | 'media'>(() => {
    const s = this.textValue();
    if (!s) return 'empty';
    if (isStoredMediaUrl(s)) return 'media';
    return 'text';
  });

  absoluteUrl = computed(() => {
    if (this.mode() !== 'media') return '';
    return mediaAbsoluteUrl(this.textValue());
  });

  showImageThumb = computed(() => {
    if (this.mode() !== 'media') return false;
    if (this.fileKind === 'image') return true;
    if (this.fileKind === 'file') return false;
    return inferIsImageFromPath(this.textValue());
  });

  fileIcon = computed(() => fileMaterialIcon(this.textValue()));

  previewOpen = signal(false);

  modalTitle = computed(() => {
    if (this.previewKind() === 'image') return this.t('builder.preview-image-title');
    if (this.previewKind() === 'pdf') return this.t('builder.preview-pdf-title');
    return this.t('builder.preview-file-title');
  });

  modalSize = computed((): 'small' | 'medium' | 'large' => 'large');

  previewKind = computed<'image' | 'pdf' | 'file'>(() => {
    if (this.mode() !== 'media') return 'file';
    const s = this.textValue();
    if (this.fileKind === 'image' || (this.fileKind !== 'file' && inferIsImageFromPath(s))) {
      return 'image';
    }
    if (isPdfPath(s)) return 'pdf';
    return 'file';
  });

  openPreview(): void {
    if (this.mode() !== 'media') return;
    if (this.previewKind() === 'pdf') {
      this.pdfTrustedUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.absoluteUrl());
    } else {
      this.pdfTrustedUrl = null;
    }
    this.previewOpen.set(true);
  }

  closePreview(): void {
    this.previewOpen.set(false);
    this.pdfTrustedUrl = null;
  }

  openInNewTab(): void {
    const url = this.absoluteUrl();
    if (url) window.open(url, '_blank', 'noopener,noreferrer');
  }
}
