import { Injectable, inject } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { DialogComponent, DialogConfig } from '../components/dialog/dialog.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {
  private dialog = inject(MatDialog);

  confirm(config: Partial<DialogConfig> = {}): Promise<boolean> {
    const dialogConfig: DialogConfig = {
      title: 'تأكيد',
      message: 'هل أنت متأكد؟',
      confirmLabel: 'تأكيد',
      cancelLabel: 'إلغاء',
      showCancel: true,
      type: 'info',
      ...config
    };

    const dialogRef = this.dialog.open(DialogComponent, {
      data: dialogConfig,
      width: '400px',
      disableClose: false,
      hasBackdrop: true
    });

    return dialogRef.afterClosed().toPromise().then(result => !!result);
  }

  success(message: string, title = 'نجح'): Promise<boolean> {
    return this.confirm({
      title,
      message,
      type: 'success',
      icon: 'check_circle',
      confirmLabel: 'موافق',
      showCancel: false
    });
  }

  error(message: string, title = 'خطأ'): Promise<boolean> {
    return this.confirm({
      title,
      message,
      type: 'error',
      icon: 'error',
      confirmLabel: 'موافق',
      showCancel: false
    });
  }

  warning(message: string, title = 'تحذير'): Promise<boolean> {
    return this.confirm({
      title,
      message,
      type: 'warning',
      icon: 'warning',
      confirmLabel: 'موافق',
      showCancel: false
    });
  }

  info(message: string, title = 'معلومة'): Promise<boolean> {
    return this.confirm({
      title,
      message,
      type: 'info',
      icon: 'info',
      confirmLabel: 'موافق',
      showCancel: false
    });
  }

  delete(itemName: string = 'العنصر'): Promise<boolean> {
    return this.confirm({
      title: 'حذف',
      message: `هل تريد حذف ${itemName}؟ لا يمكن التراجع عن هذا الإجراء.`,
      type: 'error',
      icon: 'delete',
      confirmLabel: 'حذف',
      cancelLabel: 'إلغاء'
    });
  }
}
