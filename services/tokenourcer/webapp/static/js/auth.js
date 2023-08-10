function sendUserPair(event, method) {
    event.preventDefault(); // Prevent form from submitting normally

    // Get form inputs
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    // Create JSON object
    var user = {
        username: username,
        password: password
    };

    // Send JSON data to server
    $.ajax({
        url: method, // Replace with your server URL
        type: 'POST',
        data: JSON.stringify(user),
        contentType: 'application/json',
        success: function (response) {
            console.log(response);
            location.href = "/";
        },
        error: function (error) {
            console.log(error);
            alert(error.responseText);
        }
    });
}


function register(event) {
    return sendUserPair(event, '/register');
}

function login(event) {
    return sendUserPair(event, '/login');
}
