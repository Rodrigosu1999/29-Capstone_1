# NY Times Best Sellers Tracker  
## Introduction
This website works with the NY Times Best Sellers API to add extra functionality to their best-sellers website.    
Besides the user being able to look ath the weeks overview, a user is able to look at specific books and "track" them on their account. All tracked books will be able to be selected as "read" or "not read".
This was done because most people (myself included) work better with visual trackers than with notes or datasheets and the NY Times page only displayed an overview and doesn't have this extra functionality that is usefull for reading enthusiasts.  

### Deployed app  
https://nyt-best-sellers-tracker.herokuapp.com/  

## Follow these instructions if you want to play with the code
1. Intall "python-3.9.14" or greater version if you don't have it installed.
2. Create a virtual environment in your machine if you don't want to install all dependencies globally. 
3. Run the following command in your console.   
  ``` 
  pip3 install -r requirements.txt 
  ```
4. Create your database with postgresql so you can start adding data.
5. Run the app through Flask  
  ``` 
  flask run
  ```


## User Flow  
- The user will start by loging in to the webpage if they have an account; if not, the user will sign up to create a new account.  
- After logging in, the user will be shown the full overview of the current week's best sellers divided by categories. If the user wants to know extra information about a particular book, they can click on the book's title and the user will be redirected to the book's details page.  
- The details page show the book's title, author, publisher, ISBN10 and a short description. There will also be a button for the user to track the book and will  be redirected to their tracked books page.  
- At the tracked books page the user can look at all their tracked books and toggle if they have read the book or not. In order to untrack a book, the user can click on the book's title to redirect to the details page (where the "Track" button will now be "Untrack").
- If the user needs to change their account's information, they can click on ther profile picture and click on the edit button.

## API and Notes  

The API we are using is NY Times Books API (https://developer.nytimes.com/docs/books-product/1/overview). ***While the API has a lot of useful information for us to use, when we retrieved information for particular books (with their ISBN10) the response was an empty list.*** This limited the amount of books that can be downloaded to the database and to display their information.

The app was created with Python (working with Flask, SQLAlchemy, WTForms, Jinja). Jinja was used to render HTML pages. The databse is handled with Flask-SQLAlchemy working with PostgreSQL.

## Potential Future Features
- Search bar to look for books that aren't in the current week Best Sellers List.  
- Users interactivity to look at other's tracked books.
- Accessability to look at previous weeks Best Sellers List

