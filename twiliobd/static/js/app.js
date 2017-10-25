// Execute JavaScript on page load
$(function() {
  // Event handler for clicking text or call
  $(".text-button, .call-button").click(function(event) {
    event.preventDefault()
    let btnAction = $(event.target).text();
    let $tds = $(this).closest("tr").find("td");
    let rowValues = [];
    $.each($tds, function() {
      rowValues.push($(this).text());
    });

    if (!confirm("Are you sure?")) return;
    console.log(rowValues);
    $.ajax({
      url: btnAction==='Text' ? '/text' : '/call',
      method: 'POST',
      dataType: 'json',
      data: {
        phoneNumber: rowValues[2],
        name: rowValues[0],
      },
    }).done(function(data) {
      // The JSON sent back from the server will contain a success message
      alert(data.message);
    }).fail(function(error) {
      alert(JSON.stringify(error));
    });
  });

});
