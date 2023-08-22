<?php

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

function getUser()
{
    if (isset($_COOKIE['jwt'])) {
        try {
            $decoded = JWT::decode($_COOKIE['jwt'], new Key($_ENV["SECRET"], 'HS256'));
            $user = \R::findOne('users', ' id = ?', [$decoded->user_id]);
            return $user;
        } catch (Exception $e) {

        }
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

function checkLanguage($path)
{
    return !str_contains('data:', $path)
        and !str_contains('..', $path)
        and !str_starts_with('/', $path);
}