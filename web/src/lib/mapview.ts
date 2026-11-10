// MapLibre map without a basemap: municipalities, lakes and canton outlines from our own TopoJSON.
// Colours are computed in the app (classification, muting) and handed over per unit as feature-state.
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { StartData } from './data';
import { token } from './theme';

export const CH_BOUNDS: [number, number, number, number] = [5.956, 45.818, 10.492, 47.808];

function hatchImage(bg: string, line: string): ImageData {
  const size = 6;
  const c = document.createElement('canvas');
  c.width = c.height = size * 2;
  const g = c.getContext('2d')!;
  g.fillStyle = bg;
  g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = line;
  g.lineWidth = 1.5;
  g.beginPath();
  // 45° lines that tile seamlessly
  for (let k = -1; k <= 2; k++) {
    g.moveTo(k * size - 1, c.height + 1);
    g.lineTo(k * size + c.height + 1, -1);
  }
  g.stroke();
  return g.getImageData(0, 0, c.width, c.height);
}

export interface MapEvents {
  onSelect: (unitIndex: number | null) => void;
  onHover?: (unitIndex: number | null, point: { x: number; y: number } | null) => void;
}

export class MapView {
  map: maplibregl.Map;
  ready: Promise<void>;
  private ids: number[]; // feature id per core unit index
  private colour: (string | null | undefined)[];
  private sel: number | null = null;
  private hov: number | null = null;
  private isReady = false;

