import { HttpContextToken } from '@angular/common/http';

/** Skip the global overlay loader for this request (local UI handles loading). */
export const SKIP_GLOBAL_LOADING = new HttpContextToken<boolean>(() => false);

/** Force the global overlay even for GET (e.g. long downloads without local UI). */
export const FORCE_GLOBAL_LOADING = new HttpContextToken<boolean>(() => false);
