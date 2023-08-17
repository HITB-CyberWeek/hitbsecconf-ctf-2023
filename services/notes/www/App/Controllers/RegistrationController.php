<?php

namespace App\Controllers;

class RegistrationController extends BaseController
{


    public function post()
    {
        $validation = $this->validator->make($_POST, [
            'email' => 'required|email|unique:users,email',
            'password' => 'required|min:6',
            'confirm_password' => 'required|same:password',
        ]);
        $validation->validate();

        if ($validation->fails()) {
            $this->context['errors'] = $validation->errors()->firstOfAll();
        } else {
            $user = \R::dispense('users');
            $user->password = password_hash($_POST["password"], PASSWORD_DEFAULT);
            $user->email = $_POST["email"];
            \R::store($user);
            setUser($user);
            header('Location: /notes');
        }
        $this->get();
    }
}