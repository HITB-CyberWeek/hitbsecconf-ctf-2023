<?php

namespace App\Controllers;

use Rakit\Validation\Validator;
use App\Services\UniqueRule;
use App\Services\ExistRule;

class BaseController
{
    public function __construct($template, $authRule = "all")
    {
        $this->authRule = $authRule;
        $loader = new \Twig\Loader\FilesystemLoader('/var/www/html/templates');
        $this->twig = new \Twig\Environment($loader, []);
        $this->template = $template;

        $this->context = array(
            'session' => $_SESSION,
            'post' => $_POST,
            'get' => $_GET,
            'request_uri' => $_SERVER['REQUEST_URI'],
            'errors' => []
        );

        $this->validator = new Validator;
        $this->validator->addValidator('unique', new UniqueRule());
        $this->validator->addValidator('exist', new ExistRule());

        $this::checkAuthRule();
        $this::getLanguage();
    }

    private function getLanguage()
    {
        $language = $_COOKIE['language'] ?? 'en';
//        var_dump("$language.ini");
        $this->context['language'] = parse_ini_file("language/$language.ini");
    }

    public function setLanguage()
    {
        header('Location: /');
        $language = $_GET['language'] ?? 'en';
        setcookie("language", $language, strtotime( '+1 days' ), '/');

    }

    private function checkAuthRule()
    {
        if ($this->authRule === "not_auth" && isset($_SESSION['user_id'])) {
            header('Location: /');
            exit();
        } elseif ($this->authRule === "auth" && !isset($_SESSION['user_id'])) {
            header('Location: /signin');
            exit();
        }

        if (isset($_SESSION['user_id'])) {
            $user = \R::load('users', $_SESSION['user_id']);
            $this->context['user'] = [
                "id" => $user->id,
                "email" => $user->email,
                "username" => $user->username,
            ];

        }
    }


    public function view()
    {
        if ($_SERVER["REQUEST_METHOD"] === "POST") {
            $this->post();
        } else {
            $this->get();
        }
    }

    public function get()
    {
//        var_dump($this->context);
        echo $this->twig->render($this->template, $this->context);
    }

    public function post()
    {
        $this->get();
    }
}