# LGG frontend · T14/T15

React SPA, ru-RU / Europe/Moscow. `/login` uses the real browser cookie bridge. `/__ui` is a development-only component gallery with explicitly
illustrative content, excluded by Vite from production. Gallery needs no credentials. Login requires synthetic credentials.

## Runtime and setup

Node **24.22.0**, npm **11.19.1**; exact direct dependencies and lockfile.
System Node is unchanged. The locally verified official runtime is in ignored
`../.local-runtime/` (SHA256 recorded in T14d). For this checkout from repo root:

```sh
export PATH="$PWD/.local-runtime/bin:$PATH"
alias lgg-npm='node .local-runtime/npm-tool/node_modules/npm/bin/npm-cli.js --prefix frontend'
# Dependencies already exist in this checkout; do not reinstall for a checkup.
lgg-npm run dev
```

With a matching normal Node/npm environment: `cd frontend`, `npm ci`, `npm run dev`.
Preview: <http://127.0.0.1:5173/login>, <http://127.0.0.1:5173/__ui>.
Vite binds only loopback; `/api` proxies to `127.0.0.1:8019` with the prefix removed.
Production hosting must implement the same rewrite and return API errors (never
SPA HTML) for `/api`. Port 8019 is reserved for the guarded test preview; dev backend 8018 is not used.

## Verification

Student history S2 uses `/student/materials` («Мои занятия»); courses/archive and
legacy material detail remain available. Read-only browser checks and prerequisites:
`e2e/student-history-s2.spec.ts` and `e2e/README.md`. Current verification limits are
recorded in `docs/plan/tasks/T15d.md`; do not infer browser PASS from unit tests.

```sh
npm ls
npm run typecheck
npm run lint
npm run format:check
npm run test:unit
npm run build
npm run api:types
npm run api:types:check
npm run test:e2e
```

From repo root: `npm --prefix frontend run api:types` (and `api:types:check`).
Exporter uses `.venv/bin/python` or `LGG_PYTHON`. It imports the app factory with a
sentinel config; it never calls create_config, creates an engine, connects to DB,
reads `.env`, or enters lifespan. Export failure is sanitized. Generated types
are retained in `src/shared/api/schema.d.ts`. No backend tests are needed here.

`test:e2e` runs real auth/API scenarios against the synthetic preview; see e2e/README.md. Browser component verification is separate
from product E2E. Local reports/screenshots go to ignored `.artifacts/`.

A13 in `../docs/plan/ARCHITECTURE.md` is the canonical behavior/owner map.
`theme.ts` owns tokens; global CSS and CSS Modules consume its variables. Manrope
Latin/Cyrillic variable WOFF2 are bundled locally from Fontsource 5.3.0; OFL is
preserved in `public/fonts/Manrope-OFL.txt`. No external fonts or private storage.

API requests accept `params` (URLSearchParams encoding), `body` (JSON or FormData),
`response: 'blob'`, caller cancellation and a bounded timeout. `upload` exposes XHR
byte progress; 100% uploaded bytes does not confirm server processing or commit.
After an uncertain mutation outcome the caller must refetch before a manual retry.
`ApiError` contains status, safe Russian copy, field mapping and failure kind.

The first view of `/__ui` is now a cohesive, explicitly illustrative student
overview based on the two approved references. Sample lesson/homework/result/course
views use URL parameters inside this dev route; they do not authenticate, fetch
private data, save answers or connect meetings. Technical controls remain in the
collapsed disclosure below. The owner approved the visual foundation; runtime limits remain recorded in T14d.

## Safe synthetic preview

