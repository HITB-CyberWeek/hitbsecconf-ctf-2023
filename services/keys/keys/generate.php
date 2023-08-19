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

function try_generate_key() {
    global $openssl_config;

    $login = $_POST['login'] ?? '';
    $comment = $_POST['comment'] ?? '';

    if (!$login || !$comment) {
        http_response_code(400);
        echo "No login or comment!<br/>";
        return;
    }

    $redis = new Redis();
    $redis->connect('redis');

    if ($redis->exists($login)) {
        http_response_code(400);
        return "Such key already exists!<br/>";
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
        return "Such key already exists!<br/>";
    }

    return <<< END
Generated!<br/>
Save your public key in a safe space!<br/>
Private key:<br/>
<pre>
$private_key_pem
</pre>
<br/>

Public key:<br/>
<pre>
$public_key_pem
</pre>
<br/>
<br/>
<a href='check.php?login=$login'>Next</a>
END;
}


if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $ret = try_generate_key();
    head();
    echo $ret;
} else {
    head();
?>
    <form method="POST">
    Login: <input type="text" name="login"><br>
    Comment: <input type="text" name="comment"><br>
    <input type="submit">
    </form>

<?php
}
?>

</body>
</html>
