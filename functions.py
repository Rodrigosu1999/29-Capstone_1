"""File to separate functionality from view's app"""

from app import session


def do_login(user):
    """Log in user. from session"""

    session["curr_user"] = user.id


def do_logout():
    """Logout user from session."""

    if "curr_user" in session:
        del session["curr_user"]
