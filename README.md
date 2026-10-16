# Surren Technologies website

The production site runs on PHP 8.2 in `/home/surrente/public_html` at
[ surrentech.com ](https://surrentech.com). No Python app or Composer installation is required.
The existing design and interactions are preserved in `public/home.php`.

- `public/index.php`: home, consultation submission, health and management routes.
- `public/app.php`: environment configuration and SQLite storage.
- `public/admin.php`: authenticated consultation list and handled status.
- `public/assets/`: the original brand images.
- `site/`: retained Django source; no longer deployed.

Consultations are stored outside the document root in
`/home/surrente/surrentech_php.sqlite3`. The app creates its tables automatically.
The existing `.env` is retained on the server and is never uploaded by CI.

Management: `/manage-console/`. Configure `SURRENT_ADMIN_EMAIL` and
`SURRENT_ADMIN_PASSWORD_HASH` (generated with PHP `password_hash`) in the server `.env`.
The previous `DJANGO_ADMIN_EMAIL` / `DJANGO_ADMIN_PASSWORD` settings also work if already
present. Without credentials, management stays disabled; the public site and consultation
form continue working. No outgoing email is sent automatically.

Push to `main` to lint PHP, run isolated HTTP/database/authentication tests, deploy over
certificate-verified FTPS, and check both domain names, health and the logo.
GitHub secrets: `FTP_USERNAME` and `FTP_PASSWORD`.

```sh
python3 tests/test_php.py
php -S 127.0.0.1:8000 -t public tests/router.php
```

The local router is for development only. Production uses `public/.htaccess`, which
routes only the application endpoints and image assets and blocks legacy source files.
