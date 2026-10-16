<?php
declare(strict_types=1);
$errorMessage = '';
$adminEmail = config('SURRENT_ADMIN_EMAIL', config('DJANGO_ADMIN_EMAIL'));
$adminHash = config('SURRENT_ADMIN_PASSWORD_HASH');
$legacyPassword = config('DJANGO_ADMIN_PASSWORD');
if (!$adminEmail || (!$adminHash && !$legacyPassword)) {
    http_response_code(503);
    echo 'The management login has not been configured.';
    return;
}
if (isset($_SESSION['admin_until']) && $_SESSION['admin_until'] < time()) {
    unset($_SESSION['admin_until']);
}
$authenticated = isset($_SESSION['admin_until']);
if ($method === 'POST') {
    if (!csrf_valid()) {
        http_response_code(403);
        echo 'Please reload this page and try again.';
        return;
    }
    $action = $_POST['action'] ?? 'login';
    if ($action === 'logout') {
        $_SESSION = [];
        session_destroy();
        redirect_to('/manage-console/');
    }
    if ($authenticated && $action === 'handled') {
        $update = database()->prepare('UPDATE consult_requests SET handled = 1 WHERE id = ?');
        $update->execute([(int) ($_POST['id'] ?? 0)]);
        redirect_to('/manage-console/');
    }
    if (!$authenticated && $action === 'login') {
        $db = database();
        $ip = $_SERVER['REMOTE_ADDR'] ?? '';
        $lookup = $db->prepare('SELECT attempts, since FROM login_attempts WHERE ip = ?');
        $lookup->execute([$ip]);
        $attempt = $lookup->fetch(PDO::FETCH_ASSOC);
        $limited = $attempt && (int) $attempt['since'] > time() - 900 && (int) $attempt['attempts'] >= 10;
        $password = (string) ($_POST['password'] ?? '');
        $passwordOk = $adminHash ? password_verify($password, $adminHash) : hash_equals($legacyPassword, $password);
        if (!$limited && hash_equals($adminEmail, (string) ($_POST['email'] ?? '')) && $passwordOk) {
            session_regenerate_id(true);
            $_SESSION['admin_until'] = time() + 1800;
            $_SESSION['csrf'] = bin2hex(random_bytes(32));
            $db->prepare('DELETE FROM login_attempts WHERE ip = ?')->execute([$ip]);
            redirect_to('/manage-console/');
        }
        $count = ($attempt && (int) $attempt['since'] > time() - 900) ? (int) $attempt['attempts'] + 1 : 1;
        $since = $count === 1 ? time() : (int) $attempt['since'];
        $db->prepare('INSERT OR REPLACE INTO login_attempts (ip, attempts, since) VALUES (?, ?, ?)')->execute([$ip, $count, $since]);
        http_response_code($limited ? 429 : 401);
        $errorMessage = $limited ? 'Too many login attempts. Please try again in 15 minutes.' : 'Email or password is incorrect.';
    }
}
$requests = $authenticated ? database()->query('SELECT id, email, created_at, handled FROM consult_requests ORDER BY id DESC LIMIT 500')->fetchAll(PDO::FETCH_ASSOC) : [];
?>
<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Consultation requests — Surren Technologies</title>
<style>body{font:16px/1.6 system-ui,sans-serif;background:#faf9f6;color:#171021;margin:0}main{max-width:960px;margin:60px auto;padding:24px}form{display:grid;gap:12px;max-width:400px}input,button{font:inherit;padding:12px;border:1px solid #ccc;border-radius:8px}button{background:#b92c56;color:white;cursor:pointer}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px;border-bottom:1px solid #ddd}td form{display:block}.error{color:#a02342}.scroll{overflow-x:auto}</style>
<main><a href="/">Surren Technologies</a><h1>Consultation requests</h1>
<?php if ($errorMessage): ?><p class="error" role="alert"><?= escape($errorMessage) ?></p><?php endif; ?>
<?php if (!$authenticated): ?>
<form method="post"><input type="hidden" name="csrf_token" value="<?= escape($_SESSION['csrf']) ?>"><input type="hidden" name="action" value="login">
<label for="email">Email</label><input id="email" type="email" name="email" autocomplete="username" required>
<label for="password">Password</label><input id="password" type="password" name="password" autocomplete="current-password" required>
<button>Sign in</button></form>
<?php else: ?>
<form method="post"><input type="hidden" name="csrf_token" value="<?= escape($_SESSION['csrf']) ?>"><button name="action" value="logout">Sign out</button></form>
<div class="scroll"><table><thead><tr><th>Email</th><th>Received (UTC)</th><th>Status</th></tr></thead><tbody>
<?php foreach ($requests as $request): ?><tr><td><?= escape($request['email']) ?></td><td><?= escape($request['created_at']) ?></td><td>
<?php if ($request['handled']): ?>Handled<?php else: ?><form method="post"><input type="hidden" name="csrf_token" value="<?= escape($_SESSION['csrf']) ?>"><input type="hidden" name="id" value="<?= (int) $request['id'] ?>"><button name="action" value="handled">Mark handled</button></form><?php endif; ?>
</td></tr><?php endforeach; ?>
<?php if (!$requests): ?><tr><td colspan="3">No consultation requests yet.</td></tr><?php endif; ?>
</tbody></table></div>
<?php endif; ?></main></html>
