<?php

namespace App\Controllers;

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

            $this->context['user']->ownNotesList[] = $note;
            \R::store($this->context['user']);
            header('Location: /notes');
        }
        $this->get();
    }

    public function get()
    {
        foreach ($this->context['user']->ownNotesList as $note) {
            $this->context['notes'][] = $note;
        }

        parent::get();
    }
}