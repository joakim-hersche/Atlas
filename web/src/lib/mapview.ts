// MapLibre map without a basemap: the units of one spatial level, lakes and canton outlines from our
// own TopoJSON, plus optional proportional symbols at the units' label points.
// Colours are computed in the app (classification, muting) and handed over per unit as feature-state;
// feature ids are the unit's index in the level's column files.
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { FeatureCollection, Geometry, Point } from 'geojson';
import type { Base, LevelData } from './data';
import type { Display } from './hash';
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

/** D37 / D11: dot pattern for single-seat (majority-election) cantons, distinct from the no-data hatch but of
 *  the same weight: 1 px dots every 5 px (the image is drawn at pixel ratio 2). */
function dotImage(bg: string, dot: string): ImageData {
  const c = document.createElement('canvas');
  c.width = c.height = 10;
  const g = c.getContext('2d')!;
  g.fillStyle = bg;
  g.fillRect(0, 0, 10, 10);
  g.fillStyle = dot;
  g.beginPath();
  g.arc(5, 5, 1, 0, 2 * Math.PI);
  g.fill();
  return g.getImageData(0, 0, 10, 10);
}

/** A small square map button (top right). Used for "fit to Switzerland" (a "CH" label, so it does not
 *  read as fullscreen) and for the fullscreen-map toggle. */
class ButtonControl implements maplibregl.IControl {
  private el: HTMLDivElement | null = null;
  constructor(private cls: string, private onClick: () => void, private label: () => string, private html: () => string, private pressed?: () => boolean) {}
  onAdd() {
    const el = document.createElement('div');
    el.className = `maplibregl-ctrl maplibregl-ctrl-group gb-btn ${this.cls}`;
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'gb-btn-b';
    b.addEventListener('click', () => this.onClick());
    el.appendChild(b);
    this.el = el;
    this.refresh();
    return el;
  }
  /** re-read label and icon (language switch, state change) */
  refresh() {
    const b = this.el?.querySelector('button');
    if (!b) return;
    b.setAttribute('aria-label', this.label());
    b.title = this.label();
    b.innerHTML = this.html();
    if (this.pressed) b.setAttribute('aria-pressed', String(this.pressed()));
  }
  onRemove() {
    this.el?.remove();
    this.el = null;
  }
}

const ICON_FULL =
  '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="square">' +
  '<path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4"/></svg>';
const ICON_EXIT =
  '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="square">' +
  '<path d="M6 2v4H2M14 6h-4V2M10 14v-4h4M2 10h4v4"/></svg>';

/** Bounding box [x0, y0, x1, y1] of a polygon geometry (lon/lat), or null. */
export function geomBounds(g: Geometry | null): [number, number, number, number] | null {
  if (!g) return null;
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : [];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of polys) for (const r of p) for (const [x, y] of r) {
    if (x < x0) x0 = x;
    if (y < y0) y0 = y;
    if (x > x1) x1 = x;
    if (y > y1) y1 = y;
  }
  return Number.isFinite(x0) ? [x0, y0, x1, y1] : null;
}

export interface MapEvents {
  onSelect: (unitIndex: number | null) => void;
  /** U16: a tap or click with the unit under it and the point (the view may snap it to a nearby label point);
   *  when set, it replaces onSelect for clicks */
  onTap?: (unitIndex: number | null, point: { x: number; y: number }) => void;
  onHover?: (unitIndex: number | null, point: { x: number; y: number } | null) => void;
  /** reset button pressed: fit Switzerland (the view knows its padding) */
  onReset?: () => void;
  /** label of the reset button, in the UI language */
  resetLabel?: () => string;
  /** city and lake names toggle (the button is shown when this is set) */
  onLabels?: () => void;
  labelsLabel?: () => string;
  labelsOn?: () => boolean;
  /** fullscreen toggle pressed (the button is shown when this is set) */
  onFull?: () => void;
  /** label of the fullscreen toggle and whether the map is full screen now */
  fullLabel?: () => string;
  isFull?: () => boolean;
}

