import bson
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
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

@app.route('/')
def index():
    return render_template("index.html")

#CREATE AND READ
@app.route("/books", methods=["GET","POST"])
def books():
    if request.method == "POST":
        #CREATE
        book: str = request.json["book"]
        pages: str = request.json["pages"]

        #insert new book into book collection in ATLAS
        collection.insert_one({"book":book, "pages":pages})

        return f"CREATE: your book {book} ({pages}pages) has been added to your bookshelf."

    elif request.method == "GET":
        #READ
        bookshelf = list(collection.find())
        novels = []

        for titles in bookshelf:
            book = titles["book"]
            pages = titles["pages"]
            shelf = {"book":book, "pages":pages}
            novels.insert(0, shelf)
        return  novels


#UPDATE
@app.route("/books/<string:book_id>", methods=["PUT"])
def update_book(book_id: str):
    new_book: str = request.json["book"]
    new_pages: str = request.json["pages"]
    collection.update_one({"_id":bson.ObjectId(book_id)}, {"$set":{"book":new_book, "pages":new_pages}})
    return f"UPDATE: Your book has been updated to: {new_book} ({new_pages}pages)."



#DELETE
@app.route("/books/<string:book_id>", methods=["DELETE"])
def remove_book(book_id:str):
    collection.delete_one({"_id": bson.ObjectId(book_id)})

    return f"DELETE: Your book (id = {book_id}) has been removed from your bookshelf."




if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")