/**
 * Map region presets — change ACTIVE_MAP_REGION to switch country defaults.
 *
 * Customizable per region:
 * - defaultCenter / defaultZoom: initial map view
 * - selectedZoom: zoom when a point is chosen
 * - geocode.countryCode: Nominatim country filter (ISO 3166-1 alpha-2)
 * - geocode.viewbox: search bias (minLon,maxLat,maxLon,minLat)
 */
export const MAP_REGIONS = {
  syria: {
    label: 'Syria',
    defaultCenter: [33.5138, 36.2765] as [number, number],
    defaultZoom: 7,
    selectedZoom: 14,
    minZoom: 6,
    maxBounds: [
      [32.2, 35.5],
      [37.4, 42.5],
    ] as [[number, number], [number, number]],
    geocode: {
      countryCode: 'sy',
      viewbox: '35.72,37.32,42.35,32.31',
    },
  },
  palestine: {
    label: 'Palestine',
    defaultCenter: [31.9522, 35.2332] as [number, number],
    defaultZoom: 9,
    selectedZoom: 14,
    minZoom: 7,
    maxBounds: [
      [31.2, 34.2],
      [32.6, 35.6],
    ] as [[number, number], [number, number]],
    geocode: {
      countryCode: 'ps',
      viewbox: '34.17,32.55,35.55,31.25',
    },
  },
} as const;

/** Cleaner base map tiles (CARTO, OSM data). */
export const MAP_TILE_URL =
  'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
export const MAP_TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

export type MapRegionKey = keyof typeof MAP_REGIONS;

/** Switch map/search defaults by changing this key only. */
export const ACTIVE_MAP_REGION: MapRegionKey = 'syria';

export const MAP_REGION = MAP_REGIONS[ACTIVE_MAP_REGION];
