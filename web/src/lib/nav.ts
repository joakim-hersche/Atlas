// Links between pages that keep the rest of the view state (map metric, level, filters …), so a link
// opened in a new tab or shared carries it too, and Back returns to where the reader was.
import { serializeHash, type ViewState } from './hash';
import { LEVELS, type Base } from './data';
import { switchLevel } from './levels';
import { parseRef } from './places';
import { app } from './state.svelte';

export function hrefFor(route: string, params: Record<string, string> = {}, extra: Partial<ViewState> = {}): string {
  return serializeHash({ ...app.snapshot(), ...extra, route, params }) || '#';
}
export const profileHref = (ref: string) => hrefFor('profile', { id: ref });
export const sourceHref = (id: string) => hrefFor('sources', { src: id });

/** Levels that have a map. */
export const hasMap = (level: string) => LEVELS.some((l) => l.id === level && l.geometry);

/** Open the map at the place's level with the place selected and in view. */
export function showOnMap(base: Base, ref: string): void {
  const { level, id } = parseRef(ref);
  if (!hasMap(level)) return;
  if (app.level !== level) switchLevel(base, level);
  app.sel = id;
  app.focusSel = true;
  app.go('map', {});
}
