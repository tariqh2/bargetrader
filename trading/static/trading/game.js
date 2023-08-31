$(document).ready(function(){
    // Setup AJAX with CSRF token
    $.ajaxSetup({
        headers: { "X-CSRFToken": getCookie('csrftoken') }
    });
$("#bid-offer-form").on("submit", function(e){
    e.preventDefault();
    $.ajax({
        url: updateBidOfferUrl,
        data: $(this).serialize(),
        type: "POST",
        success: function(response){
            // do something with the response
            if(response.status === 'success') {
        alert("Bid and offer submitted successfully."); // Display a pop-up message
        // Select user's row
        let userRow = $('#user-row-' + response.player_name);
        // Check if the row exists
        if (userRow.length) {
            // The row exists, update bid and offer values
            userRow.find('.bid').text('$' + response.bid);
            userRow.find('.offer').text('$' + response.offer);
        } else {
            // The row doesn't exist, create a new row and append it to the table
            let newRow = `<tr id="user-row-${response.player_name}">
                                <td>${response.player_name}</td>
                                <td><button class="hit-bid">Hit Bid</button></td>
                                <td class="bid">$${response.bid}</td>
                                <td><button class="lift-offer">Lift Offer</button></td>
                                <td class="offer">$${response.offer}</td>
                            </tr>`;
            $('.auction-status table').append(newRow);
        }     
    } else {
        // Process and display form error messages from the server
        let errorMsg = "An error occurred while submitting your bid and offer.";
        if (response.errors && response.errors.length) {
            errorMsg += "\n\n" + response.errors.join("\n");
        }
        alert(errorMsg);
        
    }
        },
        error: function(jqXHR) {
            // This handles HTTP error responses like 400, 500, etc.
            if (jqXHR.responseJSON && jqXHR.responseJSON.errors) {
                let errorMsg = "An error occurred while submitting your bid and offer.";
                errorMsg += "\n\n" + jqXHR.responseJSON.errors.join("\n");
                alert(errorMsg);
} else {
    alert('An unexpected error occurred.');
}
}
    });
});
// Handle hit bid and lift offer button clicks
$(document).on("click", ".hit-bid, .lift-offer", function(e){
    var aiPlayerId = $(this).data("player-id");
    var parentTr = $(this).parents("tr"); // get the parent tr element
    console.log(parentTr.find(".bid")); // Debug
    console.log(parentTr.find(".offer")); // Debug
    var price = $(this).hasClass("hit-bid") ? parentTr.find(".bid").data("bid") : parentTr.find(".offer").data("offer");
    console.log(price); // Log the price to console for debugging
    $.ajax({
        url: createTradeUrl,
        data: {
            ai_player_id: aiPlayerId,
            price: price,
            action: $(this).hasClass("hit-bid") ? 'sell' : 'buy',
        },
        type: "POST",
        success: function(response) {
            if(response.status === 'success') {
                let newRow = `<tr id="trade-row-${response.trade.id}">
                    <td>${response.trade.buyer.name}</td>
                    <td>${response.trade.seller.name}</td>
                    <td>${response.trade.price}</td>
                    <td>${response.trade.quantity}</td>
                </tr>`;
                $('.confirmed-trades table').append(newRow);
            } else {
                alert("An error occurred while creating the trade."); 
            }
        }
    });
});

// Initialize timer variables
let minutes = 2; // because we're starting at 03:00, which is 2 minutes and 60 seconds
let seconds = 60;

// Update the display
const updateDisplay = () => {
    $('#countdown-timer').text((minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds);
};

const countdown = setInterval(function() {
    seconds--; // Decrement seconds

    if (seconds < 0) { // If seconds go below zero...
        seconds = 59; // Reset seconds
        minutes--;    // and decrement a minute.
    }

    updateDisplay(); // Update the timer display

    if (minutes < 0) { // If minutes go below zero...
    clearInterval(countdown); // Clear the interval
    alert("The game round has ended!"); // Display the end of round message

    // Inside the function where the timer ends
    $.ajax({
        url: playerSummaryUrl,
        type: "GET",
        success: function(response) {
            let summaryHtml = `
                <ul>
                    <li>Position: ${response.position}</li>
                    <li>Cash Flow: ${response.cash_flow}</li>
                    <li>Buy Trades Count: ${response.buy_trades_count}</li>
                    <li>Sell Trades Count: ${response.sell_trades_count}</li>
                    <!-- Add other relevant data here -->
                </ul>
            `;

            // Assuming you are using a simple modal/pop-up system:
            $("#summaryModal .modal-body").html(summaryHtml);
            $("#summaryModal").modal('show'); // Show the modal
        },
        error: function(error) {
            console.error("Error fetching player summary:", error);
        }
    });

}

}, 1000); // This will run every second

// Start the timer immediately
updateDisplay();





});