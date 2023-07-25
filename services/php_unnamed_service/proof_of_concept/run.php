#!/usr/bin/env php
<?php

$PRIVATE_KEY = <<< EOF
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQClMDDoEH8JJ+kS
uOQ37XRNnFr63KP4EHcFPdT1INO+kW+7FTyQ5z08KMxXUWMZNwIL3h9CTJJObOyO
OUvgJEsI3ZFD4jiOBu3gNv0MsPL+6peKReOBXeC2rLFPlzyT98Xf10rrjECLXHrZ
+unkkV7Vvy9ST7+23qpq0TF3FMZyy2C30znEWkjfQyCcJKSynv+ZNlqdq0b0FUnq
6q287m0v/dvhXV+1cyC4wZLOmWBFH5PPQMWu7CFGB4NMhc/gq1Vrr5Cc3O1SPSzj
fJqgN3T1V11Zf5e1LG7f0m03ynNJ1cl866z/aoJ97fsH63IPj5WQjv05m7PSTLnS
E/aAlRXDAgMBAAECggEAFEZx+knsDcekR/QBrwuqNsx2Lkxeo9gBg9cvCFdbJgzb
1e6pXG/FiFjJm/4VV8b0rVg6Jf0YCCA+eMZ3la9etlvbtKVTo7sd/2NAdApUCQ3q
Q8KIRhyrtEBGEyrQ+Kh01SCrxXWVhoV3XsH5a2Ccb0fkGwpG0b9K04mRtLgME5LI
dPy74qVYHIB2WgQltF9hiFZMo3i69QB+uMAeeRURDy37wbNba3SyalzuR3DXA5oD
0guxmlIelCkvrmK7YAU17dk0I9/FrwY7k6keoRTtXxvD7hOn6BS1kLFHyUhhrzm/
YmbNezt6AsSIEopQbXHWMjmoh3VMtfEplFD1RbmDAQKBgQDOMEHb5bivyEXz18Le
TpcrvLksRlYCtHe4PJ2FXcgsx+tHDaHYjHV//jyzHeQFHZ/eu7gVH4Y4KRybgmrA
lcfOfYrq/ThQMte2ciXEmz7h2u10huFnr1IbF0EAhuITS4a1q3Hy1azWyo02aE4k
aKrOOipIhuB2DVVYb3s/wmP5IQKBgQDNGEUWF59Yngktc7i6yjfCTYle6c/HcIQe
LiW4LqmvJkn9mtuSZnkMlNvtLBcLUr+AwQ8hKAoZSXri9zho84rdRP0/fqzWs1JI
77nNa5a68mfGpdJRQaoHO01NzYt6nI+JDoKDvcKYiMdonYBwaZcjHmLWA+P4zAkX
H00sqh3+YwKBgAUrSotjv/SQNci+MQF3wOx0x8OnY8KfmZzB0EUmq70LqgdW/Sa7
prp1ujnXVv8V1gs0c5H7/1ZrGW+AnoKDfsXbed8YSBAipivJws6iAbqRzYAtXXtG
9uz88UE9IG/RZegqCypGVxXvcAjcJpFdGmMfLC4zS29KOEiGSvW3PuBhAoGBAMnV
e4+tOZxtEh0PyBjSjqMByRGFyXu9B9fnlCk4iraaWLBh6HmfrLqr9+7kt9zl1x4v
X+NCUwXloTChGHt4SQ1OKmeFEzTLDkxG1rQIkDJ0AZqlb1+V3mz1eDL796p3Tm4T
wG9DnLCd0pfqgA6gayMdcSiqdXxP1xZRMJKm65N/AoGAdptyxlPsq/ZE+aNa5yMi
xLy9NY5rZbrRmPALldc55plz4IBC4Ap3v/NDgFdKjmc4nqDCfbe865xdfaAv3vCR
Kz880JN/V/wSA5eRm1c26FRateOfhb7Zg4K/1kfkNIAoW1gaNA0ay5Jttn7bqNj0
7ufnKRYuUSnftrqRkGf2MTo=
-----END PRIVATE KEY-----
EOF;

$PUBLIC_KEY = <<< EOF
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApTAw6BB/CSfpErjkN+10
TZxa+tyj+BB3BT3U9SDTvpFvuxU8kOc9PCjMV1FjGTcCC94fQkySTmzsjjlL4CRL
CN2RQ+I4jgbt4Db9DLDy/uqXikXjgV3gtqyxT5c8k/fF39dK64xAi1x62frp5JFe
1b8vUk+/tt6qatExdxTGcstgt9M5xFpI30MgnCSksp7/mTZanatG9BVJ6uqtvO5t
L/3b4V1ftXMguMGSzplgRR+Tz0DFruwhRgeDTIXP4KtVa6+QnNztUj0s43yaoDd0
9VddWX+XtSxu39JtN8pzSdXJfOus/2qCfe37B+tyD4+VkI79OZuz0ky50hP2gJUV
wwIDAQAB
-----END PUBLIC KEY-----
EOF;

$PRIVATE_PREFIX_HEX = "308204bd020100300d06092a864886f70d0101010500048204a7308204a302010002820101";

function fake_private_key($public_key) {
    global $PRIVATE_PREFIX_HEX;

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
    $fake_private_key = $PRIVATE_PREFIX_HEX . $modulus;
    // print ">>>>>>>>>\n";
    // print $fake_private_key . "\n";
    $fake_private_key = pack('H*', $fake_private_key);
    $fake_private_key = base64_encode($fake_private_key);
    $fake_private_key = "-----BEGIN PRIVATE KEY-----\n" . $fake_private_key . "\n-----END PRIVATE KEY-----\n";
    return $fake_private_key;

}

// function unpack_key($key) {
//     $key = str_replace('-----BEGIN PUBLIC KEY-----', '', $key);
//     $key = str_replace('-----END PUBLIC KEY-----', '', $key);
//     $key = str_replace('-----BEGIN PRIVATE KEY-----', '', $key);
//     $key = str_replace('-----END PRIVATE KEY-----', '', $key);

//     $key_decoded = base64_decode($key);
//     $key_unpacked = unpack('H*', $key_decoded)[1];
//     print "====\n$key_unpacked\n";
// }

function main() {
    global $PUBLIC_KEY;
    global $PRIVATE_KEY;

    // unpack_key($PRIVATE_KEY);

    $fake_private_key = fake_private_key($PUBLIC_KEY);
    $hash = password_hash($PRIVATE_KEY, PASSWORD_DEFAULT);
    print password_verify($fake_private_key, $hash) ? "Private key 2 is the same as private key 1!" : "False";
    print "\n";
}

main();