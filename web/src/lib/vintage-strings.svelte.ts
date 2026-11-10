// UI strings of the older-boundaries feature (kept next to it, registered with addStrings; French is
// merged into the French dictionary once that is loaded). `tv` re-renders when the French strings
// arrive.
import { addStrings, loadFrench, t } from './i18n.svelte';
import { app } from './state.svelte';

const EN = {
  'vin.label': 'Boundaries',
  'vin.ref': '{y} harmonised',
  'vin.refT': 'All data on the current municipality state ({date}), history reprojected onto it',
  'vin.oldT': 'Municipality map of {date}: only data published on that state (or an older one)',
  'vin.title': 'Municipalities of {date}',
  'vin.count': '{n} municipalities on this state ({m} today).',
  'vin.na': '“{metric}” has no values on the {y} boundaries. An older state shows only data published on that state (or an older one); ATLAS does not split merged municipalities back into their former parts.',
  'vin.naShort': 'not on the {y} boundaries',
  'vin.toRef': 'Show it on the {y} harmonised map',
  'vin.try': 'Show {metric} instead',
  'vin.nAvail': '{n} metrics exist on these boundaries.',
  'vin.native': 'Published by the source on this municipality state.',
  'vin.forward': 'Published on an older state and carried forward to these boundaries by ATLAS: merged municipalities summed; where a municipality was split, its counts are divided by the residents of each part (boundary estimate).',
  'vin.nEst': '{n} municipalities carry a boundary estimate.',
  'vin.noYear': 'no value for {y} on these boundaries',
  'vin.today': 'Today part of',
  'vin.todayOne': 'Today',
  'vin.mergedL': 'Formed from',
  'vin.mergedV': '{n} municipalities of {y}',
  'vin.share': '{p} % of residents',
  'vin.profile': 'Profile today',
  'vin.hint': 'Tap a municipality for its value and the municipality it belongs to today.',
  'vin.geo': 'Boundaries: BFS generalised historized boundaries (G1), state {date}',
  'vin.loading': 'Loading the {y} boundaries …',
  'vin.ch': 'Switzerland',
  'vin.none': 'This version of ATLAS has no older boundaries.',
  'vin.brand': 'Switzerland · municipalities of {y} (not harmonised)',
  'vin.yrHarm': 'on the boundaries of {date}',
};
const DE = {
  'vin.label': 'Grenzen',
  'vin.ref': '{y} harmonisiert',
  'vin.refT': 'Alle Daten auf dem aktuellen Gemeindestand ({date}), die Geschichte darauf umgerechnet',
  'vin.oldT': 'Gemeindekarte vom {date}: nur Daten, die auf diesem (oder einem älteren) Stand publiziert sind',
  'vin.title': 'Gemeinden am {date}',
  'vin.count': '{n} Gemeinden auf diesem Stand (heute {m}).',
  'vin.na': '«{metric}» hat auf dem Gemeindestand {y} keine Werte. Ein früherer Stand zeigt nur Daten, die auf diesem (oder einem älteren) Stand publiziert sind; ATLAS teilt fusionierte Gemeinden nicht in ihre früheren Teile auf.',
  'vin.naShort': 'nicht auf dem Stand {y}',
  'vin.toRef': 'Auf der harmonisierten Karte {y} zeigen',
  'vin.try': 'Stattdessen {metric} zeigen',
  'vin.nAvail': '{n} Merkmale gibt es auf diesem Gemeindestand.',
  'vin.native': 'Von der Quelle auf diesem Gemeindestand publiziert.',
  'vin.forward': 'Auf einem älteren Stand publiziert und von ATLAS auf diesen Stand fortgeschrieben: fusionierte Gemeinden summiert; wo eine Gemeinde geteilt wurde, nach der Bevölkerung der Teile aufgeteilt (Grenzschätzung).',
  'vin.nEst': '{n} Gemeinden mit Grenzschätzung.',
  'vin.noYear': 'kein Wert für {y} auf diesem Gemeindestand',
  'vin.today': 'Heute Teil von',
  'vin.todayOne': 'Heute',
  'vin.mergedL': 'Entstanden aus',
  'vin.mergedV': '{n} Gemeinden von {y}',
  'vin.share': '{p} % der Einwohner',
  'vin.profile': 'Profil heute',
  'vin.hint': 'Gemeinde antippen: Wert und die Gemeinde, zu der sie heute gehört.',
  'vin.geo': 'Grenzen: BFS generalisierte historisierte Gemeindegrenzen (G1), Stand {date}',
  'vin.loading': 'Gemeindestand {y} wird geladen …',
  'vin.ch': 'Schweiz',
  'vin.none': 'Diese Version von ATLAS enthält keine früheren Gemeindestände.',
  'vin.brand': 'Schweiz · Gemeinden von {y} (nicht harmonisiert)',
  'vin.yrHarm': 'auf dem Gemeindestand vom {date}',
};
const n = ' ';
const FR: Record<string, string> = {
  'vin.label': 'Limites',
  'vin.ref': '{y} harmonisé',
  'vin.refT': `Toutes les données sur l’état actuel des communes ({date}), l’historique recalculé sur cet état`,
  'vin.oldT': `Carte des communes au {date}${n}: seulement les données publiées sur cet état (ou un état plus ancien)`,
  'vin.title': 'Communes au {date}',
  'vin.count': '{n} communes à cet état ({m} aujourd’hui).',
  'vin.na': `«${n}{metric}${n}» n’a pas de valeurs sur les limites de {y}. Un ancien état ne montre que les données publiées sur cet état (ou un état plus ancien)${n}; ATLAS ne redivise pas les communes fusionnées.`,
  'vin.naShort': 'pas sur les limites de {y}',
  'vin.toRef': 'Afficher sur la carte harmonisée {y}',
  'vin.try': 'Afficher {metric} à la place',
  'vin.nAvail': '{n} indicateurs existent sur ces limites.',
  'vin.native': 'Publié par la source sur cet état des communes.',
  'vin.forward': `Publié sur un état plus ancien et reporté sur ces limites par ATLAS${n}: communes fusionnées additionnées${n}; une commune divisée est répartie selon la population de chaque partie (estimation de limites).`,
  'vin.nEst': '{n} communes avec une estimation de limites.',
  'vin.noYear': 'pas de valeur pour {y} sur ces limites',
  'vin.today': 'Aujourd’hui dans',
  'vin.todayOne': 'Aujourd’hui',
  'vin.mergedL': 'Issue de',
  'vin.mergedV': '{n} communes de {y}',
  'vin.share': `{p}${n}% des habitants`,
  'vin.profile': 'Profil actuel',
  'vin.hint': 'Touchez une commune pour sa valeur et la commune dont elle fait partie aujourd’hui.',
  'vin.geo': `Limites${n}: OFS limites communales généralisées historisées (G1), état {date}`,
  'vin.loading': 'Chargement des limites de {y} …',
  'vin.ch': 'Suisse',
  'vin.none': 'Cette version d’ATLAS ne contient pas d’anciennes limites.',
  'vin.brand': 'Suisse · communes de {y} (non harmonisé)',
  'vin.yrHarm': 'sur les limites du {date}',
};
addStrings(EN, DE);

let frReady = $state(false);
let frP: Promise<unknown> | null = null;
function ensureFrench() {
  frP ??= Promise.all([loadFrench(), import('./i18n-fr')]).then(([, m]) => {
    Object.assign(m.FR, FR);
    frReady = true;
  });
}

/** t() for these strings; also waits for the French dictionary. */
export function tv(key: string, vars?: Record<string, string | number>): string {
  if (app.lang === 'fr') {
    ensureFrench();
    void frReady;
  }
  return t(key, vars);
}

/** 31.12.2000 / 31 Dec 2000 / 31.12.2000 */
export function fmtDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  if (app.lang === 'en') return `${d} ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m - 1]} ${y}`;
  return `${String(d).padStart(2, '0')}.${String(m).padStart(2, '0')}.${y}`;
}
