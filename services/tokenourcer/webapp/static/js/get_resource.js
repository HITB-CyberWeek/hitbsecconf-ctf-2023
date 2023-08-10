function get_resource(event) {
    console.log("event: " + event.toString());
    event.preventDefault();

    let token = $("#token").val();
    let username = $("#username").val();
    let resource_id = $("#resource-id").val();

    console.log(token, username, resource_id);
}

$("#download-btn").on("click", get_resource);
