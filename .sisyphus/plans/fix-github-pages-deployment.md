# Fix GitHub Pages Deployment — diablaq.com

## TL;DR

> **Quick Summary**: Fix the flip-flopping deployment by switching GitHub Pages from legacy branch-based deployment to GitHub Actions artifact deployment, and clean up old static site remnants from the repo.
>
> **Deliverables**:
> - GitHub Pages source changed from "Deploy from branch" to "GitHub Actions"
> - Old static HTML files removed (root `index.html`, `_future.t`, 14 product directories)
> - All unpushed commits (14) delivered to `origin/gh-pages`
> - Site verified live at `https://diablaq.com` with generator-built content
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO — strictly sequential (each step depends on prior verification)
> **Critical Path**: Validate → Switch API → Remove files + commit → Push → Verify deployment

---

## Context

### Original Request
The user reported the live site at diablaq.com flip-flops between the new generator-built version and the old static HTML version. Sometimes a push deploys correctly, other times the site reverts.

### Root Cause Analysis
GitHub Pages is configured with `"build_type": "legacy"` and `"source": {"branch": "gh-pages", "path": "/"}`. This means GitHub directly serves raw files from the `gh-pages` branch root — which contains the **old** hand-written static site (`index.html` using `mvp.css`). The Actions workflow (`pages.yml`) ALSO deploys via `actions/deploy-pages` (the correct mechanism). These two deployments race, causing inconsistent results.

### Interview Summary
**Key Discussions**:
- **Branch strategy**: User wants to keep `gh-pages` as the development branch (not switch to `main`)
- **Remote scope**: Only `origin` (GitHub) — ignore `dom` remote
- **Old files**: User confirmed old static files should be removed
- **CNAME**: Generator handles it (copies from repo root to `dist/`)

### Metis Review
**Identified Gaps** (addressed):
- **CRITICAL — CNAME and .nojekyll must be preserved**: The builder COPIES these from repo root (`builder.py:154-157`), it does NOT generate them. Removing them breaks custom domain and Jekyll processing. **Decision: Keep both files.**
- **Race condition on push order**: If commits are pushed while build_type is still "legacy", a legacy deploy triggers immediately. **Decision: Switch API FIRST, then push.**
- **API call format**: Must omit `source` field when sending `build_type=workflow` — sending both may cause validation errors.
- **Repo slug needed**: Must validate with `gh repo view` before API calls.
- **`_future.t` file**: Old HTML snippet not used by generator — include in cleanup.
- **`kontakt/` directory**: Also an old static page (14 dirs total including kontakt/).

---

## Work Objectives

### Core Objective
Ensure every push to `gh-pages` triggers a GitHub Actions workflow that builds and deploys the generator-produced site, with zero competing deployment mechanisms.

### Concrete Deliverables
- GitHub Pages `build_type` changed from `"legacy"` to `"workflow"`
- Root `index.html` and `_future.t` removed from repo
- 14 old static directories removed: `belzebubs/`, `bzik/`, `ciecio/`, `hadfield/`, `karmiciel/`, `kodiak/`, `kontakt/`, `mama/`, `midguard/`, `pisto/`, `pzg/`, `spz/`, `winon/`, `zvyrke/`
- All 14+ unpushed commits pushed to `origin/gh-pages`
- Live site at `https://diablaq.com` serves generator-built content

### Definition of Done
- [ ] `gh api repos/{owner}/{repo}/pages --jq '.build_type'` returns `"workflow"`
- [ ] `curl -s https://diablaq.com | grep 'pico.min.css'` finds the new CSS framework
- [ ] `curl -s https://diablaq.com | grep 'mvp.css'` returns NO matches (old CSS gone)
- [ ] `gh api repos/{owner}/{repo}/pages --jq '.cname'` returns `"diablaq.com"`
- [ ] `git log origin/gh-pages..gh-pages --oneline` returns empty (fully pushed)

### Must Have
- GitHub Pages source = "GitHub Actions" (not "Deploy from branch")
- `CNAME` file preserved in repo root (builder copies it to dist/)
- `.nojekyll` file preserved in repo root (builder copies it to dist/)
- All old static HTML removed from repo
- Custom domain `diablaq.com` intact after switch

