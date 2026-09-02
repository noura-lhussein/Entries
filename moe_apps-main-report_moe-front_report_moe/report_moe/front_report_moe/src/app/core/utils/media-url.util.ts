import { environment } from '../../../environments/environment';

/** Resolve stored `/media/...` paths to an absolute URL for <img> and <a href>. */
export function mediaAbsoluteUrl(relativeOrAbsolute: string): string {
  if (!relativeOrAbsolute) return '';
  if (relativeOrAbsolute.startsWith('http://') || relativeOrAbsolute.startsWith('https://')) {
    return relativeOrAbsolute;
  }
  let base = '';
  if (environment.apiUrl.startsWith('http')) {
    base = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
  } else if (typeof window !== 'undefined') {
    base = window.location.origin;
  }
  const path = relativeOrAbsolute.startsWith('/') ? relativeOrAbsolute : `/${relativeOrAbsolute}`;
  return `${base}${path}`;
}
