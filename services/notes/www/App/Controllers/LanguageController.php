<?php

namespace App\Controllers;

use Ausi\SlugGenerator\SlugGenerator;


class LanguageController extends BaseController
{

    public function __construct($template, $authRule = "all")
    {
        parent::__construct($template, $authRule);
        $en_ini = parse_ini_file('en.ini');
        $this->context['keys'] = array_keys($en_ini);
    }


    private function getSlug($title)
    {
        $generator = new SlugGenerator;
        $slug = $generator->generate($title);
        $count_notes = \R::count('languages', ' slug LIKE ? ', ['%' . $slug . '%']);
        if ($count_notes >= 1) {
            $slug .= "-$count_notes";
        }
        return $slug;
    }


    public function post()
    {
        $validator = [
            'title' => 'required|min:5|max:50'
        ];

        foreach ($this->context['keys'] as $key) {
            $validator[$key] = 'required|min:1';
        }

        $validation = $this->validator->make($_POST, $validator);
        $validation->validate();

        if ($validation->fails()) {
            $this->context['errors'] = $validation->errors()->firstOfAll();
        } else {
            $user = getUser();
            $language = \R::dispense('languages');
            $language->title = $_POST['title'];
            $language->slug = $this->getSlug($_POST["title"]);
            $user->ownLanguagesList[] = $language;
            \R::store($user);
            $data = "";
            foreach ($this->context['keys'] as $key) {
                $data .= $key . " = " . $_POST[$key] . "\n";
            }
            $data = str_replace(["{", "}"], "_", $data);
            if (!is_dir("user:" . $user->id)) {
                mkdir("user:" . $user->id);
            }
            file_put_contents("user:" . $user->id . "/" . $language->slug . ".ini", $data);
            $this->context['shared_link'] = "http://" . $_SERVER['HTTP_HOST'] . "/language/set/?language=user:" . $user->id . "/" . $language->slug . "&location=/";
            echo $this->twig->render("language/success.twig", $this->context);
            exit();
        }
        $this->get();

    }
}
