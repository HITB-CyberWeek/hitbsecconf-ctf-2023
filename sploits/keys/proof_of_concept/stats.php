#!/usr/bin/env php
<?php

$ITERATIONS = 10000;
$INDECES_STAT = [7, 51, 52, 53, 59];

function update_private_key_stats($private_key, &$stat) {
    global $INDECES_STAT;

    $private_key_unpacked = unpack_key($private_key);

    $chars_for_stats = [];
    foreach ($INDECES_STAT as $i) {
        array_push($chars_for_stats, $private_key_unpacked[$i]);
    }

    $key = implode('_', $chars_for_stats);
    $stat[$key] = ($stat[$key] ?? 0) + 1;
}

function unpack_key($key) {
    $key = str_replace('-----BEGIN PUBLIC KEY-----', '', $key);
    $key = str_replace('-----END PUBLIC KEY-----', '', $key);
    $key = str_replace('-----BEGIN PRIVATE KEY-----', '', $key);
    $key = str_replace('-----END PRIVATE KEY-----', '', $key);

    $key_decoded = base64_decode($key);
    $key_unpacked = unpack('H*', $key_decoded)[1];
    return $key_unpacked;
}

function main() {
    global $ITERATIONS;

    $config = array(
        "digest_alg" => "sha512",
        "private_key_bits" => 2048,
        "private_key_type" => OPENSSL_KEYTYPE_RSA,
    );

    $stat = [];
    for ($i = 0; $i < $ITERATIONS; $i++) {
        $private_key = openssl_pkey_new($config);
        openssl_pkey_export($private_key, $private_key_pem);
        // $public_key_pem = openssl_pkey_get_details($private_key)['key'];

        if ($i % 100 == 0) {
            echo "ITERATION: $i\n";
        }
        update_private_key_stats($private_key_pem, $stat);
    }

    print_r($stat);
}

main();
