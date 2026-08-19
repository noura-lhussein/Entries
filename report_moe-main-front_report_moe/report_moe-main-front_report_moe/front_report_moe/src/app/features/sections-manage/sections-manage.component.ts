import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { BuilderService, MainSection, SubMainSection } from '../../core/services/builder.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../shared/services/toast.service';
import { TranslationService } from '../../shared/services/translation.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { ModalComponent } from '../../shared/components/modal/modal.component';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { DialogService } from '../../shared/services/dialog.service';
import { FormInputComponent } from '../../shared/components/form-input/form-input.component';
import {
  FormSelectComponent,
  type SelectOption,
} from '../../shared/components/form-select/form-select.component';
import {
  AssignedUsersDialogComponent,
} from '../../shared/components/assigned-users-dialog/assigned-users-dialog.component';
import {
  TableComponent,
  type TableAction,
  type TableColumn,
  type TableRow,
} from '../../shared/components/table/table.component';

@Component({
  selector: 'app-sections-manage',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    PageHeaderComponent,
    ModalComponent,
    ButtonComponent,
    FormInputComponent,
    FormSelectComponent,
    TableComponent,
  ],
  template: `
    <div class="page-container">
      <div class="page-chrome">
        <app-page-header
          [title]="t('sections-manage.title')"
          [description]="t('sections-manage.description')"
        ></app-page-header>
      </div>

      <div class="layout">
        <section class="card">
          <div class="card-chrome">
            <div class="card-header">
              <h3>{{ t('sections-manage.main-title') }}</h3>
              <app-button
                [label]="t('sections-manage.add-main')"
                [icon]="'add'"
                variant="primary"
                (clicked)="openMainDialog()"
              ></app-button>
            </div>
          </div>
          <div class="card-body list" *ngIf="mainSections().length > 0; else emptyMain">
            <div
              *ngFor="let main of mainSections()"
              class="list-item"
              [class.active]="selectedMainId() === main.id"
              (click)="selectMain(main.id)"
            >
              <span>{{ main.name }}</span>
              <div class="row-actions">
                <button
                  class="icon-btn edit"
                  (click)="openMainDialog(main); $event.stopPropagation()"
                >
                  <mat-icon>edit</mat-icon>
                </button>
                <button
                  class="icon-btn delete"
                  (click)="deleteMain(main); $event.stopPropagation()"
                >
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </div>
          </div>
          <ng-template #emptyMain>
            <div class="empty">{{ t('sections-manage.empty-main') }}</div>
          </ng-template>
        </section>

        <section class="card">
          <div class="card-chrome">
            <div class="card-header">
              <h3>{{ t('sections-manage.sub-title') }}</h3>
              <app-button
                [label]="t('sections-manage.add-sub')"
                [icon]="'add'"
                variant="primary"
                (clicked)="openSubDialog()"
              ></app-button>
            </div>

            <div class="filter-row">
              <input
                type="text"
                [ngModel]="subFilter()"
                (ngModelChange)="subFilter.set($event)"
                [placeholder]="t('sections-manage.sub-filter-placeholder')"
              />
            </div>
          </div>

          <div class="card-body table-wrap" *ngIf="subSections().length > 0; else emptySub">
            <app-table
              [data]="subTableData()"
              [columns]="subTableColumns()"
              [actions]="subTableActions()"
              [paginator]="true"
              [pageSize]="10"
              [emptyMessage]="t('sections-manage.empty-sub')"
              [scroll]="{ maxHeight: '100%', vertical: 'auto' }"
              (actionClicked)="onSubTableAction($event)"
            ></app-table>
          </div>
          <ng-template #emptySub>
            <div class="empty">{{ t('sections-manage.empty-sub') }}</div>
          </ng-template>
        </section>
      </div>
    </div>

    <app-modal
      [title]="editingMainId() ? t('sections-manage.edit-main') : t('sections-manage.add-main')"
      [visible]="mainDialogOpen()"
      [size]="'small'"
      (close)="closeMainDialog()"
    >
      <app-form-input
        [label]="t('sections-manage.main-title')"
        [placeholder]="t('sections-manage.main-title')"
        [(ngModel)]="mainFormName"
      ></app-form-input>
      <div class="actions" footer>
        <app-button
          [label]="t('form.back')"
          variant="ghost"
          (clicked)="closeMainDialog()"
        ></app-button>
        <app-button [label]="t('form.save')" variant="primary" (clicked)="saveMain()"></app-button>
      </div>
    </app-modal>

    <app-modal
      [title]="editingSubId() ? t('sections-manage.edit-sub') : t('sections-manage.add-sub')"
      [visible]="subDialogOpen()"
      [size]="'small'"
      (close)="closeSubDialog()"
    >
      <app-form-input
        [label]="t('sections-manage.sub-name')"
        [placeholder]="t('sections-manage.sub-name')"
        [(ngModel)]="subFormName"
      ></app-form-input>
      <app-form-select
        [label]="t('sections-manage.main-link')"
        [placeholder]="t('sections-manage.select-main')"
        [options]="mainSectionOptions()"
        [(ngModel)]="subFormMainId"
        (ngModelChange)="onSubFormMainChange()"
      ></app-form-select>
      <app-form-select
        [label]="t('sections-manage.parent-link')"
        [placeholder]="t('sections-manage.select-parent')"
        [options]="parentSectionOptions()"
        [(ngModel)]="subFormParentId"
      ></app-form-select>
      <div class="actions" footer>
        <app-button
          [label]="t('form.back')"
          variant="ghost"
          (clicked)="closeSubDialog()"
        ></app-button>
        <app-button [label]="t('form.save')" variant="primary" (clicked)="saveSub()"></app-button>
      </div>
    </app-modal>
  `,
  styleUrl: './sections-manage.component.scss',
})
export class SectionsManageComponent implements OnInit {
  private builder = inject(BuilderService);
  private auth = inject(AuthService);
  private toast = inject(ToastService);
  private dialog = inject(DialogService);
  private matDialog = inject(MatDialog);
  private translation = inject(TranslationService);
  t = (key: string) => this.translation.t(key);

