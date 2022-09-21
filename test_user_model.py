"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Book, UserBook

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()

        u1 = User.signup(
            "test_user1", "test_email1@email.com", "test_password", None)

        db.session.commit()

        self.u1 = u1

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no books or book relations
        self.assertEqual(len(u.books), 0)
        self.assertEqual(len(u.users_books), 0)

    def test_signup(self):
        """Test if the signup method creates a new user"""
        # We create a new user
        user = User.signup(
            "test_user3", "test_email3@email.com", "test_password", None)

        db.session.commit()
        # We check if the information we gave is correct
        self.assertEqual(user.username, "test_user3")
        self.assertEqual(user.email, "test_email3@email.com")
        self.assertNotEqual(user.password, "test_password")
        # We got a default image url when a image is not given
        self.assertIsNotNone(user.image_url)
        # The new user shouldn't have any users or followers
        self.assertEqual(len(user.books), 0)
        self.assertEqual(len(user.users_books), 0)

    def test_invalid_username_signup(self):
        """Test if the signup method doesn't create a new user when a username value is invalid"""
        # We create a new user with an invalid username
        user = User.signup(
            None, "test_email3@email.com", "test_password", None)
        # We should get an exception
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        """Test if the signup method doesn't create a new user when a email value is invalid"""
        # We create a new user with an invalid email
        user = User.signup(
            "test_user3", None, "test_password", None)
        # We should get an exception
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_passwordl_signup(self):
        """Test if the signup method doesn't create a new user when a password value is invalid"""
        # We should get an exception when we give an empty password as we have it "Nullable=False"
        with self.assertRaises(ValueError) as context:
            user = User.signup(
                "test_user3", "test_email3@email.com", None, None)

    def test_authentication(self):
        """We are testing the authenticate method for Loging In"""
        user = User.authenticate(self.u1.username, "test_password")
        # With a valid authentication we should get our user back
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test_user1")

    def test_invalid_authentication(self):
        bad_user = User.authenticate("wrong", "test_password")
        # With an invalid authentication False should be returned
        self.assertFalse(bad_user)
        bad_password = User.authenticate(self.u1.username, "wrong")
        self.assertFalse(bad_password)
