import { cp, mkdir, readFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const pkg = JSON.parse(
  await readFile(new URL('node_modules/pdfjs-dist/package.json', root)),
);
if (pkg.version !== '6.4.299') throw new Error('Unexpected PDF.js version');
for (const name of ['cmaps', 'standard_fonts', 'wasm', 'iccs']) {
  await mkdir(new URL('public/pdfjs/', root), { recursive: true });
  await cp(
    new URL(`node_modules/pdfjs-dist/${name}`, root),
    new URL(`public/pdfjs/${name}`, root),
    { recursive: true },
  );
}
await cp(
  new URL('node_modules/pdfjs-dist/LICENSE', root),
  new URL('public/pdfjs/LICENSE', root),
);
console.log('PDF.js6.4.299 local assets ready');
