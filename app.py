import os

import datetime
from flask import Flask, render_template, flash, redirect, session, g
from sqlalchemy.exc import IntegrityError

from sqlalchemy import or_
import requests
from functions import do_login, do_logout

from flask_caching import Cache

from forms import UserAddForm, LoginForm,  UserEditForm
from models import db, connect_db, User, Book, UserBook

CURR_USER_KEY = "curr_user"
BASE_URL = "https://api.nytimes.com/svc/books/v3/lists/"
API_KEY = "hqYOQpGSpdTrvEmdSR6k6ZGNvzJvC6nf"

app = Flask(__name__)


# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///nyt_best_sellers'))

app.config['DEBUG'] = True
app.config['CACHE_TYPE'] = "SimpleCache"
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

cache = Cache(app)

connect_db(app)


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

#######################################################################################
#####LOGIN-LOGOUT-SIGNUP ROUTES ##########################################################
#######################################################################################


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            # We will get an Integrity Error if the username already exist
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        # If authentication fails we get false and render the form again
        user = User.authenticate(form.username.data,
                                 form.password.data)
        # If true we login and redirect
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    return redirect("/")

#######################################################################################
##################BOOK ROUTES ##########################################################
#######################################################################################


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no books
    - logged in: current week's best sellers
    """
    # If the user is not the one in session render the anonym root route
    if g.user:

        unformated_date = datetime.datetime.now()
        date = unformated_date.strftime("%Y-%m-%d")
        lists = do_books_overview(date)
        return render_template('home.html', lists=lists)

    else:
        return render_template('home-anon.html')


@app.route('/books/<int:isbn>')
def show_book(isbn):
    """Show book acording to the ISBN"""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # If the book is in our DB, we don't make a request and retrieve the information from our databse

    book = Book.query.filter_by(isbn_10=isbn).first()

    if book:
        return render_template('book_show.html', book=book)
    # If the book is not in our DB, we retieve the data from the API
    else:
        try:
            res = requests.get(
                f"{BASE_URL}best-sellers/history.json",
                params={"api-key": API_KEY,
                        "isbn": isbn})
            data = res.json()
            book = data["results"][0]
            # API response is a list, therefore we get the first book even when it's only one book in the list

            title = book["title"]
            author = book["author"]
            description = book["description"]
            publisher = book["publisher"]

            # ISBN_10 is already given from the url
            book2 = Book.add_book(title=title,
                                  author=author,
                                  description=description,
                                  publisher=publisher,
                                  isbn_10=isbn)

            db.session.commit()

            db_book = Book.query.get_or_404(book2.id)
            # We'll see information about the current book
            return render_template('book_show.html', book=db_book)

        # The API is currently throwing empty results when looking for particular books with ISBN_10
        except IndexError as e:
            flash("Book's details curently unavailable.", "danger")
            return redirect("/")


@app.route('/books/<int:isbn>/track', methods=["POST"])
def track_book(isbn):
    """Make current user and book relation for tracking the book"""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    book = Book.query.filter_by(isbn_10=isbn).first()

    # If the book is in the DB, we let the user track the book

    if book:
        try:

            track_book = UserBook(user_id=g.user.id, book_id=book.id)

            db.session.add(track_book)
            db.session.commit()

        except IntegrityError:
            # We will get an Integrity Error if the username already exist
            flash("User is already tracking this book", 'danger')
            return redirect(f"/books/{isbn}")

        return redirect("users/books")

    # If the book is not in our DB, we redirect to root route
    else:
        flash("The book is unavailable to track or the ISBN is incorrect.", "danger")
        return redirect("/")


@app.route('/books/stop-tracking/<int:isbn>', methods=["POST"])
def stop_track_book(isbn):
    """Delete user and book relation for tracking the book"""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    book = Book.query.filter_by(isbn_10=isbn).first()

    # If the book is in the DB, we let the user untrack the book

    if book:
        try:

            g.user.books.remove(book)
            db.session.commit()

            return redirect(f"/books/{isbn}")

        except:
            # We will get an error if the user tries to untrack an already untracked book
            flash("User is not tracking this book", 'danger')
            return redirect(f"/books/{isbn}")

    # If the book is not in our DB, we redirect to root route
    else:
        flash("The book is unavailable to track or the ISBN is incorrect.", "danger")
        return redirect("/")

#######################################################################################
#############USER-BOOKS ROUTES ##########################################################
#######################################################################################


@app.route('/users/books')
def user_books():
    """Show basic information about the user's tracked books 
    """
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    else:
        return render_template('user_track_books.html', user=g.user)


@app.route('/users/books/<int:isbn>/read', methods=["POST"])
def read_unread_book(isbn):
    """Let user select if they have read the book or not"""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    book = Book.query.filter_by(isbn_10=isbn).first()

    # If the book is in the DB, we let the user select if the book has been read or not

    if book:

        # query to see if there is a relation between the book and the user
        relation = UserBook.query.filter(
            UserBook.user_id == g.user.id, UserBook.book_id == book.id).first()

        # If the relation exist and 'read_or_not' is true, change to false
        if relation and relation.read_or_not:

            relation.read_or_not = False
            db.session.commit()
            return redirect("/users/books")

        # If the relation exist and 'read_or_not' is false, change to true
        elif relation:
            relation.read_or_not = True
            db.session.commit()
            return redirect("/users/books")

        # Redirect if the relation doesn't exist
        else:
            flash("The user isn't tracking this book.", "danger")
        return redirect("/")

    # If the book is not in our DB, we redirect to root route
    else:
        flash("The book is unavailable to track or the ISBN is incorrect.", "danger")
        return redirect("/")


#######################################################################################
###################USER ROUTES ##########################################################
#######################################################################################

@app.route('/users/<int:user_id>')
def user_details(user_id):
    """Render user's details page"""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template("users/details.html", user=user)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    # delete user from DB
    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


@app.route('/users/edit', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    # If the user is not the one in session redirect
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    # Data to pass to the form to be pre-filled wit the user's data
    data = {"username": g.user.username,
            "email": g.user.email, "image_url": g.user.image_url}

    form = UserEditForm(data=data)

    # If the form  has valid data and CRSF-Token
    if form.validate_on_submit():
        user = User.authenticate(g.user.username,
                                 form.password.data)
        # Change user's info to the form data ifauthentication is correct
        if user:
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            db.session.add(user)
            db.session.commit()
            flash(f"{user.username}, your changes were made successfully", "success")
            return redirect(f"/users/{user.id}")
        # Render form if the credentials are incorrect
        flash("Invalid credentials.", 'danger')

    return render_template('users/edit.html', form=form)

##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask


@cache.memoize(timeout=86400)
def do_books_overview(date):
    """Get this weeks books overview"""
    res = requests.get(
        f"{BASE_URL}full-overview.json",
        params={"api-key": API_KEY,
                "published_date": date})
    data = res.json()
    results = data["results"]
    lists = results["lists"]

    return lists
