
        $(document).ready(function(){
            // Setup AJAX with CSRF token
            $.ajaxSetup({
                headers: { "X-CSRFToken": '{{csrf_token}}' }
            });
        $("#bid-offer-form").on("submit", function(e){
            e.preventDefault();
            $.ajax({
                url: "{% url 'update_bid_offer' %}",
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
                alert("An error occurred while submitting your bid and offer."); // Display a different message in case of an error
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
                url: "{% url 'create_trade' %}",
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
    });
    