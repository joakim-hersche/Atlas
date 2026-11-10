// English, German and French strings of the review round 3 fixes (2026-11-10): small numbers in change maps,
// hidden vs no data, PNG export, phone layout, older boundaries, profile, wording. French is FR_R3 below,
// merged into the French dictionary by i18n-fr.ts. French: no-break space (U+202F) before : ; ? ! and %.
import { addStrings } from './i18n.svelte';

const n = ' ';

const EN: Record<string, string> = {
  // B1 small numbers in change maps
  'r3.hiddenChg': 'hidden: small numbers in {from} or {to} (the change is unstable)',
  'r3.chgEither': 'Flagged because the value of {from} or {to} rests on small numbers.',
  'r3.urChg': '{n} changes rest on small numbers in either year (△)',
  // B2 hidden vs no data
  'r3.hiddenN': '{n} hidden as small numbers',
  'r3.showThem': 'show',
  'r3.sparseHidden': '{n} of {total} {units} shown ({pct}): {h} hidden as small numbers, {g} without data.',
  'r3.sparseHiddenOnly': '{n} of {total} {units} shown ({pct}): {h} are hidden as small numbers.',
  'r3.agHidden': 'Includes {n} {units} hidden on the map as small numbers: totals and ratios of sums count every unit.',
  'r3.agHiddenMean': 'Includes {n} {units} hidden on the map as small numbers (their weights count).',
  'r3.nUnits': 'n = {n} {units}',
  'r3.smNote': 'Each panel shows the values of its year, not the change.',
  'r3.smHidden': '{h} hidden',
  'r3.rgHidden': 'Small-number values are hidden on the map, so they are left out here too ({n}).',
  'r3.rgShown': 'Small-number values are shown on the map; here they are left out only if you tick the box.',
  'r3.csvHidden': 'small numbers hidden',
};

const DE: Record<string, string> = {
  'r3.hiddenChg': 'ausgeblendet: kleine Zahlen {from} oder {to} (die Veränderung ist unsicher)',
  'r3.chgEither': 'Markiert, weil der Wert von {from} oder {to} auf kleinen Zahlen beruht.',
  'r3.urChg': '{n} Veränderungen beruhen in einem der beiden Jahre auf kleinen Zahlen (△)',
  'r3.hiddenN': '{n} als kleine Zahlen ausgeblendet',
  'r3.showThem': 'zeigen',
  'r3.sparseHidden': '{n} von {total} {units} gezeigt ({pct}): {h} als kleine Zahlen ausgeblendet, {g} ohne Daten.',
  'r3.sparseHiddenOnly': '{n} von {total} {units} gezeigt ({pct}): {h} sind als kleine Zahlen ausgeblendet.',
  'r3.agHidden': 'Enthält {n} {units}, die auf der Karte als kleine Zahlen ausgeblendet sind: Summen und Verhältnisse von Summen zählen jede Einheit.',
  'r3.agHiddenMean': 'Enthält {n} {units}, die auf der Karte als kleine Zahlen ausgeblendet sind (ihre Gewichte zählen).',
  'r3.nUnits': 'n = {n} {units}',
  'r3.smNote': 'Jede Tafel zeigt die Werte ihres Jahres, nicht die Veränderung.',
  'r3.smHidden': '{h} ausgeblendet',
  'r3.rgHidden': 'Werte mit kleinen Zahlen sind auf der Karte ausgeblendet und fehlen deshalb auch hier ({n}).',
  'r3.rgShown': 'Werte mit kleinen Zahlen sind auf der Karte sichtbar; hier fehlen sie nur, wenn Sie das Kästchen ankreuzen.',
  'r3.csvHidden': 'kleine Zahlen ausgeblendet',
};

export const FR_R3: Record<string, string> = {
  'r3.hiddenChg': `masqué${n}: petits nombres en {from} ou en {to} (variation instable)`,
  'r3.chgEither': `Signalé parce que la valeur de {from} ou de {to} repose sur de petits nombres.`,
  'r3.urChg': '{n} variations reposent sur de petits nombres dans l’une des deux années (△)',
  'r3.hiddenN': '{n} masquées (petits nombres)',
  'r3.showThem': 'afficher',
  'r3.sparseHidden': `{n} {units} sur {total} affichées ({pct})${n}: {h} masquées (petits nombres), {g} sans données.`,
  'r3.sparseHiddenOnly': `{n} {units} sur {total} affichées ({pct})${n}: {h} sont masquées (petits nombres).`,
  'r3.agHidden': `Inclut {n} {units} masquées sur la carte (petits nombres)${n}: les totaux et rapports de sommes comptent chaque unité.`,
  'r3.agHiddenMean': `Inclut {n} {units} masquées sur la carte (petits nombres)${n}; leurs poids comptent.`,
  'r3.nUnits': 'n = {n} {units}',
  'r3.smNote': 'Chaque vignette montre les valeurs de son année, pas la variation.',
  'r3.smHidden': '{h} masquées',
  'r3.rgHidden': `Les valeurs à petits nombres sont masquées sur la carte, elles sont donc aussi exclues ici ({n}).`,
  'r3.rgShown': `Les valeurs à petits nombres sont affichées sur la carte${n}; ici, elles ne sont exclues que si vous cochez la case.`,
  'r3.csvHidden': 'petits nombres masqués',
};

addStrings(EN, DE);
