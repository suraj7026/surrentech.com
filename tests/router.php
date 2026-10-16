<?php
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($path === '/' || $path === '/index.html') { readfile(dirname(__DIR__) . '/public/index.html'); return true; }
if (preg_match('~^/assets/[a-zA-Z0-9_-]+\.png$~', $path)) {
    return false;
}
require dirname(__DIR__) . '/public/index.php';
