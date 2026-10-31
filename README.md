# Elevano Capital factsheet

Daily performance report (QuantStats) for Elevano Capital, published at
https://factsheet.elevanocapital.com.

## How it works

`generate.py` reads `nav_history` from Supabase, builds the QuantStats HTML
report and writes it to `FACTSHEET_OUTPUT` (default: the legacy Render path).

The report is a single self-contained HTML file, so it is hosted as a static
page on **GitHub Pages**. The workflow in
`.github/workflows/publish-factsheet.yml`:

- runs every day at 00:30 UTC, on every push to `main`, and on demand
  (Actions tab, "Publish factsheet", *Run workflow*);
- regenerates the report with the `SUPABASE_URL` / `SUPABASE_KEY` secrets;
- publishes it to GitHub Pages. If generation fails, the previous version stays
  online.

Costs nothing: the repository is public, so Actions minutes and Pages hosting
are free.

## One-time setup (after merging to `main`)

1. **Secrets**: Settings → Secrets and variables → Actions → add
   `SUPABASE_URL` and `SUPABASE_KEY` (same values as on Railway).
2. **Pages**: Settings → Pages → *Build and deployment* → Source:
   **GitHub Actions**.
3. **Custom domain**: still in Settings → Pages, enter
   `factsheet.elevanocapital.com` and tick *Enforce HTTPS* once the certificate
   is issued.
4. **DNS**: at the registrar, point the `factsheet` CNAME record from
   `elevano-factsheet-production.up.railway.app` to `mambui.github.io`.
5. Run the workflow once from the Actions tab and check the page.
6. Once the domain resolves to GitHub Pages, delete the `elevano-factsheet`
   service (and its `factsheet-watchdog`, or keep it: it just polls the URL) on
   Railway. `server.py` and `start.sh` only exist for that Railway container and
   can then be removed.

## Local run

```bash
pip install -r requirements.txt
SUPABASE_URL=... SUPABASE_KEY=... FACTSHEET_OUTPUT=site/index.html python generate.py
```
