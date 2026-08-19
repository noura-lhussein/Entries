import { Injectable, signal } from '@angular/core';

export type Language = 'en' | 'ar';

const STORAGE_KEY = 'moe_lang';

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private currentLang = signal<Language>(this.readInitial());

  lang = this.currentLang.asReadonly();

  constructor() {
    this.applyToDocument(this.currentLang());
  }

  toggle(): void {
    this.set(this.currentLang() === 'en' ? 'ar' : 'en');
  }

  set(lang: Language): void {
    this.currentLang.set(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    this.applyToDocument(lang);
  }

  private readInitial(): Language {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'ar' ? 'ar' : 'en';
  }

  private applyToDocument(lang: Language): void {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  }
}
