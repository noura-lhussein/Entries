/** Session debug logging (remove after investigation). */
export function debugLog(
  location: string,
  message: string,
  data: Record<string, unknown>,
  hypothesisId: string,
  runId = 'pre-fix',
): void {
  // #region agent log
  fetch('http://127.0.0.1:7688/ingest/dfa3ea9f-5b72-408f-8326-e6988d563ab7', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'ed8107' },
    body: JSON.stringify({
      sessionId: 'ed8107',
      runId,
      hypothesisId,
      location,
      message,
      data,
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion
}
