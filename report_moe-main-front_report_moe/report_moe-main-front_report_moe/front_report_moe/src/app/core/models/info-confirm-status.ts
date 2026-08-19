/** Matches backend Info.confirmed choices. */
export type InfoConfirmStatus = 'waiting' | 'accept' | 'reject';

export const INFO_STATUS_WAITING: InfoConfirmStatus = 'waiting';
export const INFO_STATUS_ACCEPT: InfoConfirmStatus = 'accept';
export const INFO_STATUS_REJECT: InfoConfirmStatus = 'reject';

export function isInfoAccepted(
  status: InfoConfirmStatus | string | boolean | null | undefined,
): boolean {
  return normalizeInfoConfirmStatus(status) === INFO_STATUS_ACCEPT;
}

export function isInfoRejected(
  status: InfoConfirmStatus | string | boolean | null | undefined,
): boolean {
  return normalizeInfoConfirmStatus(status) === INFO_STATUS_REJECT;
}

export function isInfoWaiting(
  status: InfoConfirmStatus | string | boolean | null | undefined,
): boolean {
  return normalizeInfoConfirmStatus(status) === INFO_STATUS_WAITING;
}

/** Map legacy boolean API values and aliases to canonical status strings. */
export function normalizeInfoConfirmStatus(
  status: InfoConfirmStatus | string | boolean | null | undefined,
): InfoConfirmStatus {
  if (status === true || status === 'true') return INFO_STATUS_ACCEPT;
  if (status === false || status === 'false') return INFO_STATUS_WAITING;
  if (status === 'approved') return INFO_STATUS_ACCEPT;
  if (status === 'rejected') return INFO_STATUS_REJECT;
  if (
    status === INFO_STATUS_ACCEPT ||
    status === INFO_STATUS_REJECT ||
    status === INFO_STATUS_WAITING
  ) {
    return status;
  }
  return INFO_STATUS_WAITING;
}
