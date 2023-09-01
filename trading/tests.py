from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Player, Trade, AIPlayer, GameSession
from django.urls import reverse
from .forms import BidOfferForm
from django.utils import timezone
import logging
from .views import start_game_session
from decimal import Decimal



# Create a logger object
logger = logging.getLogger('trading')

class UserTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.test_username = 'testuser'
        self.test_password = 'testpassword'
        self.user = User.objects.create(username=self.test_username)
        self.user.set_password(self.test_password)
        self.user.save()
        self.player = Player.objects.create(user=self.user)

    def test_register(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password': 'newpassword',
            'confirmation': 'newpassword',
        })
        self.assertEqual(response.status_code, 302) # Expecting a redirect
        new_user = User.objects.filter(username='newuser').first()
        self.assertIsNotNone(new_user)
        new_player = Player.objects.filter(user=new_user).first()
        self.assertIsNotNone(new_player)

    def test_login(self):
        response = self.client.post(reverse('login_view'), {
            'username': self.test_username,
            'password': self.test_password
        })
        self.assertEqual(response.status_code, 302) # Expecting a redirect

    def test_game_view(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('game'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_username)
        self.assertContains(response, self.player.position)
        self.assertContains(response, self.player.cash_flow)

class PlayerPositionTestCase(TestCase):
    def setUp(self):
        # Create a user and a player (John)
        self.user_john = User.objects.create_user(username='john', password='password')
        self.john = Player.objects.create(user=self.user_john)

        # Create another player (Paul)
        self.user_paul = User.objects.create_user(username='paul', password='password')
        self.paul = Player.objects.create(user=self.user_paul)

    def test_one_trade_position(self):
        # John buys 2000mt at $90 from Paul
        trade1 = Trade.objects.create(buyer=self.john, seller=self.paul, price=90, quantity=2000)

        # Check if the position is calculated correctly for John
        john_position = self.john.calculate_position()
        self.assertEqual(john_position, 2000)  # John's position should be 2000 (he bought 2000mt)

        # Check if the position is calculated correctly for Paul
        paul_position = self.paul.calculate_position()
        self.assertEqual(paul_position, -2000)  # Paul's position should be -2000 (he sold 2000mt)

        # Check if updating positions works
        self.john.update_position()
        self.paul.update_position()

        # Retrieve the updated positions
        updated_john = Player.objects.get(id=self.john.id)
        updated_paul = Player.objects.get(id=self.paul.id)

        # Check if the positions are updated correctly
        self.assertEqual(updated_john.position, 2000)
        self.assertEqual(updated_paul.position, -2000)

    def test_two_trades_position(self):
        # John buys 2000mt at $90 from Paul
        trade1 = Trade.objects.create(buyer=self.john, seller=self.paul, price=90, quantity=2000)

        # John sells 2000mt at $100 back to Paul
        trade2 = Trade.objects.create(buyer=self.paul, seller=self.john, price=100, quantity=2000)

        # Check if the position is calculated correctly for John after both trades
        john_position = self.john.calculate_position()
        self.assertEqual(john_position, 0)  # John's position should be 0 after buying and selling

        # Check if the position is calculated correctly for Paul after both trades
        paul_position = self.paul.calculate_position()
        self.assertEqual(paul_position, 0)  # Paul's position should be 0 after selling and buying

        # Check if updating positions works
        self.john.update_position()
        self.paul.update_position()

        # Retrieve the updated positions
        updated_john = Player.objects.get(id=self.john.id)
        updated_paul = Player.objects.get(id=self.paul.id)

        # Check if the positions are updated correctly
        self.assertEqual(updated_john.position, 0)
        self.assertEqual(updated_paul.position, 0)

    def test_three_trades_position(self):
        # John buys 2000mt at $90 from Paul
        trade1 = Trade.objects.create(buyer=self.john, seller=self.paul, price=90, quantity=2000)

        # John buys another 2000mt at $80 from Paul
        trade2 = Trade.objects.create(buyer=self.john, seller=self.paul, price=80, quantity=2000)

        # Check if the position is calculated correctly for John after both trades
        john_position = self.john.calculate_position()
        self.assertEqual(john_position, 4000)  # John's position should be 4000 (he bought 4000mt)

        # Check if the position is calculated correctly for Paul after both trades
        paul_position = self.paul.calculate_position()
        self.assertEqual(paul_position, -4000)  # Paul's position should be -4000 (he sold 4000mt)

        # Check if updating positions works
        self.john.update_position()
        self.paul.update_position()

        # Retrieve the updated positions
        updated_john = Player.objects.get(id=self.john.id)
        updated_paul = Player.objects.get(id=self.paul.id)

        # Check if the positions are updated correctly
        self.assertEqual(updated_john.position, 4000)
        self.assertEqual(updated_paul.position, -4000)

class PlayerCashFlowTestCase(TestCase):
    def setUp(self):
        # Create a user and a player (John)
        self.user_john = User.objects.create_user(username='john', password='password')
        self.john = Player.objects.create(user=self.user_john)

        # Create another player (Paul)
        self.user_paul = User.objects.create_user(username='paul', password='password')
        self.paul = Player.objects.create(user=self.user_paul)

    def test_one_trade_cash_flow(self):
        # John buys 2000mt at $5 from Paul
        trade1 = Trade.objects.create(buyer=self.john, seller=self.paul, price=5, quantity=2000)

        # Check if the cash flow is calculated correctly for John
        john_cash_flow = self.john.calculate_cash_flow()
        self.assertEqual(john_cash_flow, -10000)  # John's cash flow should be -10000 (he spent $10000)

        # Check if the cash flow is calculated correctly for Paul
        paul_cash_flow = self.paul.calculate_cash_flow()
        self.assertEqual(paul_cash_flow, 10000)  # Paul's cash flow should be 10000 (he received $10000)

        # Check if updating cash flows works
        self.john.update_cash_flow()
        self.paul.update_cash_flow()

        # Retrieve the updated cash flows
        updated_john = Player.objects.get(id=self.john.id)
        updated_paul = Player.objects.get(id=self.paul.id)

        # Check if the cash flows are updated correctly
        self.assertEqual(updated_john.cash_flow, -10000)
        self.assertEqual(updated_paul.cash_flow, 10000)
    
    def test_two_trades_cash_flow(self):
        # John buys 2000mt at $5 from Paul
        trade1 = Trade.objects.create(buyer=self.john, seller=self.paul, price=5, quantity=2000)

        # John sells 2000mt at $7 to Paul
        trade2 = Trade.objects.create(buyer=self.paul, seller=self.john, price=7, quantity=2000)

        # Check if the cash flow is calculated correctly for John after both trades
        john_cash_flow = self.john.calculate_cash_flow()
        self.assertEqual(john_cash_flow, 4000)  # John's cash flow should be 4000 (he sold 2000mt at $7 and bought 2000mt at $5)

        # Check if the cash flow is calculated correctly for Paul after both trades
        paul_cash_flow = self.paul.calculate_cash_flow()
        self.assertEqual(paul_cash_flow, -4000)  # Paul's cash flow should be -4000 (he bought 2000mt at $5 and sold 2000mt at $7)

        # Check if updating cash flows works
        self.john.update_cash_flow()
        self.paul.update_cash_flow()

        # Retrieve the updated cash flows
        updated_john = Player.objects.get(id=self.john.id)
        updated_paul = Player.objects.get(id=self.paul.id)

        # Check if the cash flows are updated correctly
        self.assertEqual(updated_john.cash_flow, 4000)
        self.assertEqual(updated_paul.cash_flow, -4000)



class BidOfferFormTest(TestCase):

    def setUp(self):
        # You can create any setup data here if needed
        pass

    def test_empty_aiplayer_bid_offer(self):
        # Test submission when AIPlayer is empty
        form_data = {'bid': 10.00, 'offer': 20.00}
        form = BidOfferForm(data=form_data)
        self.assertTrue(form.is_valid())  # Expecting the form to be valid
    
    def test_nonempty_aiplayer_bid_offer(self):
        # Creating a mock AIPlayer object
        AIPlayer.objects.create(bid=8.00, offer=22.00)
        
        # Test submission when AIPlayer has data
        form_data = {'bid': 10.00, 'offer': 20.00}
        form = BidOfferForm(data=form_data)
        self.assertTrue(form.is_valid())  # Expecting the form to be valid since the bid is higher than the AIPlayer bid and offer is lower than the AIPlayer offer

        # Test with bid equal to AIPlayer's offer
        form_data = {'bid': 22.00, 'offer': 20.00}
        form = BidOfferForm(data=form_data)
        self.assertFalse(form.is_valid())  # Expecting the form to be invalid

        # Test with offer equal to AIPlayer's bid
        form_data = {'bid': 10.00, 'offer': 8.00}
        form = BidOfferForm(data=form_data)
        self.assertFalse(form.is_valid())  # Expecting the form to be invalid
    
    def test_bid_cannot_be_higher_than_offer(self):
        # Create form data with bid higher than offer
        form_data = {
            'bid': 200,  # Bid
            'offer': 100  # Offer
        }
        form = BidOfferForm(data=form_data)
        # Trigger validation
        valid = form.is_valid()
        # Print errors after validation
        logger.debug(form.errors)

        
        # Assert the form is not valid
        self.assertFalse(form.is_valid())

        # Assert that the specific validation error is raised
        self.assertIn("The bid cannot be higher than the offer.", form.errors['__all__'])

        

class BidOfferFormErrorValidation(TestCase):
    
    def setUp(self):
        # Setup some initial AIPlayer data
        AIPlayer.objects.create(bid=150, offer=250)
        AIPlayer.objects.create(bid=160, offer=240)

    def test_validate_market_rules(self):
        # Test that a bid higher or equal to the lowest offer is invalid
        form = BidOfferForm(data={'bid': 240, 'offer': 260})
        self.assertFalse(form.is_valid())
        self.assertIn("Your bid price cannot be equal to or higher than the lowest offer in the market.", form.errors['__all__'])
        
        # Test that an offer lower or equal to the highest bid is invalid
        form = BidOfferForm(data={'bid': 140, 'offer': 160})
        self.assertFalse(form.is_valid())
        self.assertIn("Your offer price cannot be equal to or lower than the highest bid in the market.", form.errors['__all__'])

    def test_validate_bid_offer_relation(self):
        # Test that a bid higher than the offer is invalid
        form = BidOfferForm(data={'bid': 230, 'offer': 220})
        self.assertFalse(form.is_valid())
        self.assertIn("The bid cannot be higher than the offer.", form.errors['__all__'])

        # Test that a bid lower than the offer is valid
        form = BidOfferForm(data={'bid': 200, 'offer': 300})
        self.assertTrue(form.is_valid())

class LogoutViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout_view')
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_logout_authenticated_user(self):
        # Log the user in
        self.client.login(username='testuser', password='testpass123')

        # Check logout
        response = self.client.get(self.logout_url, follow=False) # Don't follow any redirects as index redirects to register
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)

        # After logout, the user should be anonymous
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_unauthenticated_user(self):
        # Try to log out when the user is not authenticated
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)


