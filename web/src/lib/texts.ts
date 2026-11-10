// German and French for the texts the pipeline writes in English (value notes, gap reasons, curation reasons,
// travel-time reasons, source descriptions): web/texts.json, docs/web_data_contract.md section 11.1. The data
// files keep their English texts; `translate` looks a text up as an exact key, else as a pattern, else segment by
// segment ("; "). Reference implementation: translate() in pipeline/build/texts.py. Pure functions (tested).

export interface TextsFile {
  version: number;
  langs: string[];
  exact: Record<string, Record<string, string>>;
  patterns: { en: string; de?: string; fr?: string }[];
  numbers: Record<string, { group: string; decimal: string }>;
}

interface Compiled {
  file: TextsFile;
  res: { re: RegExp; p: TextsFile['patterns'][number] }[];
}
const compiled = new WeakMap<TextsFile, Compiled>();
function compile(f: TextsFile): Compiled {
  let c = compiled.get(f);
  if (!c) {
    const res: Compiled['res'] = [];
    for (const p of f.patterns ?? []) {
      try {
        res.push({ re: new RegExp(`^(?:${p.en})$`), p });
      } catch {
        /* a pattern this engine cannot read is skipped */
      }
    }
    c = { file: f, res };
    compiled.set(f, c);
  }
  return c;
}

/** English number "1,234.5" in the target language's grouping ("1'234.5", "1 234,5"). */
function fmtNumbers(s: string, f: TextsFile, lang: string): string {
  const n = f.numbers?.[lang];
  if (!n) return s;
  return s.replace(/\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+/g, (m) => {
    const [int, dec] = m.split('.');
    const i = int.replace(/,/g, n.group);
    return dec !== undefined ? `${i}${n.decimal}${dec}` : i;
  });
}

/** Steps 1 (exact, whole-text pattern) for one text; null when nothing matches. */
function one(c: Compiled, text: string, lang: string, depth: number): string | null {
  const ex = c.file.exact?.[text]?.[lang];
  if (ex !== undefined) return ex;
  if (depth > 4) return null;
  for (const { re, p } of c.res) {
    const tpl = p[lang as 'de' | 'fr'];
    if (!tpl) continue;
    const m = re.exec(text);
    if (!m) continue;
    let ok = true;
    const out = tpl.replace(/\{(\d+)(?:\|([ntl]))?\}/g, (_, k: string, mode: string | undefined) => {
      const g = m[Number(k)] ?? '';
      if (!mode) return g;
      if (mode === 'n') return fmtNumbers(g, c.file, lang);
      if (mode === 't') {
        const tr = full(c, g, lang, depth + 1, true);
        if (tr === null) ok = false;
        return tr ?? g;
      }
      // 'l': a list "a, b, c", each item translated
      const items = g.split(', ').map((x) => full(c, x, lang, depth + 1, true));
      if (items.some((x) => x === null)) ok = false;
      return items.map((x, j) => x ?? g.split(', ')[j]).join(', ');
    });
    if (ok) return out;
  }
  return null;
}

/** Steps 1–2: the whole text, else the longest runs of "; "-separated segments that match. null = no part matched,
 *  or (strict, inside a template) any part left untranslated. */
function full(c: Compiled, text: string, lang: string, depth = 0, strict = false): string | null {
  const w = one(c, text, lang, depth);
  if (w !== null) return w;
  const seg = text.split('; ');
  if (seg.length < 2) return null;
  const parts: string[] = [];
  let any = false;
  for (let i = 0; i < seg.length; ) {
    let done = false;
    for (let j = seg.length; j > i; j--) {
      const tr = one(c, seg.slice(i, j).join('; '), lang, depth);
      if (tr !== null) {
        parts.push(tr);
        i = j;
        any = true;
        done = true;
        break;
      }
    }
    if (!done) {
      if (strict) return null;
      parts.push(seg[i]);
      i++;
    }
  }
  return any ? parts.join(lang === 'fr' ? ' ; ' : '; ') : null;
}

/** The text in `lang` (de / fr), or the English text unchanged when there is no translation. */
export function translate(f: TextsFile | null | undefined, text: string, lang: string): string {
  if (!f || !text || lang === 'en' || !(f.langs ?? []).includes(lang)) return text;
  return full(compile(f), text, lang) ?? text;
}
