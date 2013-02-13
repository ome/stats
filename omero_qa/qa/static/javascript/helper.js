function saveEmail (value) {
    $($('#id_email').parent()).append('<img src="/qa/static/images/spinner.gif"/>');
    $.ajax({
        type: "POST",
        url: "../save_email/",
        data: "email="+value,
        contentType:'html',
        cache:false,
        success: function(responce){
            if(responce.match(/(Error: )/gi)) {
                $('#email_error ul.errorlist').remove()
                $('#email_error').append(responce.replace('Error: ',''))
            } else {
                $('#email_error ul.errorlist').remove()
            }
            $($('#email_form').parent().find('img')).remove()
        },
        error: function(responce) {
            $($('#id_email').parent().find('img')).remove()
            alert("Email '"+value+"' could not be save.")
        }
    });
}
