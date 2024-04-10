import bson
import os
import time
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

# book = {"book":"Harry Potter", "pages":800}
# collection.insert_one(book)

#instantiate
app: Flask = Flask(__name__)

# Set a secret key for the session
app.secret_key = 'your_secret_key_here'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/home')
def home():
    books = collection.find()
    return render_template('home.html', books=books)

@app.route('/books', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_name = request.form.get('bookName')
        pages = int(request.form.get('pages'))

        # Check if the book already exists in the database
        existing_book = collection.find_one({'book': book_name})
        if existing_book:
            flash('Book already exists in the database', 'error')
        else:
            collection.insert_one({'book': book_name, 'pages': pages})
            flash('Book added successfully', 'success')

        # Regardless of whether the book was added or not, stay on the add_book route
        return redirect(url_for('add_book'))  # Redirect back to add.html
    else:
        return render_template('add.html')


@app.route('/update', methods=['GET', 'POST'])
def update_book():
    if request.method == 'POST':
        # Get data from the form
        old_book_name = request.form.get('oldBookName')
        new_book_name = request.form.get('newBookName')
        new_pages = int(request.form.get('newPages'))

        # Update the book in the database
        result = collection.update_one({'book': old_book_name}, {
            '$set': {'book': new_book_name, 'pages': new_pages}})
        if result.modified_count > 0:
            flash('Book updated successfully', 'success')
        else:
            flash('Book not found', 'error')

        # Regardless of whether the book was updated or not, stay on the update_book route
        return redirect(url_for('update_book'))  # Redirect back to update.html
    else:
        return render_template('update.html')


@app.route('/delete', methods=['GET', 'POST'])
def delete_book():
    if request.method == 'POST':
        # Get data from the form
        book_name = request.form.get('bookName')

        # Check if the book exists in the database
        existing_book = collection.find_one({'book': book_name})
        if existing_book:
            # Delete the book from the database
            collection.delete_one({'book': book_name})
            flash(f'Book "{book_name}" deleted successfully', 'success')
        else:
            flash(f'Book "{book_name}" does not exist', 'error')

        # Regardless of whether the book was deleted or not, stay on the delete_book route
        return redirect(url_for('delete_book'))  # Redirect back to delete.html
    else:
        return render_template('delete.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")