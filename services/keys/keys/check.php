<?php

require_once "common.php";

$openssl_config = array(
    "digest_alg" => "sha512",
    "private_key_bits" => 2048,
    "private_key_type" => OPENSSL_KEYTYPE_RSA,
);

function try_check_key() {
    $login = trim($_POST['login'] ?? '');
    $private_key = $_POST['private_key'] ?? '';

    if (!$login || !$private_key) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">No login or private_key!</div>';
    }

    if (str_contains($private_key, "\r")) {
        $private_key = str_replace("\r\n", "\n", $private_key);
    }
    $private_key = trim(trim($private_key, "\n"));

    $redis = new Redis();
    $redis->connect('redis');

    $data_str = $redis->get($login);
    if (!$data_str) {
        http_response_code(404);
        return '<div class="alert alert-danger" role="alert">No such login!</div>';
    }

    $data = json_decode($data_str, TRUE);
    $private_key_hash = $data['private_key_hash'];

    if (!password_verify($private_key, $private_key_hash)) {
        http_response_code(400);
        return '<div class="alert alert-danger" role="alert">Bad key!</div>';
    }

    return "<p>OK, you have generated the key with the comment: " . htmlspecialchars($data['comment']) . '</p>'
           . '<p><a href="/">Home</a>';
}


if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $ret = try_check_key();
    head("Check your key");
    echo $ret;
} else {
    head("Check your key");
    $login = $_GET['login'];
?>
    <p>Let`s check you saved your private key:</p>
    <form method="POST">
    <div class="form-group">
    Private key:<br/><textarea cols="70" rows="22" name="private_key"></textarea><br/>
    <input type="hidden" name="login" value="<?php echo urlencode($login) ?>"><br/>
    <input class="btn btn-outline-success" type="submit" value="Check">
    </div>
    </form>

<?php
}
foot();

