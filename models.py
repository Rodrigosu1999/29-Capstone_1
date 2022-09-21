"""SQLAlchemy models for NY Times Best Sellers Tracker."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    books = db.relationship("Book",
                            secondary="users_books",
                            backref="users")

    users_books = db.relationship("UserBook",
                                  cascade="all,delete",
                                  backref="User")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}>"

    def count_books(self):
        """How many books is the user following?"""

        count = len(self.books)

        return count

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Book(db.Model):
    """An individual book."""

    __tablename__ = 'books'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(140),
        nullable=False
    )
    description = db.Column(
        db.String,
        nullable=False
    )
    author = db.Column(
        db.String(140),
        nullable=False
    )
    publisher = db.Column(
        db.String(140),
        nullable=False
    )

    isbn_10 = db.Column(
        db.Integer,
        nullable=False,
        unique=True
    )

    users_books = db.relationship("UserBook",
                                  cascade="all,delete",
                                  backref="Book")

    @classmethod
    def add_book(cls, title, author, description, publisher,
                 isbn_10):
        """Add book into our databse
        """

        book = Book(
            title=title,
            author=author,
            description=description,
            publisher=publisher,
            isbn_10=isbn_10
        )

        db.session.add(book)
        return book


class UserBook(db.Model):
    """Connection of a user <-> book."""

    __tablename__ = 'users_books'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        unique=True
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey('books.id', ondelete="cascade"),
        unique=True
    )

    read_or_not = db.Column(
        db.Boolean,
        default=False,
    )


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
