export interface ClientLocation {
  client_latitude: number;
  client_longitude: number;
}

/** Best-effort browser geolocation; returns null if denied or unavailable. */
export function tryGetClientLocation(): Promise<ClientLocation | null> {
  return new Promise((resolve) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          client_latitude: position.coords.latitude,
          client_longitude: position.coords.longitude,
        });
      },
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 5000, maximumAge: 120_000 },
    );
  });
}
