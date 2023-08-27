from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Player, Trade, AIPlayer, GameSession
from django.urls import reverse
from .forms import BidOfferForm
from django.utils import timezone
import logging

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
