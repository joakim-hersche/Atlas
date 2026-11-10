// Radio groups (role="radiogroup" with role="radio" buttons) behave like native radios everywhere in the
// app: one tab stop per group (the checked one), arrow keys move and select, Home / End jump to the ends.
// Installed once by the shell; it follows the DOM, so components only need the roles and aria-checked.

const radiosOf = (g: Element): HTMLElement[] =>
  [...g.querySelectorAll<HTMLElement>('[role="radio"]')].filter((r) => r.closest('[role="radiogroup"]') === g);
const enabled = (r: HTMLElement) => !(r as HTMLButtonElement).disabled && r.getAttribute('aria-disabled') !== 'true';

function syncTabStops(): void {
  for (const g of document.querySelectorAll('[role="radiogroup"]')) {
    const rs = radiosOf(g);
    const stop = rs.find((r) => r.getAttribute('aria-checked') === 'true' && enabled(r)) ?? rs.find(enabled);
    for (const r of rs) {
      const ti = r === stop ? 0 : -1;
      if (r.tabIndex !== ti) r.tabIndex = ti;
    }
  }
}

const STEP: Record<string, number> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

function onKey(e: KeyboardEvent): void {
  const r = (e.target as Element | null)?.closest?.('[role="radio"]') as HTMLElement | null;
  const g = r?.closest('[role="radiogroup"]');
  if (!r || !g) return;
  const rs = radiosOf(g).filter(enabled);
  const k = rs.indexOf(r);
  if (k < 0 || !rs.length) return;
  let next: HTMLElement | undefined;
  if (e.key in STEP) next = rs[(k + STEP[e.key] + rs.length) % rs.length];
  else if (e.key === 'Home') next = rs[0];
  else if (e.key === 'End') next = rs[rs.length - 1];
  if (!next) return;
  e.preventDefault();
  next.focus();
  if (next.getAttribute('aria-checked') !== 'true') next.click();
}

export function initRadioGroups(): () => void {
  let raf = 0;
  const schedule = () => {
    if (!raf) raf = requestAnimationFrame(() => {
      raf = 0;
      syncTabStops();
    });
  };
  const mo = new MutationObserver(schedule);
  mo.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['aria-checked', 'disabled'] });
  document.addEventListener('keydown', onKey);
  schedule();
  return () => {
    mo.disconnect();
    cancelAnimationFrame(raf);
    document.removeEventListener('keydown', onKey);
  };
}
