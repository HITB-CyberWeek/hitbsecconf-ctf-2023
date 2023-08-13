$("#issue-token-btn").on("click", function (event) {
    $.ajax({
        url: '/issue_token',
        type: 'POST',
        data: '',
        contentType: 'application/json',
        success: function (response) {
            console.log(response);
            location.href = "/tokens_page";
        },
        error: function (error) {
            console.log(error);
            alert(error.responseText);
        }
    });
});
