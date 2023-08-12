<?php

function head() {
echo <<< END
<html>
<head>
    <title>Key</title>
</head>
<body>
END;
}

function try_get_key() {
    $login = trim($_GET['login'] ?? '');

    if (!$login) {
        http_response_code(400);
        echo "No login!<br/>";
        return;
    }

    $redis = new Redis();
    $redis->connect('redis');

    $data_str = $redis->get($login);
    if (!$data_str) {
        http_response_code(404);
        return "No such login!<br/>";
    }

    $data = json_decode($data_str, TRUE);
    $public_key = $data['public_key_pem'];

    return "Public key:<br/>\n<pre>\n$public_key\n</pre>\n";
}

$ret = try_get_key();
head();
echo $ret;
?>

</body>
</html>
