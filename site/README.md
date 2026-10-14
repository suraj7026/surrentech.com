# surrentech.com — Django site

The landing page from `landing/index.html` rebuilt as a Django app and deployed to the
HostIndia cPanel account (`/home/surrente/public_html`, served by LiteSpeed/Passenger with Python 3.12).

## Layout

- `surrentech_site/` — project settings (everything configurable via `.env`)
- `website/` — landing page view, `ConsultRequest` model (consultation form submissions), admin
- `website/templates/website/home.html` — the landing page
- `passenger_wsgi.py` — cPanel entry point; unpacks `_vendor.tar.gz`, loads `.env`, runs migrations on start
- `manage.py`, `requirements.txt`, `.htaccess`

## Server layout

`/home/surrente/public_html/` **is** the Django app root (same pattern as `ashramstay.surrentech.com`).
The SQLite database lives one level up, outside the web root: `/home/surrente/surrentech_site.sqlite3`.
Python packages are shipped as `_vendor.tar.gz` (the host has no pip over FTP) and unpacked by
`passenger_wsgi.py` on startup.

## One-time server setup (cPanel UI)

1. cPanel → **Setup Python App** → Create Application:
   - Python version **3.12**, Application root **public_html**, Application URL **surrentech.com**
   - This creates `/home/surrente/virtualenv/public_html/3.12/` (the `.htaccess` Passenger block points there).
2. That's it — all code, the `.env` and the vendor bundle arrive over FTP.

Admin: `https://surrentech.com/manage-console/` (login created from `DJANGO_ADMIN_EMAIL` / `DJANGO_ADMIN_PASSWORD`
in `.env` on first boot; remove those two lines afterwards).

## Deploys

Push to `main` → `.github/workflows/deploy.yml` runs checks, builds the Linux vendor bundle,
collects static files, timestamps `passenger_wsgi.py` (forces an app restart) and uploads the
changed files over FTPS with `SamKirkland/FTP-Deploy-Action`. `.env`, `_vendor/`, `tmp/` and logs
on the server are never touched by the sync.

Required GitHub secrets: `FTP_USERNAME` = `surrenhomepage@surrentech.com`, `FTP_PASSWORD`.

## Local development

```bash
cd site
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
