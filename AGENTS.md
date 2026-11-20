# Static Pages publishing conventions

- This is the shared repository for all of the user's static pages. Add each new page in its own directory here; do not create a repository per page.
- Drafts, source data, screenshots, and intermediate output belong in the repository-root `artifacts/<task>/` directory. It is ignored by Git and outside the Pages publishing source. Create it locally when needed; do not force-add it.
- Create and verify a complete reviewable page in `artifacts/` first. Promote the specific output only after the user confirms publication of that output; unrelated past publication permission is not blanket approval for new drafts. Do not write drafts into `docs/` or update the public navigation before that confirmation.
- Confirmed financial reports belong at `docs/reports/<symbol>/<YYYY-MM-DD>/index.html`. Other confirmed pages use `docs/pages/<slug>/index.html`; tools use `docs/tools/<slug>/index.html`.
- Keep `docs/index.html` as the public navigation page. On confirmed publication update its entries, visible page count, and the repository-root README. Preserve existing entries and archived report dates.
- Publish only the `docs/` directory from the existing `main` branch via GitHub Pages; retain `docs/.nojekyll`. The base URL is `https://wvliteam.github.io/static-pages/`. The physical `docs/` prefix is not part of public URLs.
- Use relative links and asset paths that work under this base URL. Prefer self-contained HTML where useful. Do not add server-side requirements to published pages.
- Publish only intended page content and assets. Keep `artifacts/` outside `docs/` and untracked. Files committed to this public repository remain readable on GitHub even if they are outside `docs/`; this layout excludes drafts from publication, not a directory access-control feature. Keep credentials and account data out of both Git and published pages.
- Check new page URLs and the navigation homepage after deployment. State clearly whether a report is a dated snapshot or updates automatically.
