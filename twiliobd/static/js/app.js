// Execute JavaScript on page load
$(function() {
    // Submit dial phone form submission with ajax
    $('#contactForm').on('submit', function(e) {
        e.preventDefault();
        $.ajax({
            url: '/call',
            method: 'POST',
            dataType: 'json',
            data: {
                phoneNumber: $('#phoneNumber').val()
            }
        }).done(function(data) {
            // The JSON sent back from the server will contain
            // a success message
            alert(data.message);
        }).fail(function(error) {
            alert(JSON.stringify(error));
        });
    });

    $(".call-button").click(function() {
      console.log("Calling");
      let $tds = $(this).closest("tr").find("td");
      $.each($tds, function() {
        console.log($(this).text());
    });

    $(".text-button").click(function() {
      console.log("Texting");
      let $tds = $(this).closest("tr").find("td");
      $.each($tds, function() {
        console.log($(this).text());
    });

});});
