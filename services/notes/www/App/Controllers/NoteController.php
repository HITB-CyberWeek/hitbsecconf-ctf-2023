<?php

use App\Controllers\BaseController;

class NoteController extends BaseController
{
    public function post()
    {
        $validation = $this->validator->make($_POST, [
            'title' => 'required|min:5',
            'description' => 'required|min:10'
        ]);
        $validation->validate();

        if ($validation->fails()) {
            $this->context['errors'] = $validation->errors()->firstOfAll();
        } else {
            $note = \R::dispense('notes');
            $note->title = $_POST["title"];
            $note->description = $_POST["description"];
            \R::store($note);
        }
        $this->get();
    }
}