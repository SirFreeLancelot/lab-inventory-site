# Lab inventory site

Edit the Google Sheet (tabs `locations`, `items`, `stock`); the site and printable checklist rebuild from it.

## One-time setup
1. Create a GitHub repo, push this folder to `main`.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. **Actions → Build and deploy → Run workflow**. The site appears at `https://<user>.github.io/<repo>/`.
4. The CSV links are at the top of `.github/workflows/build.yml`; change them if you republish a tab.

## Day to day
- Edit the sheet, then **Actions → Build and deploy → Run workflow** (it also runs nightly). Published CSVs can lag a few minutes.
- If a build fails, the error says which row is wrong (unknown location/item id, bad qty).
- `data/` holds a backup copy of the CSVs, updated on each build.

## Pages and URLs (stable; never reuse an id)
- `/` home, `/tree.html`, `/summary.html`, `/checklist.html`
- `/locations/<location_id>/` and `/items/<item_id>/` — point QR codes here.
- Photos: put a file in `photos/` and enter its filename in the `photo` column of `items`.

## Printing the checklist
Open `/checklist.html`, Ctrl+P, paper A4, margins "Default" or "None", turn on "Background graphics" off. One box per unit; tick one for each unit found.
