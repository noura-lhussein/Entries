import { Injectable, computed, effect, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { AuthService } from './auth.service';
import { LanguageService } from '../../shared/services/language.service';
import { TranslationService } from '../../shared/services/translation.service';

@Injectable({ providedIn: 'root' })
export class AppBrandingService {
  private auth = inject(AuthService);
  private title = inject(Title);
  private language = inject(LanguageService);
  private translation = inject(TranslationService);

  isBudgetBranding = computed(() => this.auth.isBudgetOnlyUser());

  documentTitle = computed(() =>
    this.translation.t(this.isBudgetBranding() ? 'app.title.budget' : 'app.title.default'),
  );

  brandAr = computed(() =>
    this.isBudgetBranding()
      ? this.translation.t('app.brand.budget')
      : this.translation.t('app.brand.default.ar'),
  );

  brandEn = computed(() =>
    this.isBudgetBranding()
      ? this.translation.t('app.brand.budget')
      : this.translation.t('app.brand.default.en'),
  );

  showBrandAr = computed(() => !this.isBudgetBranding());

  footerText = computed(() =>
    this.translation.t(this.isBudgetBranding() ? 'app.footer.budget' : 'app.footer.default'),
  );

  constructor() {
    effect(() => {
      this.auth.currentUser();
      this.auth.isBudgetOnlyUser();
      this.language.lang();
      this.title.setTitle(this.documentTitle());
    });
  }

  apply(): void {
    this.title.setTitle(this.documentTitle());
  }
}
