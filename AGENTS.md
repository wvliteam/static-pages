# Static Pages publishing conventions

- Reuse `wvliteam/static-pages` for all pages. Do not create a repository per page.
- `main/docs/` contains only approved formal pages. Financial reports use `docs/reports/<symbol>/<YYYY-MM-DD>/index.html`; other pages use `docs/pages/<slug>/index.html` or `docs/tools/<slug>/index.html`.
- Develop each new page on a `preview/<task>` branch. Commit only reviewable HTML and required assets at `artifacts/<task>/public/`; use lowercase task slugs. Keep raw data, logs, screenshots, credentials, and local tooling in ignored `scratch/` or outside the checkout.
- Open a same-repository PR targeting `main` to trigger a Pages preview. The workflow runs trusted main scripts and reads static files at the PR head SHA. Never run PR build scripts with privileged credentials.
- The preview URL is `https://wvliteam.github.io/static-pages/previews/pr-<number>/<task>/`. The deployment injects a preview banner and noindex metadata; source HTML stays clean. Preview URLs are public, not access controlled.
- Preview does not imply formal approval. After the user approves this specific version, move its final files from `artifacts/<task>/public/` to their formal `docs/` destination on the PR branch, remove tracked draft artifacts, and update `docs/index.html` plus the README page list. Only then merge that PR. Do not repeatedly ask for approval already given.
- Never merge tracked `artifacts/` into `main`. Do not add draft links or draft counts to the formal homepage. Preserve other reports, their dates, and existing user changes.
- Pages uses GitHub Actions. The generated `gh-pages` branch contains main/docs and previews from all open eligible PRs; do not edit or merge it into main. `previews/` is reserved for generated output and must not exist in main/docs.
- Every run rebuilds the complete deployment so previews do not overwrite formal pages or one another. Closing/merging a PR removes its preview on the next successful deployment.
- Source skill files live at `skills/static-page-publisher/`, outside docs. Keep them portable and free of tokens and machine-specific paths. Update the locally installed copy when changing the tracked skill, and vice versa.
- Use relative links that work under `/static-pages/` and the nested preview path. On deployment check the public deployment.json against the main and PR head SHAs, then verify the actual preview/formal HTML content.