### Must NOT Have (Guardrails)
- **DO NOT** delete `CNAME` or `.nojekyll` — builder copies these to dist/ (builder.py:154-157)
- **DO NOT** delete `css/` or `img/` directories — these are source assets for the generator
- **DO NOT** modify `pages.yml` workflow — it's already correctly configured
- **DO NOT** modify `builder.py` or any generator source code
- **DO NOT** touch `main` branch — it's stale but out of scope
- **DO NOT** touch `dom` remote — only `origin` (GitHub) is in scope
- **DO NOT** push before the API switch is verified
- **DO NOT** send the `source` field in the `build_type: workflow` API call
- **DO NOT** modify `content/`, `templates/`, `tests/`, `scripts/`, `_migracja/`, `_penpot/`

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest + golden build tests)
- **Automated tests**: NO — this is a DevOps/config task, not a code change
- **Framework**: N/A
- **Primary verification**: Agent-executed QA via `gh api`, `curl`, `git` commands

### QA Policy
Every task includes agent-executed QA scenarios using Bash commands (gh CLI, curl, git).
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API/Config changes**: Use Bash (`gh api`, `curl`) — assert JSON fields and HTTP status codes
- **Git operations**: Use Bash (`git`) — verify branch state, push status, commit presence
- **Deployment**: Use Bash (`curl`) — check live site content, response codes

---

## Execution Strategy

### Parallel Execution Waves

> Strictly sequential — each wave depends on the previous wave's verification.
> No parallelism possible due to dependency chain.

```
Wave 1 (Prerequisites — validate environment):
└── Task 1: Validate prerequisites (gh auth, repo slug, current Pages config) [quick]

Wave 2 (API Switch — depends on Wave 1 repo slug):
└── Task 2: Switch GitHub Pages source from "legacy" to "workflow" [quick]

Wave 3 (Cleanup — depends on Wave 2 API switch verified):
└── Task 3: Remove old static files and commit [quick]

Wave 4 (Push — depends on Wave 3 commit):
└── Task 4: Push all commits to origin/gh-pages [quick]

Wave 5 (Verification — depends on Wave 4 push):
└── Task 5: Verify deployment and live site content [quick]

Critical Path: Task 1 → Task 2 → Task 3 → Task 4 → Task 5
Parallel Speedup: None (sequential dependency chain)
Max Concurrent: 1
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2 | 1 |
| 2 | 1 | 3 | 2 |
| 3 | 2 | 4 | 3 |
| 4 | 3 | 5 | 4 |
| 5 | 4 | — | 5 |

### Agent Dispatch Summary

- **Wave 1**: 1 task — T1 → `quick` (load_skills: [`git-master`])
- **Wave 2**: 1 task — T2 → `quick`
- **Wave 3**: 1 task — T3 → `quick` (load_skills: [`git-master`])
- **Wave 4**: 1 task — T4 → `quick` (load_skills: [`git-master`])
- **Wave 5**: 1 task — T5 → `quick`

---

## TODOs

---

- [x] 1. Validate Prerequisites

  **What to do**:
  - Run `gh auth status` to verify GitHub CLI is authenticated with sufficient permissions
  - Run `gh repo view --json nameWithOwner` to get the exact repo slug (expected: `dekoza/diablaq.com`)
  - Run `gh api repos/{owner}/{repo}/pages` to capture current Pages configuration as a baseline
  - Verify current branch is `gh-pages` and has the expected HEAD commit
  - Verify `CNAME` file exists in repo root and contains `diablaq.com`
  - Verify `.nojekyll` file exists in repo root
  - Verify old static files exist before removal (index.html, _future.t, product directories)

  **Must NOT do**:
  - Do NOT modify any files or settings in this task — validation only
  - Do NOT push anything

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple verification commands, no complex logic
  - **Skills**: [`git-master`]
    - `git-master`: Needed for git branch/status verification

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (solo)
  - **Blocks**: Task 2
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `.github/workflows/pages.yml:5` — Confirms workflow triggers on `gh-pages` branch
  - `diablaq_site/builder.py:154-157` — Shows builder copies CNAME and .nojekyll from root to dist/

  **External References**:
  - GitHub Pages API: `GET /repos/{owner}/{repo}/pages` returns `build_type`, `source`, `cname` fields

  **WHY Each Reference Matters**:
  - `pages.yml:5` — Confirms the trigger branch matches our dev branch (`gh-pages`)
  - `builder.py:154-157` — Proves CNAME/nojekyll are copied (not generated), so root copies must survive

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Verify GitHub CLI auth and repo access
    Tool: Bash
    Preconditions: gh CLI installed
    Steps:
      1. Run `gh auth status` — expect output contains "Logged in to github.com"
      2. Run `gh repo view --json nameWithOwner --jq '.nameWithOwner'` — expect "dekoza/diablaq.com"
      3. Run `gh api repos/dekoza/diablaq.com/pages --jq '.build_type'` — expect "legacy"
      4. Run `gh api repos/dekoza/diablaq.com/pages --jq '.cname'` — expect "diablaq.com"
    Expected Result: All 4 commands succeed with expected values
    Failure Indicators: Auth failure, wrong repo slug, unexpected build_type
    Evidence: .sisyphus/evidence/task-1-gh-auth-and-pages.txt

  Scenario: Verify files exist before cleanup
    Tool: Bash
    Preconditions: On gh-pages branch
    Steps:
      1. Run `test -f index.html && echo EXISTS || echo MISSING` — expect "EXISTS"
      2. Run `test -f _future.t && echo EXISTS || echo MISSING` — expect "EXISTS"
      3. Run `test -f CNAME && echo EXISTS || echo MISSING` — expect "EXISTS"
      4. Run `test -f .nojekyll && echo EXISTS || echo MISSING` — expect "EXISTS"
      5. Run `ls -d belzebubs/ bzik/ ciecio/ hadfield/ karmiciel/ kodiak/ kontakt/ mama/ midguard/ pisto/ pzg/ spz/ winon/ zvyrke/ 2>&1` — expect all 14 dirs listed
      6. Run `git branch --show-current` — expect "gh-pages"
    Expected Result: All files and directories exist, on correct branch
    Failure Indicators: Any file MISSING, wrong branch
    Evidence: .sisyphus/evidence/task-1-file-inventory.txt
  ```

  **Evidence to Capture:**
  - [ ] task-1-gh-auth-and-pages.txt — full output of gh auth, repo view, pages API
  - [ ] task-1-file-inventory.txt — inventory of files before cleanup

  **Commit**: NO