**Current preview is retained: do not seed/reset it.** Resume guidance:
[ENVIRONMENT](../docs/plan/ENVIRONMENT.md#сохранение-текущего-preview).
The commands below create a **new** synthetic namespace, only when separately
authorized and isolated from retained data. Do not run concurrently with DB pytest.
From repo root, after the read-only preflight succeeds:

```sh
MODE=TEST PYTHONPATH=. .venv/bin/python scripts/test_preflight.py
MODE=TEST PYTHONPATH=. .venv/bin/python scripts/t14e_preview.py
```

This creates random synthetic credentials and one-time activation/reset links only
in ignored `frontend/.artifacts/t14e-credentials.json` (0600). Open this file locally;
never paste it into chat, logs, commits or traces. Restarting the script regenerates
credentials/links for new synthetic accounts (a random namespace per run). Use `/login`, then reload and logout.
The backend media root is a new OS temporary `lgg-test-media-preview-*` directory;
no dev media is used. It is disposable and is not production persistence.

Production requires `BROWSER_ORIGIN=https://your-exact-host` (no trailing slash)
and `BROWSER_COOKIE_SECURE=1`; missing/insecure production configuration fails.
The same-origin proxy must preserve Origin and rewrite `/api` to backend root.
No wildcard CORS or cross-domain cookie workaround. Web Locks is required.
Access stays in memory; the HttpOnly refresh cookie is scoped to `/api/auth/browser`.
Teacher/student learning routes are implemented through T15b.3; admin remains a session placeholder. Current acceptance and remaining work: [STATUS](../docs/plan/STATUS.md).

## T14f files and recovery

Development-only file gallery: <http://127.0.0.1:5173/__ui/files>. Sign in with the
`files_student` entry in the ignored local credentials file, then choose **Открыть
тестовые файлы**. The preview seed now creates an isolated synthetic Homework,
working answer, two-page `math.pdf` and notebook photo using the actual upload API.
The normal `student` account remains separate for auth regression tests.

`UploadQueue` takes an existing answer and a version-aware adapter; it never creates
or submits an answer implicitly. Original File objects live in the upper memory
DraftProvider until ack/logout/discard. XHR bytes at100% are **Обрабатываем**, not
saved. Uncertain completion stops the queue; read the protected answer, compare,
then explicitly remove the already saved local copy or retry. No automatic mutation
replay.403/404 stop writes;409 keeps local files alongside the server version.
Persisted converted descriptors cannot reveal every historical original size;
server source-size/quota checks remain authoritative.

`FilePreview` reads authorized bytes and actual Content-Type; blob URLs never carry
a token. Preview stops reading at20MiB even without Content-Length. Legacy archives
have an explicit authenticated download fallback (which can use more memory), not
an unlimited preview promise. PDF.js and its worker are pinned to6.4.299. `predev`
and `prebuild` copy cmap/fonts/wasm/ICC and LICENSE from the installed exact package
into ignored `public/pdfjs/`; build serves these locally. No CDN, external viewer,
actions, scripting sandbox, annotations or authoring are instantiated. One page is
rendered at a time with a selectable text layer. Gallery keeps the current file ID
in the router query so browser Back closes it. This integration stays DEV-only;
T15 product screens reuse these shared file components.

Current preview media use an OS temporary directory recorded at
`files.media_root` in the ignored credentials JSON. Files survive a frontend reload
while this synthetic backend is running. Restarting the seed creates a fresh
namespace/root; this is not durable school storage. Normal Compose media use the
existing `lgg-dev_media` volume, persistent across ordinary restarts (not volume
removal). T14f does not change that volume or dev8018. View files through the
protected gallery; no public media directory or unauthenticated file link is added.

`files.spec.ts` combines actual API uploads/downloads/replacement/deletion with
explicit browser fault injection for interrupted/network/403/409/413/corrupt/large
responses. These fault examples do not certify real quota exhaustion, a dropped
connection after server commit, WebKit or physical mobile devices. Read the exact
results and NOT RUN matrix in `docs/plan/tasks/T14f.md`.

## T15b.1 teacher students and courses

`/teacher/students` and `/teacher/courses` use the existing scoped API. Invitation
links use `VITE_PUBLIC_ORIGIN` when configured, otherwise the current origin;
configure the public school origin in a production build. Only the activation
fragment from the API is accepted. Never put invitation tokens in page queries,
logs, screenshots, or persistent client storage. Current synthetic teacher access
is in ignored0600 `.artifacts/t15b1-login.txt`; old login notes become stale on seed.
Teacher schedule/review/MyDay are implemented; monetary statistics and admin UI remain planned. Evidence and manual route:
`docs/plan/tasks/T15b.md`, current facts: `docs/plan/STATUS.md`.

### Student-first refinement of T15b.1

Teacher landing is `/teacher`; old course-list/new links redirect to
`/teacher/students`. Pupil identity includes the shared school grade; a narrow grade endpoint
is editable by an actively linked teacher. Start teaching in the pupil card:
server creates/enrols a single active personal space atomically, retries reuse it.
Legacy/direct/archive courses remain available. Current teacher manual route and
checks supersede the original separate create/enrol UI route in T15b.md.