  constructor(container: HTMLElement, data: StartData, ev: MapEvents, opts: { nav?: boolean } = {}) {
    const index = new Map(data.core.units.map((u, i) => [Number(u), i]));
    this.ids = data.core.units.map(Number);
    this.colour = new Array(this.ids.length);

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
    if (opts.nav !== false) this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    this.map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: 'Boundaries: BFS generalized boundaries' }),
      'bottom-right',
    );

    this.ready = new Promise((resolve) => {
      this.map.on('load', () => {
        this.addLayers(data);
        this.isReady = true;
        resolve();
      });
    });

    const at = (p: maplibregl.Point) => {
      if (!this.isReady) return undefined;
      const f = this.map.queryRenderedFeatures(p, { layers: ['gem-fill'] })[0];
      return f ? index.get(Number(f.id)) : undefined;
    };
    this.map.on('click', (e) => ev.onSelect(at(e.point) ?? null));
    if (ev.onHover) {
      const onHover = ev.onHover;
      this.map.on('mousemove', (e) => {
        const i = at(e.point);
        this.map.getCanvas().style.cursor = i === undefined ? '' : 'pointer';
        onHover(i ?? null, i === undefined ? null : { x: e.point.x, y: e.point.y });
      });
      this.map.on('mouseout', () => onHover(null, null));
    }
  }

  private fillColour() {
    return ['coalesce', ['feature-state', 'fc'], token('--nodata-fill')] as unknown as maplibregl.ExpressionSpecification;
  }

  private addLayers(d: StartData) {
    const m = this.map;
    m.addSource('gem', { type: 'geojson', data: d.gemeinde, tolerance: 0.25 });
    m.addSource('kt', { type: 'geojson', data: d.kanton, tolerance: 0.25 });
    m.addSource('lakes', { type: 'geojson', data: d.lakes, tolerance: 0.25 });
    m.addImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')), { pixelRatio: 2 });

    m.addLayer({ id: 'gem-fill', type: 'fill', source: 'gem', paint: { 'fill-color': this.fillColour(), 'fill-antialias': false } });
    m.addLayer({
      id: 'gem-hatch', type: 'fill', source: 'gem',
      paint: { 'fill-pattern': 'hatch', 'fill-opacity': ['case', ['boolean', ['feature-state', 'nd'], false], 1, 0], 'fill-antialias': false },
    });
    m.addLayer({ id: 'lakes', type: 'fill', source: 'lakes', paint: { 'fill-color': token('--water') } });
    m.addLayer({
      id: 'gem-line', type: 'line', source: 'gem',
      paint: {
        'line-color': token('--gem-line'),
        'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.12, 9, 0.5, 12, 1],
        'line-opacity': ['interpolate', ['linear'], ['zoom'], 6, 0.45, 9, 0.8],
      },
    });
    m.addLayer({
      id: 'kt-line', type: 'line', source: 'kt',
      paint: { 'line-color': token('--kt-line'), 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 10, 1.6], 'line-opacity': 0.85 },
    });
    // hover and selection: a dark line on a light casing, readable on every class colour
    const on = ['any', ['boolean', ['feature-state', 'sel'], false], ['boolean', ['feature-state', 'hov'], false]];
    m.addLayer({
      id: 'gem-hl-casing', type: 'line', source: 'gem',
      paint: { 'line-color': token('--sel-casing'), 'line-width': ['case', on, ['case', ['boolean', ['feature-state', 'sel'], false], 4.5, 3.5], 0] as never },
    });
    m.addLayer({
      id: 'gem-hl', type: 'line', source: 'gem',
      paint: { 'line-color': token('--sel-line'), 'line-width': ['case', on, ['case', ['boolean', ['feature-state', 'sel'], false], 2.2, 1.4], 0] as never },
    });
  }

  /** Re-read the colour tokens (light/dark switch). */
  applyTheme() {
    const m = this.map;
    if (!m.getLayer('gem-fill')) return;
    m.setPaintProperty('bg', 'background-color', token('--map-bg'));
    m.setPaintProperty('gem-fill', 'fill-color', this.fillColour());
    m.setPaintProperty('lakes', 'fill-color', token('--water'));
    m.setPaintProperty('gem-line', 'line-color', token('--gem-line'));
    m.setPaintProperty('kt-line', 'line-color', token('--kt-line'));
    m.setPaintProperty('gem-hl', 'line-color', token('--sel-line'));
    m.setPaintProperty('gem-hl-casing', 'line-color', token('--sel-casing'));
    m.updateImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')));
  }

  /** Fill colour per unit (null = no data, hatched). Only changed units are sent to MapLibre. */
  setColours(colour: (string | null)[]) {
    for (let i = 0; i < this.ids.length; i++) {
      const c = colour[i];
      if (c !== this.colour[i]) {
        this.map.setFeatureState({ source: 'gem', id: this.ids[i] }, c === null ? { fc: null, nd: true } : { fc: c, nd: false });
        this.colour[i] = c;
      }
    }
  }

  private flag(key: 'sel' | 'hov', i: number | null) {
    const id = i === null ? null : this.ids[i];
    const cur = key === 'sel' ? this.sel : this.hov;
    if (id === cur) return;
    if (cur !== null) this.map.setFeatureState({ source: 'gem', id: cur }, { [key]: false });
    if (id !== null) this.map.setFeatureState({ source: 'gem', id }, { [key]: true });
    if (key === 'sel') this.sel = id;
    else this.hov = id;
  }
  setSelected(i: number | null) {
    this.flag('sel', i);
  }
  setHover(i: number | null) {
    this.flag('hov', i);
  }

  /** Screen position of a unit's label point (for tooltips driven from another view). */
  project(lngLat: [number, number]) {
    return this.map.project(lngLat);
  }
}

/** Keep two maps on the same centre and zoom, both ways, without feedback loops. */
export function syncCameras(a: maplibregl.Map, b: maplibregl.Map): () => void {
  let busy = false;
  const follow = (src: maplibregl.Map, dst: maplibregl.Map) => () => {
    if (busy) return;
    busy = true;
    dst.jumpTo({ center: src.getCenter(), zoom: src.getZoom() });
    busy = false;
  };
  const ab = follow(a, b);
  const ba = follow(b, a);
  a.on('move', ab);
  b.on('move', ba);
  ab();
  return () => {
    a.off('move', ab);
    b.off('move', ba);
  };
}