- [ ] 2. Switch GitHub Pages Source to "GitHub Actions"

  **What to do**:
  - Run `gh api -X PUT repos/dekoza/diablaq.com/pages -F build_type=workflow` to switch from legacy to Actions deployment
  - Note: This returns HTTP 204 No Content on success (no JSON body) — this is expected, NOT an error
  - Note: Do NOT include a `source` field in the request — only send `build_type=workflow`
  - Verify the switch by running `gh api repos/dekoza/diablaq.com/pages --jq '.build_type'` — must return `"workflow"`
  - Verify custom domain preserved by running `gh api repos/dekoza/diablaq.com/pages --jq '.cname'` — must return `"diablaq.com"`
  - If verification fails, STOP. Do not proceed to Task 3.

  **Must NOT do**:
  - Do NOT send `source` field in the PUT request — only `build_type`
  - Do NOT push any commits yet — switch must be confirmed BEFORE pushing
  - Do NOT modify any files in the repo

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single API call + verification
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (solo)
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:

  **External References**:
  - GitHub Pages REST API: `PUT /repos/{owner}/{repo}/pages` with body `{"build_type": "workflow"}`
  - Expected response: HTTP 204 No Content (success is silent — no JSON body returned)
  - Verification endpoint: `GET /repos/{owner}/{repo}/pages` returns full config including `build_type` and `cname`

  **WHY Each Reference Matters**:
  - API format: The PUT must omit `source` — sending both `source` and `build_type=workflow` may cause validation errors
  - 204 response: Agents often mistake no-body responses for errors — this is expected success

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Switch Pages source and verify
    Tool: Bash
    Preconditions: Task 1 verified gh auth + repo slug
    Steps:
      1. Run `gh api -X PUT repos/dekoza/diablaq.com/pages -F build_type=workflow 2>&1` — expect empty output or HTTP 204
      2. Run `gh api repos/dekoza/diablaq.com/pages --jq '.build_type'` — expect "workflow"
      3. Run `gh api repos/dekoza/diablaq.com/pages --jq '.cname'` — expect "diablaq.com"
      4. Run `gh api repos/dekoza/diablaq.com/pages --jq '.https_enforced'` — expect "true"
    Expected Result: build_type is "workflow", custom domain and HTTPS preserved
    Failure Indicators: build_type still "legacy", cname changed or null, API error
    Evidence: .sisyphus/evidence/task-2-api-switch.txt
  ```

  **Evidence to Capture:**
  - [ ] task-2-api-switch.txt — PUT response + GET verification output

  **Commit**: NO

- [ ] 3. Remove Old Static Files and Commit

  **What to do**:
  - Remove root `index.html` (old static homepage using mvp.css)
  - Remove `_future.t` (old HTML snippet, not used by generator)
  - Remove 14 old static product directories, each containing only `index.html`:
    `git rm -r belzebubs/ bzik/ ciecio/ hadfield/ karmiciel/ kodiak/ kontakt/ mama/ midguard/ pisto/ pzg/ spz/ winon/ zvyrke/`
  - **DO NOT remove**: `CNAME`, `.nojekyll`, `css/`, `img/` — these are source files the builder needs
  - Verify after removal: `CNAME` still exists, `.nojekyll` still exists, `css/` still exists, `img/` still exists
  - Commit: `chore: remove old static HTML files superseded by generator`

  **Must NOT do**:
  - Do NOT delete `CNAME` — builder.py:154-157 copies this to dist/. Deleting it breaks custom domain.
  - Do NOT delete `.nojekyll` — builder.py:154-157 copies this to dist/. Deleting it enables Jekyll.
  - Do NOT delete `css/` — builder.py:145 copies this to dist/ as source assets
  - Do NOT delete `img/` — builder.py:146 copies this to dist/ as source assets
  - Do NOT push yet — Task 4 handles the push

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple git rm commands + commit
  - **Skills**: [`git-master`]
    - `git-master`: Needed for proper git rm and commit

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (solo)
  - **Blocks**: Task 4
  - **Blocked By**: Task 2

  **References**:

  **Pattern References**:
  - `diablaq_site/builder.py:145-146` — Builder copies `css/` and `img/` from root to dist/ (DO NOT DELETE)
  - `diablaq_site/builder.py:154-157` — Builder copies `CNAME` and `.nojekyll` from root to dist/ (DO NOT DELETE)

  **WHY Each Reference Matters**:
  - builder.py:145-146 — Proves `css/` and `img/` are SOURCE assets, not old static files. Removing them breaks the build.
  - builder.py:154-157 — Proves `CNAME` and `.nojekyll` are COPIED to dist/, not generated. Removing them from root means dist/ won't get them.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Remove old files and verify protected files survive
    Tool: Bash
    Preconditions: On gh-pages branch, API switch verified (Task 2)
    Steps:
      1. Run `git rm index.html _future.t` — expect success
      2. Run `git rm -r belzebubs/ bzik/ ciecio/ hadfield/ karmiciel/ kodiak/ kontakt/ mama/ midguard/ pisto/ pzg/ spz/ winon/ zvyrke/` — expect success
      3. Run `test -f CNAME && echo SAFE || echo DELETED` — expect "SAFE"
      4. Run `test -f .nojekyll && echo SAFE || echo DELETED` — expect "SAFE"
      5. Run `test -d css && echo SAFE || echo DELETED` — expect "SAFE"
      6. Run `test -d img && echo SAFE || echo DELETED` — expect "SAFE"
      7. Run `test -f index.html && echo STILL_EXISTS || echo REMOVED` — expect "REMOVED"
      8. Run `test -d belzebubs && echo STILL_EXISTS || echo REMOVED` — expect "REMOVED"
      9. Run `git commit -m "chore: remove old static HTML files superseded by generator"` — expect success
    Expected Result: Old files removed, protected files intact, clean commit
    Failure Indicators: Protected file deleted, git rm fails, commit fails
    Evidence: .sisyphus/evidence/task-3-file-cleanup.txt

  Scenario: Verify nothing unexpected was staged
    Tool: Bash
    Preconditions: Commit from previous scenario created
    Steps:
      1. Run `git diff HEAD~1 --stat` — expect only: index.html, _future.t, and 14 product directories deleted
      2. Verify NO unexpected files in the diff (no css/, img/, CNAME, .nojekyll, content/, templates/)
    Expected Result: Only old static files in the commit diff
    Failure Indicators: Protected files appear in diff, unexpected changes
    Evidence: .sisyphus/evidence/task-3-commit-diff.txt
  ```

  **Evidence to Capture:**
  - [ ] task-3-file-cleanup.txt — git rm output + file existence checks
  - [ ] task-3-commit-diff.txt — git diff --stat of the cleanup commit

  **Commit**: YES
  - Message: `chore: remove old static HTML files superseded by generator`
  - Files: `index.html`, `_future.t`, `belzebubs/`, `bzik/`, `ciecio/`, `hadfield/`, `karmiciel/`, `kodiak/`, `kontakt/`, `mama/`, `midguard/`, `pisto/`, `pzg/`, `spz/`, `winon/`, `zvyrke/`
  - Pre-commit: `test -f CNAME && test -f .nojekyll && test -d css && test -d img`