/** A proportional symbol: unit index, position and radius in px at the reference zoom. */
export interface Symbol {
  i: number;
  lngLat: [number, number];
  r: number;
}

/** Radius multiplier by zoom: symbols grow when zooming in, less than the area does. */
const ZOOM_STOPS: [number, number][] = [[5, 0.6], [7.5, 1], [10, 1.8], [13, 3.2]];
export function zoomScale(z: number): number {
  const s = ZOOM_STOPS;
  if (z <= s[0][0]) return s[0][1];
  for (let k = 1; k < s.length; k++)
    if (z <= s[k][0]) return s[k - 1][1] + ((z - s[k - 1][0]) / (s[k][0] - s[k - 1][0])) * (s[k][1] - s[k - 1][1]);
  return s[s.length - 1][1];
}
const RADIUS = ['interpolate', ['linear'], ['zoom'], ...ZOOM_STOPS.flatMap(([z, f]) => [z, ['*', ['get', 'r'], f]])] as unknown as maplibregl.ExpressionSpecification;

const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] };

export class UnitMap {
  map: maplibregl.Map;
  ready: Promise<void>;
  private n = 0;
  private colour: (string | null | undefined)[] = [];
  private dim: boolean[] = [];
  private sel: number | null = null;
  private hov: number | null = null;
  private isReady = false;
  private level = '';
  private display: Display = 'choropleth';
  private symbolsOn = false;
  private symbolStyle: 'filled' | 'hollow' = 'filled';
  private ctls: ButtonControl[] = [];

