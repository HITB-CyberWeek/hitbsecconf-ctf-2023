<?php

require_once "common.php";

function try_get_key() {
    $login = trim($_GET['login'] ?? '');

    if (!$login) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">No login!</div>';
    }

    if (!preg_match('/^[-_\w]+$/', $login)) {
        return '<div class="alert alert-danger" role="alert">Bad login!<div>';
    }

    $redis = new Redis();
    $redis->connect('redis');

    $data_str = $redis->get($login);
    if (!$data_str) {
        http_response_code(404);
        return '<div class="alert alert-danger" role="alert">No such login!</div>';
    }

    $data = json_decode($data_str, TRUE);
    $public_key = $data['public_key_pem'];

    return "Public key:<br/>\n<pre>\n$public_key\n</pre>\n";
}

$ret = try_get_key();
head("Keys");
echo $ret;
foot();
