<?php
namespace App\Controllers;
//use Ausi\SlugGenerator\SlugGenerator;


class LanguageController extends BaseController
{

    public function __construct($template, $authRule = "all")
    {
        parent::__construct($template, $authRule);
            $en_ini = parse_ini_file('en.ini');
            $this->context['keys'] = array_keys($en_ini);
    }

    public function post()
    {
        $validator = [
            'title' => 'required|min:5|max:50'
        ];

        foreach ($this->context['keys'] as $key) {
            $validator[$key] = 'required|min:5|max:50';
        }

        $validation = $this->validator->make($_POST, $validator);
        $validation->validate();

        if ($validation->fails()) {
            $this->context['errors'] = $validation->errors()->firstOfAll();
        } else {
            $generator = new SlugGenerator;
            $user = getUser();
            $language = \R::dispense('languages');
            $language->title = $_POST['title'];
//            $language->slug = $generator->generate($_POST['title']);
            $user->ownLanguagesList[] = $language;
            \R::store($user);
            $data = "";
            foreach ($this->context['keys'] as $key) {
                $data .= $key . " = " . $_POST[$key] . "\n";
            }
            $data = str_replace(["{", "}"], "_",$data);
            file_put_contents("lang_" . $language->getID() . ".ini", $data);
        }
        $this->get();
    }


}