  constructor(container: HTMLElement, base: Base, ev: MapEvents, opts: { nav?: boolean } = {}) {
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
    if (ev.onFull) {
      const isFull = ev.isFull ?? (() => false);
      const c = new ButtonControl('gb-full', ev.onFull, ev.fullLabel ?? (() => 'Full-screen map'), () => (isFull() ? ICON_EXIT : ICON_FULL));
      this.ctls.push(c);
      this.map.addControl(c, 'top-right');
    }
    if (ev.onLabels) {
      const on = ev.labelsOn ?? (() => true);
      const c = new ButtonControl('gb-labels', ev.onLabels, ev.labelsLabel ?? (() => 'City and lake names'), () => '<span class="gb-ch" aria-hidden="true">Aa</span>', on);
      this.ctls.push(c);
      this.map.addControl(c, 'top-right');
    }
    if (ev.onReset) {
      const c = new ButtonControl('gb-reset', ev.onReset, ev.resetLabel ?? (() => 'Show all of Switzerland'), () => '<span class="gb-ch" aria-hidden="true">CH</span>');
      this.ctls.push(c);
      this.map.addControl(c, 'top-right');
    }
    this.map.addControl(
      new maplibregl.AttributionControl({ compact: true, customAttribution: 'Boundaries: BFS generalized boundaries' }),
      'bottom-right',
    );

    this.ready = new Promise((resolve) => {
      this.map.on('load', () => {
        this.addLayers(base);
        this.isReady = true;
        // start with the attribution collapsed to its (i) button
        container.querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show');
        resolve();
      });
    });

    const at = (p: maplibregl.Point) => {
      if (!this.isReady) return undefined;
      const layers = this.symbolsOn ? ['sym', 'unit-fill'] : ['unit-fill'];
      const f = this.map.queryRenderedFeatures(p, { layers })[0];
      return f && typeof f.id === 'number' ? f.id : undefined;
    };
    this.map.on('click', (e) => {
      const i = at(e.point) ?? null;
      if (ev.onTap) ev.onTap(i, { x: e.point.x, y: e.point.y });
      else ev.onSelect(i);
    });
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

  private fillColour(): maplibregl.ExpressionSpecification | string {
    if (this.display === 'symbols') return token('--sym-ground');
    return ['coalesce', ['feature-state', 'fc'], token('--nodata-fill')] as unknown as maplibregl.ExpressionSpecification;
  }

  private addLayers(b: Base) {
    const m = this.map;
    m.addSource('units', { type: 'geojson', data: EMPTY, tolerance: 0.25 });
    m.addSource('kt', { type: 'geojson', data: b.kanton, tolerance: 0.25 });
    m.addSource('lakes', { type: 'geojson', data: b.lakes, tolerance: 0.25 });
    m.addSource('sym', { type: 'geojson', data: EMPTY });
    m.addImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')), { pixelRatio: 2 });
    m.addImage('majdots', dotImage(token('--nodata-fill'), token('--nodata-line')), { pixelRatio: 2 });

    m.addLayer({ id: 'unit-fill', type: 'fill', source: 'units', paint: { 'fill-color': this.fillColour(), 'fill-antialias': false } });
    m.addLayer({
      id: 'unit-hatch', type: 'fill', source: 'units',
      paint: { 'fill-pattern': 'hatch', 'fill-opacity': ['case', ['boolean', ['feature-state', 'nd'], false], 1, 0], 'fill-antialias': false },
    });
    m.addLayer({
      id: 'unit-maj', type: 'fill', source: 'units',
      paint: { 'fill-pattern': 'majdots', 'fill-opacity': ['case', ['boolean', ['feature-state', 'mj'], false], 1, 0], 'fill-antialias': false },
    });
    m.addLayer({ id: 'lakes', type: 'fill', source: 'lakes', paint: { 'fill-color': token('--water') } });
    m.addLayer({
      id: 'lakes-line', type: 'line', source: 'lakes',
      paint: { 'line-color': token('--water-line'), 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 10, 1.1] },
    });
    m.addLayer({ id: 'unit-line', type: 'line', source: 'units', paint: { 'line-color': token('--gem-line') } });
    m.addSource('regions', { type: 'geojson', data: EMPTY, tolerance: 0.25 });
    m.addLayer({ id: 'region-line', type: 'line', source: 'regions', paint: { 'line-color': token('--ink'), 'line-width': 0.8, 'line-opacity': 0.7 } });
    m.addLayer({
      id: 'kt-line', type: 'line', source: 'kt',
      paint: { 'line-color': token('--kt-line'), 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 10, 1.6], 'line-opacity': 0.85 },
    });
    // hover and selection: a dark line on a light casing, readable on every class colour
    const on = ['any', ['boolean', ['feature-state', 'sel'], false], ['boolean', ['feature-state', 'hov'], false]];
    m.addLayer({
      id: 'unit-hl-casing', type: 'line', source: 'units',
      paint: { 'line-color': token('--sel-casing'), 'line-width': ['case', on, ['case', ['boolean', ['feature-state', 'sel'], false], 4.5, 3.5], 0] as never },
    });
    m.addLayer({
      id: 'unit-hl', type: 'line', source: 'units',
      paint: { 'line-color': token('--sel-line'), 'line-width': ['case', on, ['case', ['boolean', ['feature-state', 'sel'], false], 2.5, 1.5], 0] as never },
    });
    m.addLayer({
      id: 'sym', type: 'circle', source: 'sym',
      layout: { 'circle-sort-key': ['-', 0, ['get', 'r']], visibility: 'none' },
      paint: { 'circle-radius': RADIUS },
    });
    this.styleUnits();
    this.styleSymbols();
  }

  private styleUnits() {
    const m = this.map;
    if (!m.getLayer('unit-line')) return;
    const gem = this.level === 'gemeinde' || this.level === '';
    m.setPaintProperty('unit-line', 'line-width', gem
      ? ['interpolate', ['linear'], ['zoom'], 6, 0.12, 9, 0.5, 12, 1]
      : ['interpolate', ['linear'], ['zoom'], 6, 0.7, 10, 1.6]);
    m.setPaintProperty('unit-line', 'line-opacity', gem ? ['interpolate', ['linear'], ['zoom'], 6, 0.45, 9, 0.8] : 1);
    m.setPaintProperty('unit-line', 'line-color', this.display === 'symbols' && !gem ? token('--sym-line') : token('--gem-line'));
    m.setPaintProperty('unit-fill', 'fill-color', this.fillColour());
    m.setLayoutProperty('unit-hatch', 'visibility', this.display === 'symbols' ? 'none' : 'visible');
    m.setLayoutProperty('unit-maj', 'visibility', this.display === 'symbols' ? 'none' : 'visible');
  }

  private styleSymbols() {
    const m = this.map;
    if (!m.getLayer('sym')) return;
    const filled = this.symbolStyle === 'filled';
    const sel = ['boolean', ['feature-state', 'sel'], false];
    const hov = ['boolean', ['feature-state', 'hov'], false];
    m.setLayoutProperty('sym', 'visibility', this.symbolsOn ? 'visible' : 'none');
    m.setPaintProperty('sym', 'circle-color', filled
      ? ['coalesce', ['feature-state', 'fc'], token('--nodata-fill')]
      : 'rgba(0,0,0,0)');
    const dim = ['boolean', ['feature-state', 'dim'], false];
    m.setPaintProperty('sym', 'circle-opacity', filled ? (['case', dim, 0.55, 0.92] as never) : 1);
    m.setPaintProperty('sym', 'circle-stroke-opacity', ['case', dim, filled ? 0.5 : 0.22, 1] as never);
    m.setPaintProperty('sym', 'circle-stroke-color', ['case', ['any', sel, hov], token('--sel-line'),
      filled ? (['case', ['boolean', ['feature-state', 'nd'], false], token('--nodata-line'), token('--sym-stroke')]) : token('--ink')] as never);
    m.setPaintProperty('sym', 'circle-stroke-width', ['case', sel, 2.5, hov, 1.5, filled ? 0.6 : 1] as never);
  }

  /** Regional values (D21): municipal borders hidden, the outlines of the native regions drawn instead.
   *  null = normal municipal borders. */
  setRegions(fc: FeatureCollection | null) {
    if (!this.isReady) return;
    (this.map.getSource('regions') as maplibregl.GeoJSONSource).setData(fc ?? EMPTY);
    this.map.setLayoutProperty('unit-line', 'visibility', fc ? 'none' : 'visible');
  }

  /** Show another spatial level (geometry with feature id = unit index). */
  setLevel(ld: LevelData) {
    if (!this.isReady || ld.level === this.level) return;
    this.map.removeFeatureState({ source: 'units' });
    this.map.removeFeatureState({ source: 'sym' });
    (this.map.getSource('units') as maplibregl.GeoJSONSource).setData(ld.geo);
    (this.map.getSource('sym') as maplibregl.GeoJSONSource).setData(EMPTY);
    this.level = ld.level;
    this.n = ld.units.length;
    this.colour = new Array(this.n);
    this.dim = new Array(this.n).fill(false);
    this.sel = null;
    this.hov = null;
    this.#maj = null;
    this.styleUnits();
  }

  setDisplay(d: Display) {
    if (d === this.display) return;
    this.display = d;
    this.styleUnits();
  }

  /** Units drawn within `r` px of a screen point (distinct indices). */
  unitsNear(p: { x: number; y: number }, r: number): number[] {
    if (!this.isReady) return [];
    const fs = this.map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]], { layers: ['unit-fill'] });
    return [...new Set(fs.map((f) => f.id).filter((x): x is number => typeof x === 'number'))];
  }

  /** Proportional symbols (null = none); 'filled' takes the shade colour, 'hollow' is a black ring. */
  setSymbols(symbols: Symbol[] | null, style: 'filled' | 'hollow') {
    if (!this.isReady) return;
    this.symbolsOn = !!symbols && symbols.length > 0;
    this.symbolStyle = style;
    const fc: FeatureCollection<Point> = {
      type: 'FeatureCollection',
      features: (symbols ?? []).map((s) => ({
        type: 'Feature', id: s.i, properties: { r: Math.round(s.r * 10) / 10 }, geometry: { type: 'Point', coordinates: s.lngLat },
      })),
    };
    (this.map.getSource('sym') as maplibregl.GeoJSONSource).setData(fc);
    // feature-state of the new features: colours and flags
    for (const s of symbols ?? []) {
      const c = this.colour[s.i];
      const dim = this.dim[s.i] ?? false;
      this.map.setFeatureState({ source: 'sym', id: s.i }, c ? { fc: c, nd: false, dim } : { fc: null, nd: true, dim });
    }
    if (this.sel !== null) this.map.setFeatureState({ source: 'sym', id: this.sel }, { sel: true });
    this.styleSymbols();
  }

  /** Fill colour per unit (null = no data, hatched) and dimming (filtered out, for the symbols).
   *  Only changed units are sent to MapLibre. */
  setColours(colour: (string | null)[], dim?: Uint8Array) {
    if (!this.isReady || colour.length !== this.n) return;
    for (let i = 0; i < this.n; i++) {
      const c = colour[i];
      const d = dim ? dim[i] === 1 : false;
      if (c !== this.colour[i] || d !== this.dim[i]) {
        const st = c === null ? { fc: null, nd: true, dim: d } : { fc: c, nd: false, dim: d };
        this.map.setFeatureState({ source: 'units', id: i }, st);
        if (this.symbolsOn) this.map.setFeatureState({ source: 'sym', id: i }, st);
        this.colour[i] = c;
        this.dim[i] = d;
      }
    }
  }

  #maj: Uint8Array | null = null;
  /** D37: units of single-seat cantons whose value is kept apart (drawn with the dot pattern). */
  setMajority(mask: Uint8Array | null) {
    if (!this.isReady) return;
    const prev = this.#maj;
    for (let i = 0; i < this.n; i++) {
      const a = prev?.[i] === 1;
      const b = mask?.[i] === 1;
      if (a !== b) this.map.setFeatureState({ source: 'units', id: i }, { mj: b });
    }
    this.#maj = mask;
  }

  private flag(key: 'sel' | 'hov', id: number | null) {
    const cur = key === 'sel' ? this.sel : this.hov;
    if (id === cur) return;
    for (const source of ['units', 'sym']) {
      if (cur !== null) this.map.setFeatureState({ source, id: cur }, { [key]: false });
      if (id !== null) this.map.setFeatureState({ source, id }, { [key]: true });
    }
    if (key === 'sel') this.sel = id;
    else this.hov = id;
  }
  setSelected(i: number | null) {
    if (this.isReady) this.flag('sel', i);
  }
  setHover(i: number | null) {
    if (this.isReady) this.flag('hov', i);
  }

  /** Re-read labels and icons of the map buttons (language switch, fullscreen state). */
  relabel() {
    for (const c of this.ctls) c.refresh();
  }

  /** Re-read the colour tokens. */
  applyTheme() {
    const m = this.map;
    if (!m.getLayer('unit-fill')) return;
    m.setPaintProperty('bg', 'background-color', token('--map-bg'));
    m.setPaintProperty('lakes', 'fill-color', token('--water'));
    m.setPaintProperty('kt-line', 'line-color', token('--kt-line'));
    m.setPaintProperty('unit-hl', 'line-color', token('--sel-line'));
    m.setPaintProperty('unit-hl-casing', 'line-color', token('--sel-casing'));
    m.updateImage('hatch', hatchImage(token('--nodata-fill'), token('--nodata-line')));
    this.styleUnits();
    this.styleSymbols();
  }

  /** Fit the view to one geometry (a place opened with 'show on map', a tapped ranking row). */
  fitGeometry(g: Geometry, padding: maplibregl.PaddingOptions, opts: { animate?: boolean; maxZoom?: number } = {}) {
    const b = geomBounds(g);
    if (b) this.fitBox(b, padding, opts);
  }

  /** Fit a lon/lat box. */
  fitBox(b: [number, number, number, number], padding: maplibregl.PaddingOptions, opts: { animate?: boolean; maxZoom?: number } = {}) {
    this.map.fitBounds(b, { padding, maxZoom: opts.maxZoom ?? 10.5, animate: !!opts.animate, duration: opts.animate ? 500 : 0 });
  }

  /** Centre on a unit if it is outside the visible area. */
  reveal(lngLat: [number, number]) {
    const b = this.map.getBounds();
    if (!b.contains(lngLat)) this.map.easeTo({ center: lngLat, duration: 400 });
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
