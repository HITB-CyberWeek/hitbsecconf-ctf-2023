<?php

use App\Controllers\IndexController;
use App\Controllers\RegistrationController;
use App\Controllers\AuthController;
use App\Controllers\LanguageController;
use App\Controllers\BaseController;

$router = new \Bramus\Router\Router();

if (isset($_SESSION['user_id'])) {
    $user = \R::findOne('users', $_SESSION['user_id']);
    if (is_null($user)) {
        session_destroy();
        header('Location: /');
    }
}

$router->all('', function () {
    $indexController = new IndexController('index.twig');
    $indexController->view();
});

$router->match(
    'GET|POST', 'signup',
    function () {
        $registrationController = new RegistrationController('signup.twig', 'not_auth');
        $registrationController->view();
    }
);
$router->match(
    'GET|POST', 'signin',
    function () {
        $authController = new AuthController('signin.twig', 'not_auth');
        $authController->view();
    }
);
$router->match(
    'GET', 'language',
    function () {
        $languageController = new BaseController('index.twig');
        $languageController->setLanguage();
    }
);
$router->all(
    'exit',
    function () {
        session_destroy();
        header('Location: /');
    }
);

$router->run();
