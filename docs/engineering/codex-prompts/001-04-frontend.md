# Task 001, Part 4 of 6: Frontend (React, Vite, Vitest)

**Status:** Ready. The foundation task is split into 6 self-contained parts for an agent with a 200K token context. Each part runs in its own fresh session and does not depend on earlier conversation, only on the repository.
**Depends on:** Part 1 (Makefile, .nvmrc). Independent of the backend parts
**Branch:** `m0/foundation`
**How to send:** open a new session, then paste the block below. Alternatively paste this single line and let the agent read the file: `Read the file docs/engineering/codex-prompts/001-04-frontend.md and execute the prompt inside it exactly. Do not read other files unless the prompt names them.`

---

```text
TASK 001 | M0 FOUNDATION | PART 4 OF 6 | Frontend (React, Vite, Vitest)

SESSION CONTEXT
You are the implementation agent for LifeSpace, a local single-user application. Task 001 builds the technical foundation in 6 parts. Each part runs in a separate session and you have no memory of earlier parts. Everything you need is in this prompt and in the repository. A separate architect reviews your Git diff, so do exactly what this part asks and nothing else. Do not start work that belongs to another part.

CONTEXT BUDGET (this session has a limited context window)
- Read only the files this prompt names. Read docs/engineering/TECHNICAL_BLUEPRINT.md once, in full, at the start. Do not read any other document under docs/.
- Never print lockfiles, node_modules, .venv, or full logs. Pipe long command output through "tail -n 30".
- Never run a server in the foreground. Use this background pattern and always stop the server afterwards.
    start:  setsid bash -c 'exec make dev-api' > /tmp/lifespace-api.log 2>&1 & echo $! > /tmp/lifespace-api.pid
    wait:   for i in $(seq 1 60); do curl -fsS http://127.0.0.1:8000/api/health && break; sleep 0.5; done
    stop:   kill -- -"$(cat /tmp/lifespace-api.pid)"; sleep 1; ss -ltn | grep ':8000 ' || echo "port 8000 free"
  The same pattern works for make dev-web (port 5173, files /tmp/lifespace-web.log and /tmp/lifespace-web.pid).
- If the same command fails twice for the same reason, stop and report the exact error. Try at most two different fixes for one problem.
- Your training data may predate the pinned versions (FastAPI 0.133, Starlette 1.x, SQLAlchemy 2.0.50, pytest-asyncio 1.4, Vite 8, Vitest 5, TypeScript 6, ESLint 9 flat config). When unsure of an API, read the installed package source or README (under apps/api/.venv/lib/python3.14/site-packages or apps/web/node_modules) instead of guessing.

SCOPE RULES (owner decisions, binding)
- Local single-user app. No authentication, registration, sessions, OAuth, accounts, user_id columns, or multi-tenancy. Authentication is deferred and is NOT an approved requirement.
- No Redis, vector database, message broker, agent framework, cloud infrastructure, CI, Dependabot, app Dockerfiles, or deployment configuration.
- No unnecessary abstractions. Write the simplest code that satisfies this part.

MACHINE FACTS (do not fight them, do not change them)
- Ubuntu 26.04, Node 22.22.3 (nvm), npm 10.9.8, Python 3.14.4, uv 0.11.28, Docker Desktop with Compose v5, GNU Make 4.4.1. pnpm is not installed and must not be used.
- Do not install, upgrade, or remove any global tool or package. No sudo. No npm install -g, pip install, or uv python install. Python dependencies live only in apps/api/.venv created by uv. Every uv call must run with UV_PYTHON_DOWNLOADS=never (the Makefile exports it).
- The repository path contains a space ("/home/nour/AI Factory/LifeSpace"). Quote every path in the Makefile and scripts, and prefer paths relative to the repository root.
- The login shell exports NODE_ENV=production, which makes npm skip devDependencies. apps/web/.npmrc contains include=dev and the npm scripts dev, build, preview, and test run through "env -u NODE_ENV". Run any ad hoc npm command with "env -u NODE_ENV".
- A host PostgreSQL service already listens on 127.0.0.1:5432. Never use that port or connect to it. The project database is a Docker container published on 127.0.0.1:5433.
- Docker Desktop must be running with the desktop-linux context selected. Do not change the Docker context or start or stop Docker Desktop. If Docker is unreachable, stop and report it.
- Disk space on /home can be low. If a command fails with ENOSPC, stop and report. Do not work around it.

GIT RULES
- Work on branch m0/foundation. Create it from main only if it does not exist. Do not commit to main, push, merge, or rewrite history.
- Never modify files under docs/.
- Commit your work in small conventional commits and finish with a clean git status.
- If git status is dirty at the start and the changes do not belong to this part, stop and report. Never discard changes you did not make.
- Never create or commit .env, secrets, or credentials.

START CHECK (run first)
1. git branch --show-current must print m0/foundation. git status --short must be empty.
2. Confirm Part 1 exists: Makefile, .nvmrc, .env.example. If missing, stop and tell the user to run Part 1 first.
3. Read docs/engineering/TECHNICAL_BLUEPRINT.md in full.
4. Run: node -v (must be v22.22.3) and npm -v (10.9.8).
5. If apps/web already exists, inspect it with git status and ls, and continue from what is missing.

OBJECTIVE
Create the React single page app with a status line that calls GET /api/health, plus quality tooling and tests. No backend work. No router, no error boundary, no visual design.

APPROVED VERSIONS (exact, final, saved with save-exact)
- apps/web/.npmrc contains exactly two lines: include=dev and save-exact=true.
- Runtime: react 19.3.1, react-dom 19.3.1, @tanstack/react-query 5.107.1.
- Dev: vite 8.3.8, @vitejs/plugin-react 6.3.0, typescript 6.0.3 (NOT 7: typescript-eslint requires TypeScript below 6.1), vitest 5.1.0, jsdom 31.0.0, @testing-library/react 16.3.3, @testing-library/dom 10.4.2, @testing-library/jest-dom 7.0.1, eslint 9.39.5 (NOT 10: eslint-plugin-jsx-a11y requires ESLint 9 or lower), @eslint/js 9.39.5, typescript-eslint 8.72.2, eslint-plugin-react-hooks 7.1.1, eslint-plugin-jsx-a11y 6.10.2, globals 17.14.0, prettier 3.10.1, @types/react 19.3.0, @types/react-dom 19.3.0, @types/node 22.20.5.
- Install with two commands, run inside apps/web and always prefixed with env -u NODE_ENV: "npm install" for the runtime packages and "npm install -D" for the dev packages, each package written as name@version.
- Never use --force, --legacy-peer-deps, overrides, or resolutions. If a listed version cannot be installed, stop and report the exact error.
- Do not add any other dependency (no React Router, Zustand, Motion, d3, Radix, Tailwind, zod, user-event, UI kits, Playwright).

FILES TO CREATE (apps/web)
- package.json: name lifespace-web, private, type module, engines node ">=22.22.2 <23". Scripts exactly: dev "env -u NODE_ENV vite", build "env -u NODE_ENV vite build", preview "env -u NODE_ENV vite preview", test "env -u NODE_ENV vitest run", lint "eslint .", format "prettier --write .", format:check "prettier --check .", typecheck "tsc --noEmit".
- index.html (title LifeSpace, div id root, module script /src/main.tsx).
- vite.config.ts: import defineConfig from "vitest/config" and the react plugin. Dev server host 127.0.0.1, port 5173, strictPort true, proxy "/api" to API_PROXY_TARGET (default http://127.0.0.1:8000). Read API_PROXY_TARGET with loadEnv from the repository-root .env (two directories above apps/web) and process.env, then the default. Test config: environment jsdom, globals true, setupFiles ["./src/test/setup.ts"].
- tsconfig.json: strict true, noUncheckedIndexedAccess true, noEmit, jsx react-jsx, target ES2023, module ESNext, moduleResolution Bundler, skipLibCheck, types ["vite/client", "vitest/globals", "@testing-library/jest-dom", "node"], include ["src", "vite.config.ts"].
- eslint.config.js (flat config): ignores dist, js.configs.recommended, typescript-eslint recommended, jsxA11y.flatConfigs.recommended, reactHooks.configs.flat.recommended, browser globals from the globals package. This combination is verified to work.
- .prettierrc.json (double quotes, semicolons, trailing commas all, print width 100) and .prettierignore listing dist and package-lock.json.
- src/test/setup.ts importing "@testing-library/jest-dom/vitest".
- src/shared/api/client.ts: class ApiError extends Error with status, code, and detail; and async apiFetch<T>(path, init?) that calls fetch and returns parsed JSON on success. On a non-OK response it parses an application/problem+json body into ApiError (code and detail from the body) and, when the body is not problem+json or not JSON, throws ApiError with status, code "failed", and a generic detail.
- src/features/system-status/ApiStatus.tsx: uses useQuery from TanStack Query with queryKey ["health"] and apiFetch("/api/health"). It renders one line of text: "API status: checking" while loading, "API status: ok" on success (use the returned status value), and "API status: unreachable" on error. Never rely on color.
- src/App.tsx: renders a main element with an h1 "LifeSpace" and the ApiStatus component. src/main.tsx: creates a QueryClient and mounts the app inside QueryClientProvider and StrictMode.
- No CSS file beyond minimal layout (a small optional stylesheet). No colors, no design tokens.

TESTS (Vitest and Testing Library; mock fetch with vi.stubGlobal and restore it with vi.unstubAllGlobals)
- client.test.ts: apiFetch returns data on success; a problem+json error becomes ApiError with the right status, code, and detail; a plain-text error becomes ApiError with code "failed".
- ApiStatus.test.tsx: shows the checking text first, then "API status: ok" when fetch resolves {"status": "ok"}; shows "API status: unreachable" when fetch rejects. Create a fresh QueryClient per test with retry disabled.

MAKEFILE TARGETS TO ADD (tab indentation, keep .PHONY updated)
- web-setup: cd $(WEB) && env -u NODE_ENV npm ci
- web-lint: cd $(WEB) && npm run lint && npm run format:check
- web-format: cd $(WEB) && npm run format
- web-typecheck: cd $(WEB) && npm run typecheck
- web-test: cd $(WEB) && npm test
- web-build: cd $(WEB) && npm run build
- dev-web: cd $(WEB) && npm run dev

VERIFY (run each, record the real result)
1. NODE_ENV=production make web-setup, then: cd apps/web && env -u NODE_ENV npm ls --depth=0 2>&1 | tail -n 30. The list must include vite and vitest (proof that devDependencies were installed despite NODE_ENV=production).
2. make web-lint, make web-typecheck, make web-test (record the number of tests), make web-build. All with zero errors and zero warnings.
3. Start the dev server with the background pattern for make dev-web (port 5173, files /tmp/lifespace-web.*). curl -fsS http://127.0.0.1:5173/ must return HTML containing LifeSpace. Stop the server and confirm port 5173 is free. (The /api proxy is verified in Part 5 with the backend running.)
4. git status --short must not list node_modules or dist. package-lock.json must be tracked.

COMMIT
Small conventional commits, for example "chore(web): scaffold vite react typescript project and tooling", "feat(web): add api client and system status line", "test(web): add client and status tests", "chore: add web make targets". git status must be clean afterwards.

END-OF-SESSION REPORT (required, maximum 30 lines, plain text)
- Part number and result: DONE or BLOCKED.
- Commits made (git log --oneline main..HEAD, newest first).
- Each verification command and its real result (pass or fail, test counts).
- Deviations from this prompt and why. The exact error text for any blocker.
- Anything the next part must know.
Finish by telling the user: "Part 4 is finished. Start a new session for the next part."
```
