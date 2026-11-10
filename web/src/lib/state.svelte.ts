// Shared view state (Svelte 5 runes), mirrored in the URL hash (lib/hash.ts).
// Every view and page reads and writes `app`; the hash is written by syncHash() (called once by App).
// Later pages (profile, compare places, search, sources) add a route name and read their own keys
// from app.params, or navigate with app.go('profile', { id: '261' }).
import type { Method } from './classify';
import {
  DEFAULT_HUB, DEFAULT_LEVEL, DEFAULT_METRIC, parseHash, readHash, storeLang, writeHash, type Display, type Filter, type Lang, type ReachMode, type ViewState,
} from './hash';

export class AppState {
  route = $state('map');
  level = $state(DEFAULT_LEVEL);
  metric = $state(DEFAULT_METRIC);
  metricB = $state<string | null>(null);
  size = $state<string | null>(null);
  display = $state<Display>('choropleth');
  cls = $state<Method>('quantile');
  year = $state<string | null>(null);
  filters = $state<Filter[]>([]);
  hub = $state(DEFAULT_HUB);
  reach = $state<ReachMode>('off');
  t = $state(60);
  /** selected unit id at the current level */
  sel = $state<string | null>(null);
  /** open tab of the side column / phone sheet */
  tab = $state<string | null>(null);
  params = $state<Record<string, string>>({});
  lang = $state<Lang>('en');
  only = $state(false);
  /** one-line note after a level switch replaced a metric that does not exist there (not in the hash);
   *  `prev` is the view before the switch, for "switch back" */
  levelNote = $state<{ text: string; level: string; metric: string; prev: { level: string; metric: string; metricB: string | null; size: string | null } } | null>(null);
  /** counts state loads from the URL (initial and every hashchange), so the shell can check the new state */
  loads = $state(0);
  /** fit the map to the selected unit once when the map view opens (set by 'show on map') */
  focusSel = false;
  /** reach animation running (the hash is not written meanwhile) */
  playing = $state(false);
  /** bare '#word' preset from the initial link (consumed by the compare view) */
  preset: string | null = null;

  constructor(v: ViewState) {
    this.load(v);
  }

  load(v: ViewState) {
    this.route = v.route;
    this.level = v.level;
    this.metric = v.metric ?? DEFAULT_METRIC;
    this.metricB = v.metricB;
    this.size = v.size;
    this.display = v.display;
    this.cls = v.cls;
    this.year = v.year;
    this.filters = v.filters;
    this.hub = v.hub;
    this.reach = v.reach;
    this.t = v.t;
    this.sel = v.sel;
    this.tab = v.tab;
    this.params = v.params;
    this.lang = v.lang;
    this.only = v.only;
    this.preset = v.preset;
    this.loads++;
  }

  snapshot(): Omit<ViewState, 'preset'> {
    return {
      route: this.route, level: this.level, metric: this.metric, metricB: this.metricB, size: this.size,
      display: this.display, cls: this.cls, year: this.year, filters: $state.snapshot(this.filters) as Filter[],
      hub: this.hub, reach: this.reach, t: this.t, sel: this.sel, tab: this.tab, lang: this.lang, only: this.only, params: { ...this.params },
    };
  }

  /** Switch route (page); extra keys go to params. */
  go(route: string, params: Record<string, string> = {}) {
    this.route = route;
    this.params = params;
  }

  setLevel(level: string) {
    if (level === this.level) return;
    this.level = level;
    this.sel = null;
  }
}

export const app = new AppState(readHash());

/** Write the state to the hash (debounced, not while the reach animation runs) and follow
 *  hash changes made by links. Call from a component's $effect; returns the cleanup. */
export function syncHash(): () => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const stopEffect = $effect.root(() => {
    $effect(() => {
      const s = app.snapshot();
      storeLang(s.lang);
      if (app.playing) return;
      clearTimeout(timer);
      timer = setTimeout(() => writeHash(s), 150);
    });
  });
  const onHash = () => app.load(parseHash(location.hash));
  window.addEventListener('hashchange', onHash);
  return () => {
    clearTimeout(timer);
    stopEffect();
    window.removeEventListener('hashchange', onHash);
  };
}
