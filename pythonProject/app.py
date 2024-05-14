import bson
import os
import time
# import pyrebase
import requests
from pyrebase import pyrebase
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, redirect, flash, session
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

#access MongoDB Cluster
load_dotenv()
connection_string: str = os.environ.get("CONNECTION_STRING")
mongo_client: MongoClient = MongoClient(connection_string)

#add in database and collection from Atlas
database: Database = mongo_client.get_database("bookshelf")
collection: Collection = database.get_collection("books")


#instantiate
app: Flask = Flask(__name__)

config = {
    'apiKey': "AIzaSyBjkKU3gJP_Bs6uEnNF0AX7yJG1kNhMZzA",
    'authDomain': "library-9b9fe.firebaseapp.com",
    'projectId': "library-9b9fe",
    'storageBucket': "library-9b9fe.appspot.com",
    'messagingSenderId': "105503350290",
    'appId': "1:105503350290:web:4dbeed5587628363b202cb",
    'measurementId': "G-1TCH9064JZ",
    'databaseURL': ""
}

# const firebaseConfig = {
#     apiKey: "AIzaSyC5tN1JcL2QbPtuw7DncuvZegkLF5IzwHo",
#     authDomain: "bookshelf-4a75d.firebaseapp.com",
#     projectId: "bookshelf-4a75d",
#     storageBucket: "bookshelf-4a75d.appspot.com",
#     messagingSenderId: "443099329166",
#     appId: "1:443099329166:web:148dbd877c3bc880284fdf",
#     measurementId: "G-S9MPBP1639"
#   };

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()


# Set a secret key for the session
app.secret_key = 'your_secret_key_here'


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/home')
def home():
    # Check if the user is logged in
    if 'username' in session:
        # Retrieve books for the logged-in user
        user_books = collection.find_one({'username': session['username']})
        if user_books:
            books = user_books['books']
            return render_template('home.html', username=session['username'], books=books)
        else:
            flash('No books found for this user', 'error')
            return redirect(url_for('index'))  # Redirect to the index page if no books are found
    else:
        flash('Please log in to view your books', 'error')
        return redirect(url_for('login'))  # Redirect to the login page if the user is not logged in

@app.route('/books', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session:
        flash('Please log in to add a book', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        book_name = request.form.get('bookName')
        pages = int(request.form.get('pages'))

        # Insert the book under the logged-in user
        collection.update_one({'username': session['username']}, {'$push': {'books': {'name': book_name, 'pages': pages}}})
        flash('Book added successfully', 'success')

        return redirect(url_for('add_book'))
    else:
        return render_template('add.html')


@app.route('/update', methods=['GET', 'POST'])
def update_book():
    if 'username' not in session:
        flash('Please log in to update a book', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get data from the form
        old_book_name = request.form.get('oldBookName')
        new_book_name = request.form.get('newBookName')
        new_pages = int(request.form.get('newPages'))

        # Update the book in the database for the logged-in user
        result = collection.update_one({'username': session['username'], 'books.name': old_book_name}, {
            '$set': {'books.$.name': new_book_name, 'books.$.pages': new_pages}})
        if result.modified_count > 0:
            flash('Book updated successfully', 'success')
        else:
            flash('Book not found', 'error')

        return redirect(url_for('update_book'))
    else:
        return render_template('update.html')

@app.route('/delete', methods=['GET', 'POST'])
def delete_book():
    if 'username' not in session:
        flash('Please log in to delete a book', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get data from the form
        book_name = request.form.get('bookName')

        # Delete the book from the database for the logged-in user
        result = collection.update_one({'username': session['username']}, {'$pull': {'books': {'name': book_name}}})
        if result.modified_count > 0:
            flash(f'Book "{book_name}" deleted successfully', 'success')
        else:
            flash(f'Book "{book_name}" does not exist', 'error')

        return redirect(url_for('delete_book'))
    else:
        return render_template('delete.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get registration data from the form
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Create user with email and password using Firebase authentication
            auth.create_user_with_email_and_password(email, password)

            # Store user in MongoDB
            existing_user = collection.find_one({'username': email})
            if existing_user:
                flash(
                    'Email already exists. Please use a different email address.',
                    'error')
                return redirect(url_for('register'))
            else:
                collection.insert_one(
                    {'username': email, 'password': password, 'books': []})
                flash('Account created successfully', 'success')
                return redirect(url_for(
                    'login'))  # Redirect to the login page after successful registration
        except requests.exceptions.HTTPError as e:
            error_data = e.args[0].response.json()
            error_message = error_data['error']['message']
            if 'WEAK_PASSWORD' in error_message:
                flash('Password should be at least 6 characters', 'error')
            else:
                flash(error_message, 'error')
            return redirect(url_for('register'))
        except Exception as e:
            flash(str(e),
                  'error')  # Display error message if registration fails
            return redirect(
                url_for('register'))  # Redirect back to the register page

    else:
        # If it's a GET request, simply render the register.html template
        return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Check if the user exists in MongoDB
            user = collection.find_one({'username': email})
            if user:
                # If user exists, attempt to sign in using Firebase authentication
                auth.sign_in_with_email_and_password(email, password)
                session['username'] = email
                flash('Login successful', 'success')
                return redirect(url_for('home'))
            else:
                flash('User does not exist', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            flash(str(e), 'error')  # Display error message if login fails
            return redirect(url_for('login'))

    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the index page
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")


