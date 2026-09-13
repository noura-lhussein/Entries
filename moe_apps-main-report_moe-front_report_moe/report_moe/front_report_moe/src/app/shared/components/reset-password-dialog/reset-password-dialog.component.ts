import { Component, Inject, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-reset-password-dialog',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatDialogModule, MatIconModule],
  template: `
    <div class="dialog-wrapper" dir="rtl">
      <div class="dialog-header">
        <div class="header-content">
          <div class="icon-circle">
            <mat-icon>lock_reset</mat-icon>
          </div>
          <h2>إعادة تعيين كلمة المرور</h2>
        </div>
        <button type="button" class="close-btn" (click)="cancel()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="dialog-body" [formGroup]="form">
        <p class="username-hint">
          المستخدم: <strong>{{ data.username }}</strong>
        </p>

        <div class="field-wrap">
          <label>كلمة المرور الجديدة</label>
          <input
            type="password"
            formControlName="password"
            placeholder="أدخل كلمة المرور الجديدة"
            class="input"
            [class.error]="form.get('password')?.invalid && form.get('password')?.touched"
          />
          @if (form.get('password')?.hasError('required') && form.get('password')?.touched) {
            <span class="field-error">هذا الحقل مطلوب</span>
          }
          @if (form.get('password')?.hasError('minlength') && form.get('password')?.touched) {
            <span class="field-error">الحد الأدنى 6 أحرف</span>
          }
        </div>

        <div class="field-wrap">
          <label>تأكيد كلمة المرور</label>
          <input
            type="password"
            formControlName="confirm"
            placeholder="أعد إدخال كلمة المرور"
            class="input"
            [class.error]="form.hasError('mismatch') && form.get('confirm')?.touched"
          />
          @if (form.hasError('mismatch') && form.get('confirm')?.touched) {
            <span class="field-error">كلمتا المرور غير متطابقتين</span>
          }
        </div>
      </div>

      <div class="dialog-footer">
        <button type="button" class="btn-cancel" (click)="cancel()">إلغاء</button>
        <button type="button" class="btn-save" (click)="submit()">حفظ</button>
      </div>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './reset-password-dialog.component.scss',
})
export class ResetPasswordDialogComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group(
    {
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirm: ['', Validators.required],
    },
    {
      validators: (g) =>
        g.get('password')?.value !== g.get('confirm')?.value ? { mismatch: true } : null,
    },
  );

  constructor(
    private dialogRef: MatDialogRef<ResetPasswordDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { userId: number; username: string },
  ) {}

  submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) return;
    this.dialogRef.close(this.form.get('password')!.value);
  }

  cancel(): void {
    this.dialogRef.close(null);
  }
}
