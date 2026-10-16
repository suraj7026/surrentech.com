<?php
declare(strict_types=1);
$sent = false;
$formError = '';
$_SESSION = ['csrf' => ''];
ob_start();
require dirname(__DIR__) . '/public/home.php';
file_put_contents(dirname(__DIR__) . '/public/index.html', ob_get_clean());
echo "Rendered the public home page.\n";
