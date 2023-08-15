<?php

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

function getUser()
{
    if (isset($_COOKIE['jwt'])) {
        $decoded = JWT::decode($_COOKIE['jwt'], new Key($_ENV["SECRET"], 'HS256'));
        return \R::load('users', $decoded->user_id);
    }
    return null;
}

function setUser($user)
{
    $payload['user_id'] = $user->id;
    $jwt = JWT::encode($payload, $_ENV["SECRET"], 'HS256');
    setcookie("jwt", $jwt, strtotime('+1 days'), '/');
}

function destroyUser()
{
    unset($_COOKIE['jwt']);
    setcookie('jwt', '', -1, '/');
}