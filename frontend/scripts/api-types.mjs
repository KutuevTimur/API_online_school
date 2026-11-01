import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { readFile, writeFile } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';
const root = fileURLToPath(new URL('../../', import.meta.url));
const result = spawnSync(
  process.env.LGG_PYTHON || `${root}.venv/bin/python`,
  [`${root}frontend/scripts/export_openapi.py`],
  { cwd: root, encoding: 'utf8' },
);
if (result.status !== 0) {
  console.error('OpenAPI export failed; verify local Python dependencies.');
  process.exit(1);
}
const generated = astToString(await openapiTS(JSON.parse(result.stdout)));
const target = new URL('../src/shared/api/schema.d.ts', import.meta.url);
if (process.argv.includes('--check')) {
  if ((await readFile(target, 'utf8').catch(() => '')) !== generated) {
    console.error('OpenAPI types differ: run api:types');
    process.exit(1);
  }
  console.log('OpenAPI types match source');
} else {
  await writeFile(target, generated);
  console.log('OpenAPI types generated from source (no DB connection)');
}
