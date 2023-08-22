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
            'languages' => [],
            'errors' => [],

        );

        $this->validator = new Validator;
        $this->validator->addValidator('unique', new UniqueRule());
        $this->validator->addValidator('exist', new ExistRule());

        $this::checkAuthRule();
        $this::getLanguage();
    }

    private function getLanguage()
    {
        $language = (isset($_COOKIE['language']) && checkLanguage($_COOKIE['language'])) ? $_COOKIE['language'] : 'en';
        $this->context['language_code'] = $language;

        $this->context['language'] = parse_ini_file("$language.ini");
    }

    public function setLanguage()
    {
        $location = $_GET['location'] ?? '/';
        header("Location: $location");
        $language = $_GET['language'] ?? 'en';
        setcookie("language", $language, strtotime('+1 days'), '/');

    }

    private function checkAuthRule()
    {
        $user = getUser();
        if ($this->authRule === "not_auth" && !is_null($user)) {
            header('Location: /');
            exit();
        } elseif ($this->authRule === "auth" && is_null($user)) {
            header('Location: /signin');
            exit();
        }
        if (!is_null($user)) {
            $this->context['user'] = $user;
            $this->context['languages'] = $user->ownLanguagesList;
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
        echo $this->twig->render($this->template, $this->context);
    }

    public function post()
    {
        $this->get();
    }
}