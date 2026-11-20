# Static Pages publishing conventions

- This is the shared repository for all of the user's static pages. Add each new page in its own directory here; do not create a repository per page.
- Financial reports belong at `reports/<symbol>/<YYYY-MM-DD>/index.html`. Other standalone pages use `pages/<slug>/index.html`; tools use `tools/<slug>/index.html`.
- Keep the root `index.html` as the navigation page. Update its entries, visible page count, and README when adding a page. Preserve existing entries and archived report dates.
- Publish from the existing `main` branch root via GitHub Pages; retain `.nojekyll`. The base URL is `https://wvliteam.github.io/static-pages/`.
- Use relative links and asset paths that work under this base URL. Prefer self-contained HTML where useful. Do not add server-side requirements to published pages.
- Publish only intended page content and assets. Keep credentials, account data, unrelated workspace files, and temporary browser tooling outside the repository.
- Check new page URLs and the navigation homepage after deployment. State clearly whether a report is a dated snapshot or updates automatically.