  mainSections = signal<MainSection[]>([]);
  subSections = signal<SubMainSection[]>([]);
  selectedMainId = signal<number | null>(null);
  subFilter = signal('');

  mainDialogOpen = signal(false);
  subDialogOpen = signal(false);
  editingMainId = signal<number | null>(null);
  editingSubId = signal<number | null>(null);
  mainFormName = '';
  subFormName = '';
  subFormMainId: number | null = null;
  subFormParentId: number | null = null;
  mainSectionOptions = computed<SelectOption[]>(() =>
    this.mainSections().map((main) => ({ value: main.id, label: main.name })),
  );
  parentSectionOptions = computed<SelectOption[]>(() => {
    const mainId = this.subFormMainId;
    const editingId = this.editingSubId();
    const roots: SelectOption[] = [
      { value: null, label: this.t('sections-manage.select-parent') },
    ];
    if (!mainId) return roots;
    const options = this.subSections()
      .filter((s: any) => this.getSubMainId(s) === mainId && s.id !== editingId)
      .map((s: any) => ({
        value: s.id,
        label: s.parent_name ? `${s.parent_name} / ${s.name}` : s.name,
      }));
    return [...roots, ...options];
  });
  subTableColumns = computed<TableColumn[]>(() => [
    { key: 'name', label: this.t('sections-manage.sub-name'), sortable: true },
    { key: 'parent_name', label: this.t('sections-manage.parent-link') },
    { key: 'main_section_name', label: this.t('sections-manage.main-link') },
    { key: 'node_kind', label: this.t('sections-manage.leaf') },
  ]);
  subTableActions = computed<TableAction[]>(() => {
    const actions: TableAction[] = [];
    if (this.auth.isAdmin()) {
      actions.push({
        type: 'assignees',
        label: this.t('sections-manage.assigned-users'),
        icon: 'group',
        color: 'primary',
      });
    }
    actions.push(
      { type: 'edit', label: this.t('users.edit'), icon: 'edit', color: 'edit' },
      { type: 'delete', label: this.t('users.delete'), icon: 'delete', color: 'delete' },
    );
    return actions;
  });
  subTableData = computed<TableRow[]>(() =>
    this.filteredSubSections().map((sub: any) => ({
      ...sub,
      id: sub.id,
      parent_name: sub.parent_name || '—',
      main_section_name:
        this.mainSections().find((m) => m.id === this.getSubMainId(sub))?.name || '—',
      node_kind: sub.is_leaf === false ? this.t('sections-manage.branch') : this.t('sections-manage.leaf'),
    })),
  );

  filteredSubSections = computed(() => {
    const mainId = this.selectedMainId();
    const q = this.subFilter().trim().toLowerCase();
    return this.subSections().filter((s: any) => {
      const inMain = !mainId || this.getSubMainId(s) === mainId;
      if (!inMain) return false;
      if (!q) return true;
      return String(s.name || '')
        .toLowerCase()
        .includes(q);
    });
  });

  ngOnInit(): void {
    this.loadAll();
  }

