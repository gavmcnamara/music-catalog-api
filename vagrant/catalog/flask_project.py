from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tables import Base, Genre, Band

app = Flask(__name__)

engine = create_engine('sqlite:///genresofmusic.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/genres/<int:genre_id>/')
def genretItem(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    items = session.query(Band).filter_by(genre_id=genre.id)
    output = ''
    for i in items:
        output += i.name
        output += '</br>'
        output += i.year
        output += '</br>'
        output += i.description
        output += '</br>'
        output += '</br>'
    return output

# Task 1: Create route for newMenuItem function here


@app.route('/genre/<int:genre_id>/new/')
def newBandItem(genre_id):
    return "page to create a new menu item. Task 1 complete!"

# Task 2: Create route for editMenuItem function here


@app.route('/genre/<int:genre_id>/<int:band_id>/edit/')
def ediBandItem(genre_id, band_id):
    return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here


@app.route('/genre/<int:genre_id>/<int:menu_id>/delete/')
def deleteGenreItem(genre_id, band_id):
    return "page to delete a menu item. Task 3 complete!"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)