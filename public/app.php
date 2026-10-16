<?php
declare(strict_types=1);

function config(string $key, string $default = ''): string
{
    static $values = null;
    if ($values === null) {
        $values = [];
        $path = __DIR__ . '/.env';
        if (is_file($path)) {
            foreach (file($path, FILE_IGNORE_NEW_LINES) as $line) {
                if (preg_match('/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/', $line, $match)) {
                    $values[$match[1]] = trim($match[2], "\"'");
                }
            }
        }
    }
    $value = getenv($key);
    return $value === false ? ($values[$key] ?? $default) : $value;
}

function database(): PDO
{
    static $db = null;
    if ($db === null) {
        $path = config('SURRENT_DATABASE', dirname(__DIR__) . '/surrentech_php.sqlite3');
        $db = new PDO('sqlite:' . $path, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        chmod($path, 0600);
        $db->exec('PRAGMA busy_timeout=5000');
        $db->exec('CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            remote_addr TEXT NOT NULL,
            user_agent TEXT NOT NULL,
            handled INTEGER NOT NULL DEFAULT 0
        )');
        $db->exec('CREATE INDEX IF NOT EXISTS consult_created ON consult_requests(created_at)');
        $db->exec('CREATE TABLE IF NOT EXISTS login_attempts (ip TEXT PRIMARY KEY, attempts INTEGER NOT NULL, since INTEGER NOT NULL)');
    }
    return $db;
}

function redirect_to(string $path): never
{
    header('Location: ' . $path, true, 303);
    exit;
}

function csrf_valid(): bool
{
    return is_string($_POST['csrf_token'] ?? null)
        && hash_equals($_SESSION['csrf'], $_POST['csrf_token']);
}

function escape(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
