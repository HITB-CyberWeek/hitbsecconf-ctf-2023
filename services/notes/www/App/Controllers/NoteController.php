<?php

namespace App\Controllers;

class NoteController extends BaseController
{
    public function post()
    {
        $validation = $this->validator->make($_POST, [
            'title' => 'required|min:5|max:50',
            'description' => 'required|min:10'
        ]);
        $validation->validate();

        if ($validation->fails()) {
            $this->context['errors'] = $validation->errors()->firstOfAll();
        } else {
            $note = \R::dispense('notes');
            $note->title = $_POST["title"];
            $note->description = $_POST["description"];
            $user = getUser();
            $user->ownNotesList[] = $note;
            \R::store($user);
        }
        $this->get();
    }

    public function get()
    {
        #TODO
        $user = getUser();
        foreach ($user->ownNotesList as $note) {
            $this->context['notes'][] = $note;
        }

        parent::get();
    }
}