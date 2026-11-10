// Typography per UI language (B8, E8): French sets a narrow no-break space (U+202F) before a colon, semicolon,
// question and exclamation mark and before the percent sign; English and German use a no-break space before %
// (as the app always did) and none before the colon. Use these where a string is assembled in code
// ("Source: BFS", "45 %") instead of coming whole from the dictionaries.
import { app } from './state.svelte';

const NNBSP = ' ';
const NBSP = ' ';

/** ": " in English and German, " : " (narrow no-break space) in French */
export const colon = (lang: string = app.lang): string => (lang === 'fr' ? `${NNBSP}: ` : ': ');

/** the space before "%" */
export const pctSep = (lang: string = app.lang): string => (lang === 'fr' ? NNBSP : NBSP);

/** French typography applied to a finished string: the space before : ; ! ? % becomes a narrow no-break space,
 *  and a straight apostrophe between letters becomes a curly one. Times (08:30), URLs (https://) and
 *  ratios without a space before the colon are left alone. Other languages are returned unchanged. */
export function frTypo(s: string, lang: string = app.lang): string {
  if (lang !== 'fr' || !s) return s;
  return s
    .replace(/[   ]([:;!?])(?=\s|$)/g, `${NNBSP}$1`)
    .replace(/(\d)[  ]%/g, `$1${NNBSP}%`)
    .replace(/(\p{L})'(\p{L})/gu, '$1’$2');
}
