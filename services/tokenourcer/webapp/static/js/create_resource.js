function create_resource(event) {
    console.log("event: " + event.toString());
    event.preventDefault();

    const reader = new FileReader();
    reader.onload = function (e) {
        let b64blob = e.target.result.replace(/^data:(.*,)?/, '');
        console.log(b64blob);
        let result = {
            "token": $("#token-select").val(),
            "name": $("#r-name").val(),
            "b64blob": b64blob,
        }
        console.log(JSON.stringify(result));

        $.ajax({
            url: '/create_resource',
            type: 'POST',
            data: JSON.stringify(result),
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
    reader.readAsDataURL($("#file")[0].files[0]);
}

$("#create-btn").on("click", create_resource);
