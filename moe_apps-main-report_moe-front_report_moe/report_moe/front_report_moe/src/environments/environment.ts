export const environment = {
  production: false,
  // Relative + same-origin: `ng serve` proxies /api to the backend
  // (proxy.conf.json). Keeps the session cookie same-origin and lets Angular's
  // built-in XSRF interceptor attach X-CSRFToken (it skips absolute URLs).
  apiUrl: '/api/v1',
};
