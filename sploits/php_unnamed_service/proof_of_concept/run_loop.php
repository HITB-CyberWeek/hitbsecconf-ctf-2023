#!/usr/bin/env php
<?php

$PRIVATE_PREFIX_HEX = "308204be020100300d06092a864886f70d0101010500048204a8308204a402010002820101";
$HEX_CHARS = ['e','0','4','1','2','3','5','6','7','8','9','a','b','c','d','f'];
$ITERATIONS = 1000;


function fake_private_keys($public_key, $private_key, &$stat) {
    global $PRIVATE_PREFIX_HEX;
    global $HEX_CHARS;

    $hash = password_hash($private_key, PASSWORD_DEFAULT);

    $public_key = str_replace('-----BEGIN PUBLIC KEY-----', '', $public_key);
    $public_key = str_replace('-----END PUBLIC KEY-----', '', $public_key);
    $public_key = str_replace('-----BEGIN PRIVATE KEY-----', '', $public_key);
    $public_key = str_replace('-----END PRIVATE KEY-----', '', $public_key);


    $public_key_decoded = base64_decode($public_key);
    $public_key_decoded_unpacked  = unpack('H*', $public_key_decoded)[1];
    // print_r($public_key_decoded_unpacked);
    $modulus = substr($public_key_decoded_unpacked, 64);
    // print($modulus);
    // print(substr($public_key_decoded_unpacked, 0, 37*2));


    $private_prefix_hex = $PRIVATE_PREFIX_HEX;
    $fake_private_key = $private_prefix_hex . $modulus;
    $hex_chars = $HEX_CHARS;
    //shuffle($hex_chars); // I'm lucky!
    foreach($hex_chars as $a) {
        $fake_private_key[7] = $a;
        // echo "|";
        foreach($hex_chars as $b) {
            $fake_private_key[51] = $b;
            foreach($hex_chars as $c) {
                $fake_private_key[52] = $c;
                // echo "/";
                foreach($hex_chars as $d) {
                    $fake_private_key[53] = $d;
                    foreach($hex_chars as $e) {
                        $fake_private_key[59] = $e;

                        // print ">>>>>>>>>\n";
                        // print $fake_private_key . "\n";
                        $fake_private_key_pem = "-----BEGIN PRIVATE KEY-----\n" . base64_encode(pack('H*', $fake_private_key)) . "\n-----END PRIVATE KEY-----\n";

                        // array_push($res, $fake_private_key);

                        if (substr($private_key, 0, 72) == substr($fake_private_key_pem, 0, 72)) {
                            $key = implode('_', [$a, $b, $c, $d, $e]);
                            $stat[$key] = ($stat[$key] ?? 0) + 1;
                            return;
                        }

                        // if (password_verify($fake_private_key_pem, $hash)) {
                        //     echo "$a $b $c\n";
                        //     $key = implode('_', [$a, $b, $c, $d, $e]);
                        //     $stat[$key] = ($stat[$key] ?? 0) + 1;
                        //     return;
                        // }
                    }
                }
            }
        }
    }

    $stat['not_found'] = ($stat['not_found'] ?? 0) + 1;

    unpack_key($private_key);
    unpack_key($fake_private_key_pem);

    // $fake_private_key = $PRIVATE_PREFIX_HEX . $modulus;
    // print ">>>>>>>>>\n";
    // print $fake_private_key . "\n";
    // $fake_private_key = pack('H*', $fake_private_key);
    // $fake_private_key = base64_encode($fake_private_key);
    // $fake_private_key = "-----BEGIN PRIVATE KEY-----\n" . $fake_private_key . "\n-----END PRIVATE KEY-----\n";

}

function unpack_key($key) {
    $key = str_replace('-----BEGIN PUBLIC KEY-----', '', $key);
    $key = str_replace('-----END PUBLIC KEY-----', '', $key);
    $key = str_replace('-----BEGIN PRIVATE KEY-----', '', $key);
    $key = str_replace('-----END PRIVATE KEY-----', '', $key);

    $key_decoded = base64_decode($key);
    $key_unpacked = unpack('H*', $key_decoded)[1];
    print "====\n$key_unpacked\n";
}

function main() {
    global $ITERATIONS;

    $config = array(
        "digest_alg" => "sha512",
        "private_key_bits" => 2048,
        "private_key_type" => OPENSSL_KEYTYPE_RSA,
    );

    // print_r($private_key_pem);
    // print_r($public_key_pem);

    // unpack_key($private_key_pem);

    $stat = [];
    for ($i = 0; $i < $ITERATIONS; $i++) {
        $private_key = openssl_pkey_new($config);
        openssl_pkey_export($private_key, $private_key_pem);
        $public_key_pem = openssl_pkey_get_details($private_key)['key'];

        echo "ITERATION: $i\n";
        flush();

        fake_private_keys($public_key_pem, $private_key_pem, $stat);
    }

    print_r($stat);

    // $found = FALSE;
    // $count = 0;
    // $total = count($fake_private_keys);
    // foreach($fake_private_keys as $fake_private_key) {
    //     print $count . ' / ' . $total . "\n";
    //     $hash = password_hash($private_key_pem, PASSWORD_DEFAULT);
    //     if (password_verify($fake_private_key, $hash)) {
    //         $found = TRUE;
    //         break;
    //     }
    //     $count++;
    // }

    // if (!$found) {
    //     print($private_key_pem);
    //     print("\n");
    //     print($public_key_pem);
    //     print("\n");
    // }
}

main();