class LoginViewTest(TestCase):

    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"
        self.user = User.objects.create_user(self.username, password=self.password)
        self.player = Player.objects.create(user=self.user)

    def test_login_creates_new_game_session(self):
        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password
        })
        # Check if the redirection to the game page happens
        self.assertRedirects(response, reverse("game"))
        
        # Check if a new game session is created
        self.assertEqual(GameSession.objects.filter(players=self.player).count(), 1)

class LogoutViewTestGameSession(TestCase):
    
    def setUp(self):
        # Create a test user and player
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.player = Player.objects.create(user=self.user)

        # Create a test game session with the player
        self.game_session = GameSession.objects.create()
        self.game_session.players.add(self.player)

        self.client.login(username='testuser', password='12345')

    def test_logout_ends_game_session(self):
        response = self.client.get(reverse('logout_view'))  
        # Check if the user is logged out
        self.assertNotIn('_auth_user_id', self.client.session)

        # Refresh the game session from the database
        self.game_session.refresh_from_db()

        # Check that the active status is set to False
        self.assertEqual(self.game_session.active, False)

    def test_logout_sets_finished_at_timestamp(self):
        response = self.client.get(reverse('logout_view'))  # replace 'logout_view_name' with the actual name of your logout view in urls.py

        # Refresh the game session from the database
        self.game_session.refresh_from_db()

        # Check if the finished_at field is set and is recent (you may want to adjust the seconds in the timedelta depending on your exact needs)
        self.assertIsNotNone(self.game_session.finished_at)
        self.assertTrue(timezone.now() - self.game_session.finished_at < timezone.timedelta(seconds=5))

    def tearDown(self):
        # Cleanup any objects we created during tests
        self.game_session.delete()
        self.player.delete()
        self.user.delete()

