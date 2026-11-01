import { readFile, writeFile, mkdir } from 'node:fs/promises';
const source = await readFile(
  new URL('../src/app/theme.ts', import.meta.url),
  'utf8',
);
const tokens = Object.fromEntries(
  [...source.matchAll(/(\w+):\s*'(#[\da-f]{6})'/gi)].map((m) => [m[1], m[2]]),
);
const design = await readFile(
  new URL('../../DESIGN.md', import.meta.url),
  'utf8',
);
for (const [key, value] of Object.entries(tokens))
  if (!design.includes(`${key}: "${value}"`))
    throw Error(`DESIGN drift: ${key}`);
const luminance = (hex) => {
  const rgb = hex
    .slice(1)
    .match(/../g)
    .map((x) => parseInt(x, 16) / 255)
    .map((x) => (x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4));
  return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
};
const pairs = [
  ['ink', 'surface'],
  ['ink', 'canvas'],
  ['ink', 'studentCanvas'],
  ['muted', 'studentCanvas'],
  ['primary', 'studentCanvas'],
  ['ink', 'studentHeader'],
  ['ink', 'studentHover'],
  ['muted', 'surface'],
  ['muted', 'canvas'],
  ['ink', 'lesson'],
  ['ink', 'mint'],
  ['ink', 'materialInsetSurface'],
  ...['reviewSurface', 'materialMissingSurface'].flatMap((background) =>
    ['ink', 'muted', 'primary', 'danger'].map((foreground) => [
      foreground,
      background,
    ]),
  ),
  ...['reviewActionSurface', 'reviewActionHover', 'reviewActionActive'].map(
    (background) => ['ink', background],
  ),
  ['success', 'mint'],
  ['success', 'reviewCheckedHover'],
  ['success', 'successSurface'],
  ['ink', 'successSurface'],
  ['muted', 'successSurface'],
  ['danger', 'successSurface'],
  ['surface', 'primary'],
  ['danger', 'surface'],
  ['danger', 'materialMissingBadge'],
  ['primary', 'surface'],
  ['primary', 'lesson'],
  ['controlBorder', 'surface'],
];
const results = pairs.map(([a, b]) => {
  const x = luminance(tokens[a]),
    y = luminance(tokens[b]);
  const ratio = (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  const required =
    (a === 'primary' && b === 'lesson') || a === 'controlBorder' ? 3 : 4.5;
  return {
    foreground: a,
    background: b,
    ratio: Number(ratio.toFixed(2)),
    required,
    pass: ratio >= required,
  };
});
await mkdir(new URL('../.artifacts/', import.meta.url), { recursive: true });
await writeFile(
  new URL('../.artifacts/contrast.json', import.meta.url),
  JSON.stringify(results, null, 2),
);
console.log(results);
if (results.some((x) => !x.pass)) process.exit(1);
