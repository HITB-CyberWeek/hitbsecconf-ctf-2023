<?php

use App\Controllers\IndexController;
use App\Controllers\RegistrationController;
use App\Controllers\AuthController;
use App\Controllers\LanguageController;
use App\Controllers\NoteController;
use App\Controllers\BaseController;

$router = new \Bramus\Router\Router();

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

$router->mount('/notes', function () use ($router) {
    $router->get('/', function () {
        $noteController = new NoteController('notes/index.twig', 'auth');
        $noteController->get();
    });
    $router->match('GET|POST', '/add/', function () {
        $noteController = new NoteController('notes/add.twig', 'auth');
        $noteController->view();
    });
});

$router->mount('/language', function () use ($router) {
    $router->match('GET', '/set', function () {
        $languageController = new BaseController('index.twig');
        $languageController->setLanguage();
    });
    $router->match('GET|POST', '/add', function () {
        $noteController = new LanguageController('language/add.twig', 'auth');
        $noteController->view();
    });
});

$router->all('exit', function () {
    destroyUser();
    header('Location: /');
});

$router->run();