- [ ] 4. Push All Commits to origin/gh-pages

  **What to do**:
  - Run `git push origin gh-pages` to push all local commits (14 previously unpushed + 1 cleanup commit)
  - Verify push succeeded: `git log origin/gh-pages..gh-pages --oneline` should return empty
  - Verify the Actions workflow was triggered: `gh run list --workflow=pages.yml --limit 1 --json status,conclusion`
  - Wait for the workflow to complete (poll every 30s, max 5 minutes)

  **Must NOT do**:
  - Do NOT force-push (`--force`) — regular push should work
  - Do NOT push to any branch other than `gh-pages`
  - Do NOT push to `dom` remote

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single push command + polling
  - **Skills**: [`git-master`]
    - `git-master`: Needed for push and branch verification

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (solo)
  - **Blocks**: Task 5
  - **Blocked By**: Task 3

  **References**:

  **Pattern References**:
  - `.github/workflows/pages.yml:3-5` — Workflow trigger: `on: push: branches: ["gh-pages"]`

  **WHY Each Reference Matters**:
  - pages.yml:3-5 — Confirms pushing to `gh-pages` will trigger the build+deploy workflow

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Push commits and verify workflow triggered
    Tool: Bash
    Preconditions: Task 3 commit completed, API switched to workflow mode
    Steps:
      1. Run `git push origin gh-pages` — expect success with commit count in output
      2. Run `git log origin/gh-pages..gh-pages --oneline` — expect empty output (fully pushed)
      3. Run `gh run list --workflow=pages.yml --limit 1 --json status,event,headBranch` — expect status: "in_progress" or "completed", event: "push", headBranch: "gh-pages"
    Expected Result: All commits pushed, workflow running
    Failure Indicators: Push rejected, commits still unpushed, no workflow triggered
    Evidence: .sisyphus/evidence/task-4-push-and-workflow.txt

  Scenario: Wait for workflow to complete successfully
    Tool: Bash
    Preconditions: Push completed, workflow triggered
    Steps:
      1. Poll every 30s for up to 5 minutes: `gh run list --workflow=pages.yml --limit 1 --json conclusion --jq '.[0].conclusion'`
      2. Wait until result is "success"
      3. If result is "failure" — run `gh run view --log-failed` to capture error
    Expected Result: Workflow conclusion is "success"
    Failure Indicators: conclusion is "failure" or "cancelled", timeout after 5 minutes
    Evidence: .sisyphus/evidence/task-4-workflow-completion.txt
  ```

  **Evidence to Capture:**
  - [ ] task-4-push-and-workflow.txt — push output + workflow status
  - [ ] task-4-workflow-completion.txt — final workflow status/conclusion

  **Commit**: NO (push only, no new commit)

- [ ] 5. Verify Live Site Deployment

  **What to do**:
  - Wait up to 2 minutes after workflow completion for CDN propagation
  - Verify the live site serves generator-built content (new CSS framework)
  - Verify old static site content is NOT served
  - Verify custom domain and HTTPS work correctly
  - Verify old product pages return 404 (not the old static HTML)

  **Must NOT do**:
  - Do NOT modify any files or settings
  - Do NOT re-push or re-deploy — verification only

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple curl/HTTP verification commands
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (solo)
  - **Blocks**: None
  - **Blocked By**: Task 4

  **References**:

  **Pattern References**:
  - `templates/` — Generator templates use `pico.min.css` and `fonts.css` (new stack fingerprint)
  - Old static `index.html` used `mvp.css` (old stack fingerprint) — now removed

  **WHY Each Reference Matters**:
  - CSS framework difference (`pico.min.css` vs `mvp.css`) is the definitive fingerprint for which version is being served

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Verify new site content is served
    Tool: Bash
    Preconditions: Workflow completed successfully (Task 4)
    Steps:
      1. Run `sleep 120` — wait for CDN propagation
      2. Run `curl -sL https://diablaq.com | grep -c 'pico.min.css'` — expect >= 1 (new CSS present)
      3. Run `curl -sL https://diablaq.com | grep -c 'mvp.css'` — expect 0 (old CSS absent)
      4. Run `curl -sL https://diablaq.com | grep -c 'Wydawnictwo Diablaq'` — expect >= 1 (title present)
    Expected Result: New CSS framework present, old CSS absent, site title correct
    Failure Indicators: mvp.css found, pico.min.css not found
    Evidence: .sisyphus/evidence/task-5-site-content.txt

  Scenario: Verify old static pages return 404
    Tool: Bash
    Preconditions: CDN propagation wait completed
    Steps:
      1. Run `curl -sI https://diablaq.com/belzebubs/ | head -1` — expect HTTP status 404
      2. Run `curl -sI https://diablaq.com/kontakt/ | head -1` — expect HTTP status 404
      Note: Some old paths may now be served by the generator if it creates them. That's fine — verify the content uses pico.min.css, not mvp.css.
    Expected Result: Old static pages either 404 or serve new generator content
    Failure Indicators: Old mvp.css-based HTML returned
    Evidence: .sisyphus/evidence/task-5-old-pages-404.txt

  Scenario: Verify custom domain and HTTPS
    Tool: Bash
    Preconditions: CDN propagation wait completed
    Steps:
      1. Run `curl -sI https://diablaq.com | grep -i 'HTTP/'` — expect HTTP/2 200
      2. Run `curl -sI http://diablaq.com | grep -i 'location'` — expect redirect to https://diablaq.com
      3. Run `gh api repos/dekoza/diablaq.com/pages --jq '.cname'` — expect "diablaq.com"
    Expected Result: HTTPS works, HTTP redirects, custom domain active
    Failure Indicators: Non-200 on HTTPS, no redirect from HTTP, cname null
    Evidence: .sisyphus/evidence/task-5-domain-and-https.txt
  ```

  **Evidence to Capture:**
  - [ ] task-5-site-content.txt — curl output showing CSS framework check
  - [ ] task-5-old-pages-404.txt — HTTP status for old product pages
  - [ ] task-5-domain-and-https.txt — HTTPS and domain verification

  **Commit**: NO

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> Single review agent verifies end-to-end. This is a config task, not code, so a full 4-agent review is overkill.

- [ ] F1. **Deployment Verification** — `quick`
  Run all Definition of Done checks:
  - `gh api repos/{owner}/{repo}/pages --jq '.build_type'` → `"workflow"`
  - `gh api repos/{owner}/{repo}/pages --jq '.cname'` → `"diablaq.com"`
  - `git log origin/gh-pages..gh-pages --oneline` → empty
  - `curl -s https://diablaq.com | grep 'pico.min.css'` → match
  - `curl -s https://diablaq.com | grep 'mvp.css'` → no match
  - `curl -sI https://diablaq.com/belzebubs/ | head -1` → 404
  - Verify `CNAME` and `.nojekyll` exist in repo root
  - Verify `css/` and `img/` directories exist in repo root
  Output: `API [PASS/FAIL] | Domain [PASS/FAIL] | Git [PASS/FAIL] | Content [PASS/FAIL] | VERDICT`

