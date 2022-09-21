"""Book model tests."""

# run these tests like:
#
#    python -m unittest test_book_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Book, UserBook

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:/// nyt_best_sellers_test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class BookModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        user = User.signup(
            "test_user", "test_email@email.com", "test_password", None)

        book = Book.add_book("test_title", "test_author",
                             "test_description", "test_publisher", 1234567890)

        db.session.commit()

        self.book = book

        self.user = user

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_userbook_model(self):
        """Does basic model work?"""

        relation = UserBook(
            user_id=self.user.id,
            book_id=self.book.id
        )

        db.session.add(relation)
        db.session.commit()

        # User should have 1 book
        self.assertEqual(len(self.user.books), 1)
        # Book should have 1 user
        self.assertEqual(len(self.book.users), 1)
        # The title should be the one we set
        self.assertEqual(self.user.books[0].title, "test_title")
        # The book's user_id should be the same than our user's id
        self.assertEqual(relation.user_id, self.user.id)
        # The book shoul'd not be read as default
        self.assertEqual(relation.read_or_not, False)
