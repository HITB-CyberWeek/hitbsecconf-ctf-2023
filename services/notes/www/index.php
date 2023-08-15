<?php
require_once __DIR__ . "/../vendor/autoload.php";

use App\Services\App;


App::start();
chdir('language');
require_once __DIR__ . "/routes.php";
