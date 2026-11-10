// MapLibre map without a basemap: municipalities, lakes and canton outlines from our own TopoJSON.
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { StartData } from './data';
import { ramp, token } from './theme';

export const CH_BOUNDS: [number, number, number, number] = [5.956, 45.818, 10.492, 47.808];

function hatchImage(bg: string, line: string): ImageData {
  const size = 8;
  const c = document.createElement('canvas');
  c.width = c.height = size * 2;
  const g = c.getContext('2d')!;
  g.fillStyle = bg;
  g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = line;
  g.lineWidth = 2;
  g.beginPath();
  // 45° lines that tile seamlessly
  for (let k = -1; k <= 2; k++) {
    g.moveTo(k * size - 1, c.height + 1);
    g.lineTo(k * size + c.height + 1, -1);
  }
  g.stroke();
  return g.getImageData(0, 0, c.width, c.height);
}

export class MapView {
  map: maplibregl.Map;
  ready: Promise<void>;
  private ids: number[]; // feature id per core unit index
  private colour: Int8Array;
  private dim: Float32Array;
  private sel: number | null = null;

  constructor(container: HTMLElement, data: StartData, onSelect: (unitIndex: number | null) => void) {
    const index = new Map(data.core.units.map((u, i) => [Number(u), i]));
    this.ids = data.core.units.map(Number);
    this.colour = new Int8Array(this.ids.length).fill(-2);
    this.dim = new Float32Array(this.ids.length).fill(-1);

    this.map = new maplibregl.Map({
      container,
      style: { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': token('--map-bg') } }] },
      bounds: CH_BOUNDS,
      fitBoundsOptions: { padding: 12 },
      maxBounds: [-4, 36, 24, 56],
      minZoom: 5.5,
      maxZoom: 13,
      dragRotate: false,
      pitchWithRotate: false,
      touchPitch: false,
      attributionControl: false,
      renderWorldCopies: false,
    });
    this.map.touchZoomRotate.disableRotation();
    this.map.keyboard.disableRotation();
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    this.map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: 'Boundaries: BFS – generalized boundaries; data: see card' }),
      'bottom-right',
    );

    this.ready = new Promise((resolve) => {
      this.map.on('load', () => {
        this.addLayers(data);
        resolve();
      });
    });

    this.map.on('click', (e) => {
      const f = this.map.queryRenderedFeatures(e.point, { layers: ['gem-fill'] })[0];
      const i = f ? index.get(Number(f.id)) : undefined;
      onSelect(i ?? null);
    });
    this.map.on('mousemove', 'gem-fill', () => (this.map.getCanvas().style.cursor = 'pointer'));
    this.map.on('mouseleave', 'gem-fill', () => (this.map.getCanvas().style.cursor = ''));
  }

  private addLayers(d: StartData) {
    const m = this.map;
    m.addSource('gem', { type: 'geojson', data: d.gemeinde, tolerance: 0.25 });
    m.addSource('kt', { type: 'geojson', data: d.kanton, tolerance: 0.25 });
    m.addSource('lakes', { type: 'geojson', data: d.lakes, tolerance: 0.25 });
    m.addImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')), { pixelRatio: 2 });

    const r = ramp();
    m.addLayer({
      id: 'gem-fill', type: 'fill', source: 'gem',
      paint: {
        'fill-color': ['match', ['coalesce', ['feature-state', 'c'], -1], 0, r[0], 1, r[1], 2, r[2], 3, r[3], 4, r[4], token('--nodata-fill')],
        'fill-antialias': false,
      },
    });
    m.addLayer({
      id: 'gem-hatch', type: 'fill', source: 'gem',
      paint: { 'fill-pattern': 'hatch', 'fill-opacity': ['case', ['<', ['coalesce', ['feature-state', 'c'], 0], 0], 1, 0], 'fill-antialias': false },
    });
    m.addLayer({
      id: 'gem-veil', type: 'fill', source: 'gem',
      paint: { 'fill-color': token('--map-bg'), 'fill-opacity': ['coalesce', ['feature-state', 'dim'], 0], 'fill-antialias': false },
    });
    m.addLayer({ id: 'lakes', type: 'fill', source: 'lakes', paint: { 'fill-color': token('--water') } });
    m.addLayer({
      id: 'gem-line', type: 'line', source: 'gem',
      paint: {
        'line-color': token('--gem-line'),
        'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.15, 9, 0.6, 12, 1.2],
        'line-opacity': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 9, 0.8],
      },
    });
    m.addLayer({
      id: 'kt-line', type: 'line', source: 'kt',
      paint: { 'line-color': token('--kt-line'), 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.8, 10, 2] },
    });
    m.addLayer({
      id: 'gem-sel', type: 'line', source: 'gem',
      paint: {
        'line-color': token('--sel-line'),
        'line-width': ['case', ['boolean', ['feature-state', 'sel'], false], 2.5, 0],
      },
    });
  }

  /** Re-read the colour tokens (light/dark switch). */
  applyTheme() {
    const m = this.map;
    if (!m.getLayer('gem-fill')) return;
    const r = ramp();
    m.setPaintProperty('bg', 'background-color', token('--map-bg'));
    m.setPaintProperty('gem-fill', 'fill-color', ['match', ['coalesce', ['feature-state', 'c'], -1], 0, r[0], 1, r[1], 2, r[2], 3, r[3], 4, r[4], token('--nodata-fill')]);
    m.setPaintProperty('gem-veil', 'fill-color', token('--map-bg'));
    m.setPaintProperty('lakes', 'fill-color', token('--water'));
    m.setPaintProperty('gem-line', 'line-color', token('--gem-line'));
    m.setPaintProperty('kt-line', 'line-color', token('--kt-line'));
    m.setPaintProperty('gem-sel', 'line-color', token('--sel-line'));
    m.updateImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')));
  }

  /** Colour index per unit (-1 = no data, hatched). Only changed units are sent to MapLibre. */
  setColours(colour: Int8Array) {
    for (let i = 0; i < this.ids.length; i++) {
      if (colour[i] !== this.colour[i]) {
        this.map.setFeatureState({ source: 'gem', id: this.ids[i] }, { c: colour[i] });
        this.colour[i] = colour[i];
      }
    }
  }

  /** Veil opacity per unit (0 = full colour). */
  setDim(dim: Float32Array) {
    for (let i = 0; i < this.ids.length; i++) {
      if (dim[i] !== this.dim[i]) {
        this.map.setFeatureState({ source: 'gem', id: this.ids[i] }, { dim: dim[i] });
        this.dim[i] = dim[i];
      }
    }
  }

  setSelected(i: number | null) {
    const id = i === null ? null : this.ids[i];
    if (id === this.sel) return;
    if (this.sel !== null) this.map.setFeatureState({ source: 'gem', id: this.sel }, { sel: false });
    if (id !== null) this.map.setFeatureState({ source: 'gem', id }, { sel: true });
    this.sel = id;
  }
}
