// Draws the reach network growing outward on a 2D canvas above the map.
// Each segment is drawn up to the slider time; a segment that is only partly reached is cut
// at the interpolated point along its own coordinates. The map never rotates or tilts, so
// screen = a * mercator + b, refreshed from two projected anchor points on every map render.
import type maplibregl from 'maplibre-gl';
import type { ReachFile } from './data';
import { token } from './theme';

interface Seg {
  ts: number;
  te: number;
  kind: number;
  xy: Float64Array; // mercator x,y pairs (0..1)
  cum: Float64Array; // cumulative length per vertex
}

const mx = (lon: number) => (lon + 180) / 360;
const my = (lat: number) => (180 - (180 / Math.PI) * Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))) / 360;

// line style per kind: road 0, rail 1, bus/boat/cableway straight line 2, walk 3
const STYLE: Record<number, { w: number; dash: number[] }> = {
  0: { w: 0.7, dash: [] },
  1: { w: 1.5, dash: [] },
  2: { w: 0.8, dash: [3, 2.5] },
  3: { w: 0.8, dash: [1, 2] },
};

export class ReachOverlay {
  private canvas: HTMLCanvasElement;
  private g: CanvasRenderingContext2D;
  private segs: Seg[] = [];
  private hub: [number, number] | null = null;
  private t = 0;
  private visible = false;

  constructor(private map: maplibregl.Map, parent: HTMLElement) {
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'reach-canvas';
    this.canvas.setAttribute('aria-hidden', 'true');
    parent.appendChild(this.canvas);
    this.g = this.canvas.getContext('2d')!;
    map.on('render', () => this.draw());
    map.on('resize', () => this.draw());
  }

  setNetwork(file: ReachFile | null) {
    this.segs = [];
    this.hub = null;
    if (file) {
      for (const [ts, te, kind, c] of file.segments) {
        const n = c.length / 2;
        const xy = new Float64Array(c.length);
        const cum = new Float64Array(n);
        for (let k = 0; k < n; k++) {
          xy[2 * k] = mx(c[2 * k]);
          xy[2 * k + 1] = my(c[2 * k + 1]);
          if (k) cum[k] = cum[k - 1] + Math.hypot(xy[2 * k] - xy[2 * k - 2], xy[2 * k + 1] - xy[2 * k - 1]);
        }
        this.segs.push({ ts, te, kind, xy, cum });
      }
      this.segs.sort((a, b) => a.ts - b.ts);
      const first = file.segments.find((s) => s[0] === 0);
      if (first) this.hub = [mx(first[3][0]), my(first[3][1])];
    }
    this.draw();
  }

  setTime(t: number) {
    this.t = t;
    this.draw();
  }

  setVisible(v: boolean) {
    this.visible = v;
    this.draw();
  }

  draw() {
    const m = this.map;
    const el = m.getContainer();
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (this.canvas.width !== Math.round(w * dpr) || this.canvas.height !== Math.round(h * dpr)) {
      this.canvas.width = Math.round(w * dpr);
      this.canvas.height = Math.round(h * dpr);
      this.canvas.style.width = `${w}px`;
      this.canvas.style.height = `${h}px`;
    }
    const g = this.g;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.visible || !this.segs.length) return;

    // affine mercator -> CSS pixels from two anchors
    const A = { lng: 6, lat: 46 };
    const B = { lng: 10, lat: 47.5 };
    const pa = m.project(A);
    const pb = m.project(B);
    const ax = (pb.x - pa.x) / (mx(B.lng) - mx(A.lng));
    const ay = (pb.y - pa.y) / (my(B.lat) - my(A.lat));
    const bx = pa.x - ax * mx(A.lng);
    const by = pa.y - ay * my(A.lat);
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.lineCap = 'round';
    g.lineJoin = 'round';

    const t = this.t;
    const zoomScale = Math.max(0.8, Math.min(2.2, 1 + (m.getZoom() - 7.5) / 3));
    const paths = new Map<number, Path2D>();
    const tips: [number, number][] = [];
    for (const s of this.segs) {
      if (s.ts >= t) break; // sorted by start time
      let p = paths.get(s.kind);
      if (!p) paths.set(s.kind, (p = new Path2D()));
      const n = s.cum.length;
      const xy = s.xy;
      p.moveTo(ax * xy[0] + bx, ay * xy[1] + by);
      if (t >= s.te || s.te <= s.ts) {
        for (let k = 1; k < n; k++) p.lineTo(ax * xy[2 * k] + bx, ay * xy[2 * k + 1] + by);
      } else {
        const L = s.cum[n - 1] * ((t - s.ts) / (s.te - s.ts));
        let k = 1;
        for (; k < n && s.cum[k] <= L; k++) p.lineTo(ax * xy[2 * k] + bx, ay * xy[2 * k + 1] + by);
        if (k < n) {
          const seg = s.cum[k] - s.cum[k - 1];
          const f = seg > 0 ? (L - s.cum[k - 1]) / seg : 0;
          const x = xy[2 * k - 2] + (xy[2 * k] - xy[2 * k - 2]) * f;
          const y = xy[2 * k - 1] + (xy[2 * k + 1] - xy[2 * k - 1]) * f;
          p.lineTo(ax * x + bx, ay * y + by);
          if (s.kind === 1 || s.kind === 0) tips.push([ax * x + bx, ay * y + by]);
        }
      }
    }

    const line = token('--reach-line');
    const casing = token('--reach-casing');
    // casing first (all kinds), then the coloured lines; rail last so it sits on top
    const order = [3, 2, 0, 1].filter((k) => paths.has(k));
    for (const k of order) {
      const st = STYLE[k] ?? STYLE[0];
      g.setLineDash([]);
      g.strokeStyle = casing;
      g.lineWidth = st.w * zoomScale + 1.6;
      if (k === 1) g.stroke(paths.get(k)!);
    }
    for (const k of order) {
      const st = STYLE[k] ?? STYLE[0];
      g.setLineDash(st.dash.map((d) => d * zoomScale));
      g.strokeStyle = line;
      g.lineWidth = st.w * zoomScale;
      g.stroke(paths.get(k)!);
    }
    g.setLineDash([]);
    if (tips.length && tips.length < 4000) {
      g.fillStyle = line;
      const r = 1 * zoomScale;
      g.beginPath();
      for (const [x, y] of tips) {
        g.moveTo(x + r, y);
        g.arc(x, y, r, 0, Math.PI * 2);
      }
      g.fill();
    }
    if (this.hub) {
      const x = ax * this.hub[0] + bx;
      const y = ay * this.hub[1] + by;
      g.beginPath();
      g.arc(x, y, 5.5, 0, Math.PI * 2);
      g.fillStyle = casing;
      g.fill();
      g.beginPath();
      g.arc(x, y, 3.5, 0, Math.PI * 2);
      g.fillStyle = token('--accent');
      g.fill();
    }
  }
}
