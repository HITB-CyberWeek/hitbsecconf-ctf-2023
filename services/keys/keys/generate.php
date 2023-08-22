<?php

require_once "common.php";

$openssl_config = array(
    "digest_alg" => "sha512",
    "private_key_bits" => 2048,
    "private_key_type" => OPENSSL_KEYTYPE_RSA,
);

function try_generate_key() {
    global $openssl_config;

    $login = $_POST['login'] ?? '';
    $comment = $_POST['comment'] ?? '';

    if (!$login || !$comment) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">No login or comment!<div>';
    }

    if (!preg_match('/^[-_\w]+$/', $login)) {
        return '<div class="alert alert-danger" role="alert">Bad login!<div>';
    }

    $redis = new Redis();
    $redis->connect('redis');

    if ($redis->exists($login)) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">Such key already exists!</div>';
    }

    $private_key = openssl_pkey_new($openssl_config);
    openssl_pkey_export($private_key, $private_key_pem);
    $public_key_pem = openssl_pkey_get_details($private_key)['key'];
    $private_key_pem = trim($private_key_pem, "\n");

    $hash = password_hash($private_key_pem, PASSWORD_DEFAULT, ["cost" => 6]);

    $ret = [
        'comment' => $comment,
        'public_key_pem' => $public_key_pem,
        'private_key_hash' => $hash,
    ];

    if (!$redis->setNx($login, json_encode($ret))) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">Such key already exists!</div>';
    }

    $login_encoded = urlencode($login);

    return <<< END
Generated!<br/>
Save your private key in a safe place!<br/>
Private key:<br/>
<pre>
$private_key_pem
</pre>
<br/>

Public key:<br/>
<pre>
$public_key_pem
</pre>
<a class="btn btn-outline-success" href='check.php?login=$login_encoded'>Next</a>
END;
}

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $ret = try_generate_key();
    head("Generate new key");
    echo $ret;
} else {
    head("Generate new key");
?>
    <h1>Generate key</h1>
    <form method="POST">
    <div class="form-group">
        <label for="login">Login</label>
        <input type="text" class="form-control" id="login" name="login"><br>
        <label for="comment">Comment</label>
        <input type="text" class="form-control" id="comment" name="comment"><br>
    </div>
    <input class="btn btn-outline-success" type="submit" value="Generate">
    </form>

<?php
}
foot();
