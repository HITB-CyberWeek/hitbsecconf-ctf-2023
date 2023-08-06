<?php

$openssl_config = array(
    "digest_alg" => "sha512",
    "private_key_bits" => 2048,
    "private_key_type" => OPENSSL_KEYTYPE_RSA,
);

function head() {
echo <<< END
<html>
<head>
    <title>Generate new key!</title>
</head>
<body>
END;
}

function try_check_key() {
    $login = trim($_POST['login'] ?? '');
    $private_key = $_POST['private_key'] ?? '';

    if (!$login || !$private_key) {
        http_response_code(400);
        echo "No login or private_key!<br/>";
        return;
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
        return "No such login!<br/>";
    }

    $data = json_decode($data_str, TRUE);
    $private_key_hash = $data['private_key_hash'];

    if (!password_verify($private_key, $private_key_hash)) {
        http_response_code(400);
        return "Bad key!<br/>";
    }

    return "OK, you generated the key with comment: " . $data['comment'] . '<br/>';
}


if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $ret = try_check_key();
    head();
    echo $ret;
} else {
    head();
    $login = $_GET['login'];
?>
    Lets check you save your public key:<br/>
    <form method="POST">
    Private key:<br/><textarea name="private_key"></textarea><br/>
    <input type="hidden" name="login" value="<?php echo $login ?>">
    <input type="submit">
    </form>

<?php
}
?>

</body>
</html>
