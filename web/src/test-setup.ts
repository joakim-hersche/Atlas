// Minimal browser globals for unit tests that import lib modules reading the URL hash at load time
// (state.svelte.ts creates the app state from location.hash). No DOM library needed.
const g = globalThis as Record<string, unknown>;
if (typeof g.location === 'undefined') g.location = { hash: '', pathname: '/', search: '' };
