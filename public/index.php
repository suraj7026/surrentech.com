<?php
declare(strict_types=1);
require __DIR__ . '/app.php';

ini_set('display_errors', '0');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: strict-origin-when-cross-origin');
header('Cache-Control: no-store');
$secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
if ($secure) {
    header('Strict-Transport-Security: max-age=2592000');
}

set_exception_handler(function (Throwable $error): void {
    error_log('Surrentech PHP: ' . $error->getMessage());
    http_response_code(503);
    echo 'The site is temporarily unavailable. Please try again shortly.';
});

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];
if (!in_array($method, ['GET', 'HEAD', 'POST'], true)) {
    http_response_code(405);
    header('Allow: GET, HEAD, POST');
    exit;
}
if ($path === '/healthz') {
    database()->query('SELECT 1');
    header('Content-Type: text/plain; charset=utf-8');
    echo 'ok';
    exit;
}

session_name('surrentech_session');
ini_set('session.use_strict_mode', '1');
session_set_cookie_params(['httponly' => true, 'secure' => $secure, 'samesite' => 'Lax', 'path' => '/']);
session_start();
$_SESSION['csrf'] ??= bin2hex(random_bytes(32));
if ($path === '/form-token' && $method === 'GET') {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['csrf_token' => $_SESSION['csrf']]);
    exit;
}
$formError = '';
$sent = ($_GET['sent'] ?? '') === '1';

if ($path === '/consult') {
    if ($method !== 'POST') {
        http_response_code(405);
        header('Allow: POST');
        exit;
    }
    if (!csrf_valid()) {
        http_response_code(403);
        echo 'Please reload the page and submit the form again.';
        exit;
    }
    if (trim((string) ($_POST['website'] ?? '')) !== '') {
        redirect_to('/?sent=1#contact');
    }
    $email = strtolower(trim((string) ($_POST['email'] ?? '')));
    if (strlen($email) > 254 || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(422);
        $formError = 'Please enter a valid work email address.';
    } else {
        $db = database();
        $ip = $_SERVER['REMOTE_ADDR'] ?? '';
        $recent = $db->prepare('SELECT COUNT(*) FROM consult_requests WHERE remote_addr = ? AND created_at > ?');
        $recent->execute([$ip, gmdate('Y-m-d H:i:s', time() - 3600)]);
        if ((int) $recent->fetchColumn() >= 10) {
            http_response_code(429);
            $formError = 'Too many requests. Please try later or contact us directly.';
        } else {
            $insert = $db->prepare('INSERT INTO consult_requests (email, created_at, remote_addr, user_agent) VALUES (?, ?, ?, ?)');
            $insert->execute([$email, gmdate('Y-m-d H:i:s'), $ip, substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 300)]);
            redirect_to('/?sent=1#contact');
        }
    }
} elseif (str_starts_with((string) $path, '/manage-console')) {
    require __DIR__ . '/admin.php';
    exit;
} elseif (!in_array($path, ['/', '/index.php'], true)) {
    http_response_code(404);
    echo 'Page not found.';
    exit;
} elseif ($method === 'POST') {
    http_response_code(405);
    exit;
}
require __DIR__ . '/home.php';
