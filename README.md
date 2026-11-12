# Sharp Eye case packs

## Upload a new case pack

Upload the ZIP from Gemini as-is into this repository's `uploads/` folder, then commit it. Do not unzip it or edit `levels.json`.

The included GitHub Action automatically validates the ZIP, extracts its images, adds the seven levels to the root `levels.json`, and increments the manifest version. After processing, it removes the uploaded ZIP from the published files. GitHub Pages then publishes the updated manifest and images. Sharp Eye checks for new cases each time it opens and adds them to Detective Cases; players can also tap Sync.

When setting up the repository, keep `.github/workflows/import-case-zips.yml` and `.github/workflows/deploy-pages.yml` in place. Allow GitHub Actions to write to repository contents. Set the Pages publishing source to **GitHub Actions** so the app can read `levels.json` and the group image folders.

The ZIP must contain `levels.json` at its root, with no wrapper folder, exactly seven levels in one unique group, five differences with text hints per level, and all referenced image files inside that group's folder. The archive format is described in `GEMINI_THRILLER_CASE_PACK_PROMPT.md` in the app repository.

If the ZIP is invalid or reuses a published group ID or level ID, the action fails without changing the published manifest. Check the repository's Actions tab for the reason, correct the archive, then upload the corrected ZIP.

Players still need to download a case set in the game; the existing ad unlock rules remain in effect. The app caches downloaded level images for offline play.

## One-time GitHub Pages setup

1. Use the public repository `gdsa006/sharpeye` and add the contents of this folder at the repository root. Keep `.nojekyll`, `index.html`, `levels.json`, the `group-*` folders, and `.github/workflows/`.
2. In the repository, open **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**.
3. In **Settings → Actions → General**, allow GitHub Actions to read and write repository contents. The ZIP importer needs this to commit processed packs.
4. Push to `main` or `master`. The Pages workflow publishes the files. ZIP uploads are imported and deployed by the importer workflow.
5. The app uses `https://gdsa006.github.io/sharpeye/` as its case feed URL. Rebuild the app after the feed is deployed.

GitHub Pages is available for public repositories on GitHub Free. Pages content is public on the internet: the manifest includes difference coordinates and hints, so anyone can read or download those answers. Do not upload private information or art you do not want copied.

After setup, open the Pages URL in a browser. The landing page shows the case-set count when `levels.json` is reachable. To add a pack, upload its ZIP as-is into `uploads/` and commit it; GitHub Actions will import and publish it automatically.
