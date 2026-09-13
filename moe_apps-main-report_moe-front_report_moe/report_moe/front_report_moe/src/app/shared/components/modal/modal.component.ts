import {
  Component,
  Input,
  Output,
  EventEmitter,
  ElementRef,
  OnDestroy,
  AfterViewInit,
  inject,
  ViewEncapsulation,
  ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  encapsulation: ViewEncapsulation.None,
  template: `
    <div class="app-modal-host">
      <div class="app-modal-overlay" *ngIf="visible" (click)="onBackdropClick()">
        <div
          class="app-modal-content"
          [class]="'app-modal-' + size"
          (click)="$event.stopPropagation()"
        >
          <div class="app-modal-header">
            <h3>{{ title }}</h3>
            <button type="button" class="app-modal-close-btn" (click)="onClose()">
              <mat-icon>close</mat-icon>
            </button>
          </div>
          <div class="app-modal-body">
            <ng-content></ng-content>
          </div>
          <div class="app-modal-footer">
            <ng-content select="[footer]"></ng-content>
          </div>
        </div>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './modal.component.scss',
})
export class ModalComponent implements AfterViewInit, OnDestroy {
  @Input() title = '';
  @Input() visible = false;
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() closeOnBackdrop = true;
  @Output() close = new EventEmitter<void>();

  private elRef = inject(ElementRef);

  ngAfterViewInit(): void {
    document.body.appendChild(this.elRef.nativeElement);
  }

  ngOnDestroy(): void {
    const el = this.elRef.nativeElement;
    if (el?.parentNode) {
      el.parentNode.removeChild(el);
    }
  }

  onClose(): void {
    this.close.emit();
  }

  onBackdropClick(): void {
    if (this.closeOnBackdrop) {
      this.onClose();
    }
  }
}