---

## Commit Strategy

- **Wave 3**: `chore: remove old static HTML files superseded by generator` — index.html, _future.t, belzebubs/, bzik/, ciecio/, hadfield/, karmiciel/, kodiak/, kontakt/, mama/, midguard/, pisto/, pzg/, spz/, winon/, zvyrke/

---

## Success Criteria

### Verification Commands
```bash
gh api repos/dekoza/diablaq.com/pages --jq '.build_type'  # Expected: "workflow"
gh api repos/dekoza/diablaq.com/pages --jq '.cname'        # Expected: "diablaq.com"
git log origin/gh-pages..gh-pages --oneline                 # Expected: (empty)
curl -s https://diablaq.com | grep -c 'pico.min.css'       # Expected: >= 1
curl -s https://diablaq.com | grep -c 'mvp.css'            # Expected: 0
curl -sI https://diablaq.com/belzebubs/ | head -1          # Expected: HTTP/2 404
```

### Final Checklist
- [ ] GitHub Pages build_type = "workflow"
- [ ] Custom domain diablaq.com active and HTTPS enforced
- [ ] All old static files removed from repo
- [ ] CNAME and .nojekyll preserved in repo root
- [ ] css/ and img/ source directories preserved
- [ ] All commits pushed to origin/gh-pages
- [ ] Actions workflow completed successfully
- [ ] Live site serves generator-built content (pico.min.css present)
- [ ] Old static site no longer served (mvp.css absent)
