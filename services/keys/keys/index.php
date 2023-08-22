<?php

require_once "common.php";
head("Keys!");
?>

<h1>Keys!</h1>
<div class="col-lg-8 px-0">
<p class="fs-5">Search key</p>
<p>
    <form class="d-flex" role="search" action="/key.php">
        <input class="form-control me-2" type="search" placeholder="Login" aria-label="Search" name="login">
        <button class="btn btn-outline-success" type="submit">Search</button>
    </form>
    <p><small>Hint: see <a href="https://2023.ctf.hitb.org/hitb-ctf-phuket-2023/api">API for receiving an actual list of flag ids and descriptions</a></small></p>
</p>
<p>
    <a href="/generate.php">Generate a new key</a>
</p>

</div>

<?php
foot();
?>