class EmptyRegistrationTest(TestCase):

    def test_empty_fields_during_registration(self):
        # Define the URL for registration (replace with the actual URL name for your registration view)
        url = reverse('register')

        # Simulate a POST request with empty fields
        response = self.client.post(url, {
            "username": "",
            "password": "",
            "confirmation": ""
        })

        # Check if the response contains the appropriate error message
        self.assertContains(response, "All fields are required.")
    
    def test_password_confirmation_mismatch(self):
        
        # Test registration with mismatching password and confirmation.
        
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'password': 'password123',
            'confirmation': 'password456'  # intentionally different from the password
        })

        # Check if the response contains the expected error message
        self.assertContains(response, "Passwords must match.")
        
        # Check that the user was not registered (this might vary based on how you handle user creation)
        from django.contrib.auth.models import User
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='testuser')




class UniqueGameSessionTestCase(TestCase):

    def setUp(self):
        # Create two players
        self.player1 = Player.objects.create(user=User.objects.create(username='player1'))
        self.player2 = Player.objects.create(user=User.objects.create(username='player2'))

    def test_game_session(self):
        # Start a game session for player1
        session1 = start_game_session(self.player1)

        # Assert that player1 is in the session and that it's active
        self.assertTrue(session1.players.filter(pk=self.player1.pk).exists())
        self.assertTrue(session1.active)

        # Start another game session for player1
        session2 = start_game_session(self.player1)

        # Refresh session1 instance
        session1.refresh_from_db()

        # Assert that session1 is inactive and session2 is active
        self.assertFalse(session1.active)
        self.assertTrue(session2.active)

        # Start a game session for player2
        session3 = start_game_session(self.player2)

        # Assert that player2 is in session3 and it's active
        self.assertTrue(session3.players.filter(pk=self.player2.pk).exists())
        self.assertTrue(session3.active)

        # Assert that player1's old game session (session1) is still inactive
        self.assertFalse(session1.active)


