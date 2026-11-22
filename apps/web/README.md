# LifeSpace web

React single page application built with Vite and TypeScript. It calls the API
on the same origin under `/api`; in development Vite proxies `/api` to the
FastAPI process.

## Prerequisites

- **Node 22.22.2 or newer** in the accepted ranges `^22.22.2`, `^24.15.0`, or
  `>=26.0.0` (verified on Node 22.22.3 and Node 26.13.1)
- **npm 10 or 12**, installed with Node

The root `README.md` lists the remaining tools (uv, Docker Engine or Docker
Desktop, GNU Make).

## Commands

Run inside `apps/web`, or use the equivalent `make web-*` target from the
repository root:

| Command                | Purpose                            |
| ---------------------- | ---------------------------------- |
| `npm run dev`          | Vite dev server on 127.0.0.1:5173  |
| `npm run build`        | Production build into `dist/`      |
| `npm run preview`      | Serve the production build locally |
| `npm test`             | Run Vitest once                    |
| `npm run lint`         | ESLint                             |
| `npm run format`       | Prettier write                     |
| `npm run format:check` | Prettier check                     |
| `npm run typecheck`    | `tsc --noEmit`                     |

The dev server proxies `/api` to `API_PROXY_TARGET`, read from the repository
root `.env`, then the process environment, then `http://127.0.0.1:8000`.

## Layout

```
apps/web/
├── index.html
├── package.json
├── package-lock.json
├── vite.config.ts          dev server, proxy, and Vitest config
├── tsconfig.json
├── eslint.config.js        ESLint 9 flat config
├── .prettierrc.json
├── .prettierignore
├── .npmrc
└── src/
    ├── main.tsx            QueryClient, StrictMode, root render
    ├── App.tsx
    ├── styles.css          minimal layout only, no design tokens yet
    ├── features/
    │   └── system-status/  ApiStatus component and test
    ├── shared/
    │   └── api/            fetch client, ApiError, and test
    └── test/
        └── setup.ts        jest-dom matchers for Vitest
```

There is no router, error boundary, visual design system, or state store yet.
Later milestones add them when a second view or shared UI state exists.

## Dependency notes

Versions are exact and locked in `package-lock.json`; do not upgrade them
without checking the constraints below.

- **TypeScript 6.0.3, not 7.** `typescript-eslint` 8.72.2 requires TypeScript
  `>=4.8.4 <6.1.0`.
- **ESLint 9.39.5, not 10.** `eslint-plugin-jsx-a11y` 6.10.2 supports ESLint 9
  or lower. Do not upgrade ESLint or use overrides.
- **jsdom 31.0.0** requires Node 22.22.2 or newer, which sets the lower bound of
  the accepted Node ranges. `.nvmrc` pins Node 26.
- **`NODE_ENV=production` is neutralized.** The login shell exports it, and npm
  would skip devDependencies. `.npmrc` sets `include=dev`, and the `dev`,
  `build`, `preview`, and `test` scripts run through `env -u NODE_ENV`, so the
  development server and Vitest do not run in production mode.

Tests mock `fetch` with `vi.stubGlobal` and restore it with
`vi.unstubAllGlobals`; each test builds a fresh `QueryClient` with retries
disabled.