  private loadAll(): void {
    this.builder.getMainSections().subscribe({
      next: (res) => this.mainSections.set(res.results || []),
    });
    this.builder.getSubMainSections().subscribe({
      next: (res) => this.subSections.set(res.results || []),
    });
  }

  selectMain(id: number): void {
    this.selectedMainId.set(this.selectedMainId() === id ? null : id);
  }

  getSubMainId(sub: SubMainSection): number | null {
    const s: any = sub;
    return s.main_section_id ?? s.main_section ?? null;
  }

  openMainDialog(main?: MainSection): void {
    this.editingMainId.set(main?.id ?? null);
    this.mainFormName = main?.name ?? '';
    this.mainDialogOpen.set(true);
  }

  closeMainDialog(): void {
    this.mainDialogOpen.set(false);
    this.mainFormName = '';
    this.editingMainId.set(null);
  }

  saveMain(): void {
    const name = this.mainFormName.trim();
    if (!name) return;
    const id = this.editingMainId();
    const req = id
      ? this.builder.updateMainSection(id, { name })
      : this.builder.createMainSection({ name });
    req.subscribe({
      next: () => {
        this.toast.success(this.t('user-data.update-success'));
        this.closeMainDialog();
        this.loadAll();
      },
      error: () => this.toast.error(this.t('user-data.update-error')),
    });
  }

  async deleteMain(main: MainSection): Promise<void> {
    const confirmed = await this.dialog.delete(main.name || this.t('sections-manage.main-title'));
    if (!confirmed) return;
    this.builder.deleteMainSection(main.id).subscribe({
      next: () => {
        this.toast.success(this.t('user-data.delete-success'));
        if (this.selectedMainId() === main.id) this.selectedMainId.set(null);
        this.loadAll();
      },
      error: (err) => this.toast.error(this.deleteErrorMessage(err)),
    });
  }

  openSubDialog(sub?: SubMainSection): void {
    const s: any = sub;
    this.editingSubId.set(sub?.id ?? null);
    this.subFormName = sub?.name ?? '';
    this.subFormMainId = s ? this.getSubMainId(s) : this.selectedMainId();
    this.subFormParentId = s?.parent ?? null;
    this.subDialogOpen.set(true);
  }

  onSubFormMainChange(): void {
    this.subFormParentId = null;
  }

  closeSubDialog(): void {
    this.subDialogOpen.set(false);
    this.subFormName = '';
    this.subFormMainId = null;
    this.subFormParentId = null;
    this.editingSubId.set(null);
  }

  saveSub(): void {
    const name = this.subFormName.trim();
    const mainId = this.subFormMainId;
    if (!name || !mainId) return;
    const id = this.editingSubId();
    const parentId = this.subFormParentId || null;
    const req = id
      ? this.builder.updateSubMainSection(id, {
          name,
          main_section_id: mainId,
          parent_id: parentId,
        })
      : this.builder.createSubMainSection({
          name,
          main_section_id: mainId,
          parent_id: parentId,
        });
    req.subscribe({
      next: () => {
        this.toast.success(this.t('user-data.update-success'));
        this.closeSubDialog();
        this.loadAll();
      },
      error: () => this.toast.error(this.t('user-data.update-error')),
    });
  }

  async deleteSub(sub: SubMainSection): Promise<void> {
    const confirmed = await this.dialog.delete(sub.name || this.t('sections-manage.sub-title'));
    if (!confirmed) return;
    this.builder.deleteSubMainSection(sub.id).subscribe({
      next: () => {
        this.toast.success(this.t('user-data.delete-success'));
        this.loadAll();
      },
      error: (err) => this.toast.error(this.deleteErrorMessage(err)),
    });
  }

  private deleteErrorMessage(err: { error?: { detail?: unknown } }): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    return this.t('builder.delete-blocked-has-data');
  }

  onSubTableAction(event: { type: string; row: TableRow }): void {
    if (event.type === 'assignees') {
      this.openAssignedUsers(event.row as SubMainSection);
      return;
    }
    if (event.type === 'edit') {
      this.openSubDialog(event.row as SubMainSection);
      return;
    }
    if (event.type === 'delete') {
      this.deleteSub(event.row as SubMainSection);
    }
  }

  openAssignedUsers(sub: SubMainSection): void {
    this.builder.getSubSectionAssignedUsers(sub.id).subscribe({
      next: (users) => {
        this.matDialog.open(AssignedUsersDialogComponent, {
          data: {
            contextLabel: sub.name,
            users: users || [],
          },
          width: 'min(560px, 94vw)',
          maxHeight: '90vh',
        });
      },
      error: () => this.toast.error(this.t('assigned-users.load-error')),
    });
  }
}