class PlayerSummaryTests(TestCase):

    def setUp(self):
        # Create a user and player
        self.user = User.objects.create(username='testuser')
        self.user.set_password('testpass')  # Set and save hashed password
        self.user.save()
        self.player = Player.objects.create(user=self.user)

        # Create an AI Player
        self.ai_player = AIPlayer.objects.create(name="AI Trader 1", style='bullish', bid=100.00, offer=110.00) 

        # Create two game sessions
        self.game_session1 = GameSession.objects.create()
        self.player.games.add(self.game_session1)
        print(self.game_session1.players.all())  # This should show the player you added
        self.game_session1.ai_players.add(self.ai_player)
        
        self.game_session2 = GameSession.objects.create()
        self.player.games.add(self.game_session2)
        print(self.game_session2.players.all())  # This should show the player you added
        self.game_session2.ai_players.add(self.ai_player)
        

        # For simplicity, let's assume the player buys 2000 tonnes at $10 in the first session
        Trade.objects.create(game_session=self.game_session1, buyer=self.player, seller=self.ai_player, price=10, quantity=2000)
        
        # In the second session, the player sells 1000 tonnes at $20
        Trade.objects.create(game_session=self.game_session2, buyer=self.ai_player, seller=self.player, price=20, quantity=1000)

        self.game_session1.save()
        self.game_session2.save()
    
    def test_calculate_cash_flow(self):
        login_successful = self.client.login(username='testuser', password='testpass')
        self.assertTrue(login_successful, "User failed to log in")
        self.assertIn('_auth_user_id', self.client.session, "User is not in session after logging in")
        print("Player's game sessions:", self.player.games.all())

        # In session 1: player buys 2000 tonnes at $10 => cash_flow = -$20000
        self.assertEqual(self.player.calculate_cash_flow(self.game_session1), -20000)

        # In session 2: player sells 1000 tonnes at $20 => cash_flow = $20000
        self.assertEqual(self.player.calculate_cash_flow(self.game_session2), 20000)

        # Test using player_summary view function for the latest session
        response = self.client.get(reverse('player_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(float(response.json()['cash_flow'])), 20000)

    def test_calculate_position(self):
        login_successful = self.client.login(username='testuser', password='testpass')
        self.assertTrue(login_successful, "User failed to log in")
        self.assertIn('_auth_user_id', self.client.session, "User is not in session after logging in")
        print("Player's game sessions:", self.player.games.all())

        # In session 1: player buys 2000 tonnes => position = 2000
        self.assertEqual(self.player.calculate_position(self.game_session1), 2000)

        # In session 2: player sells 1000 tonnes => position = -1000
        self.assertEqual(self.player.calculate_position(self.game_session2), -1000)

        # Test using player_summary view function for the latest session
        response = self.client.get(reverse('player_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['position'], -1000)
