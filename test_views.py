"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Book, User, UserBook

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///nyt_best_sellers_test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

# ISBN10 for Fairy Tale by Stephen King (publisher = Scribner)
TEST_ISBN = 1668002175


class ViewTestCase(TestCase):
    """Test views pages"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Book.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                               email="test@test.com",
                               password="testuser",
                               image_url=None)
        # Book we know will work from the API
        book = Book.add_book("DESPERATION IN DEATH", "J.D. Robb",
                             "The 55th book of the In Death series. Eve Dallas is reminded of her past as she investigates a possible sex trafficking ring.", "St. Martin's", 1250278244)

        book2 = Book.add_book("I'M GLAD MY MOM DIED", "Jennette McCurdy",
                              "The actress and filmmaker describes her eating disorders and difficult relationship with her mother.", "Simon & Schuster", 1982185821)

        db.session.commit()

        relation = UserBook(user_id=testuser.id, book_id=book2.id)

        db.session.commit()

        self.testuser = testuser
        self.book = book
        self.book2 = book2
        self.relation = relation

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_bs_overview(self):
        """Render homepage"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.get("/")
            html = resp.get_data(as_text=True)

            # Make sure it works
            self.assertEqual(resp.status_code, 200)

            book = Book.query.first()
            # There should be 1 book in our db as we have not selected another book in particular
            self.assertTrue(book)
            # Testing for page to render
            self.assertIn("NY Times Best Sellers", html)
            # Testing for book cards to render
            self.assertIn('<div class="card-body">', html)

    def test_anon_homepage(self):
        """Render homepage when no user is logged in"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            resp = c.get("/")
            html = resp.get_data(as_text=True)

            # Make sure it works
            self.assertEqual(resp.status_code, 200)

            # Testing for page to render
            self.assertIn("First Time?", html)
            # Testing for book cards to render
            self.assertIn(
                '<a href="/signup" class="btn btn-primary">Sign up</a>', html)

    ############################################
    ##########BOOKS#############################
    #############################################

    def test_book_show(self):
        """Testing for a particular book to show"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/books/{TEST_ISBN}")
            html = resp.get_data(as_text=True)

            # Testing for good response
            self.assertEqual(resp.status_code, 200)
            # Title should be displayed
            self.assertIn("FAIRY TALE", html)
            # Publisher should be diplayed
            self.assertIn("Scribner", html)
            # Book should be untracked
            self.assertIn("Track", html)

    def test_book_track(self):
        """Testing for tracking a book """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp2 = c.post(f"/books/1250278244/track", follow_redirects=True)
            html = resp2.get_data(as_text=True)

            # Testing for good response
            self.assertEqual(resp2.status_code, 200)
            # Title should be displayed
            self.assertIn("DESPERATION IN DEATH", html)
            # Author should be diplayed
            self.assertIn('<h5 class="card-title">by J.D. Robb</h5>', html)
            # Book should be unread
            self.assertIn("Not read", html)

    ##############################################
    ######USER VIEWS##############################
    ###########################################

    def test_user_show(self):
        """Testing for the correct user to show"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            # Testing for good response
            self.assertEqual(resp.status_code, 200)
            # Username should be displayed
            self.assertIn("testuser", html)
            # Email should be diplayed to the user
            self.assertIn("test@test.com", html)
            # User should have 0 books
            self.assertIn("<p>0</p>", html)
