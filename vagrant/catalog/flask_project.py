from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tables import Base, Genre, Band, User
# importing for password security
from flask import session as login_session
import random
import string
# importing for OAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Music Application"

# Connect to database
engine = create_engine('sqlite:///favoritemusic.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps
                                 ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if not, make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:' \
              ' 150px;-webkit-border-radius:' \
              ' 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        return redirect('/')
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
        return redirect('/')


# JSON APIs to view Genre Information #DONE
@app.route('/genres/<int:genre_id>/band/JSON')
def bandItem(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    items = session.query(Band).filter_by(
        genre_id=genre_id).all()
    return jsonify(BandItems=[i.serialize for i in items])


# ADD JSON ENDPOINT HERE
@app.route('/genres/<int:genre_id>/band/<int:band_id>/JSON')
def bandItemJSON(genre_id, band_id):
    bandItem = session.query(Band).filter_by(id=band_id).one()
    return jsonify(BandItem=bandItem.serialize)


@app.route('/genres/JSON')
def genresJSON():
    genres = session.query(Genre).all()
    return jsonify(genres=[g.serialize for g in genres])


# Show all Genres
@app.route('/')
@app.route('/genres')
def homePage():
    genre = session.query(Genre).order_by(Genre.name)
    if 'username' not in login_session:
        return render_template('publicgenres.html', genre=genre)
    else:
        return render_template('main.html', genre=genre)


# Show bands information in particular genre
@app.route('/genres/<int:genre_id>/')
@app.route('/genres/<int:genre_id>/band/')
def genreItem(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    creator = getUserInfo(genre.user_id)
    items = session.query(Band).filter_by(
        genre_id=genre_id).all()
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('band.html',
                               items=items, genre=genre, creator=creator)
    else:
        return render_template('band.html',
                               items=items, genre=genre, creator=creator)


# Create new Genre
@app.route('/genres/new/', methods=['GET', 'POST'])
def newGenre():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newGenre = Genre(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newGenre)
        flash('New Genre %s Successfully Created' % newGenre.name)
        session.commit()
        return redirect(url_for('homePage'))
    else:
        return render_template('newGenres.html')


# Edit a Genre
@app.route('/genres/<int:genre_id>/edit/', methods=['GET', 'POST'])
def editGenre(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedGenre = session.query(
        Genre).filter_by(id=genre_id).one()
    if editedGenre.user_id != login_session['user_id']:
        return redirect('/')
    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
            return redirect(url_for('homePage', genre_id=genre_id))
    else:
        return render_template(
            'editGenre.html', genre=editedGenre)


# Delete a Genre
@app.route('/genres/<int:genre_id>/delete/', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    genreToDelete = session.query(
        Genre).filter_by(id=genre_id).one()
    if genreToDelete.user_id != login_session['user_id']:
        flash("Not Authorized")
        return redirect("/")
    if request.method == 'POST':
        session.delete(genreToDelete)
        flash('%s Successfully Deleted' % genreToDelete.name)
        session.commit()
        return redirect(
            url_for('homePage', genre_id=genre_id))
    else:
        return render_template(
            'deleteGenre.html', genre=genreToDelete, genre_id=genre_id)


# Create new band
@app.route('/genres/<int:genre_id>/band/new', methods=['GET', 'POST'])
def newGenreItem(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        return redirect('/')
    if request.method == 'POST':
        newItem = Band(name=request.form['name'], description=request.form[
                           'description'], year=request.form['year'],
                       genre_id=genre_id, user_id=genre.user_id)
        session.add(newItem)
        session.commit()
        flash('New Band %s Item Successfully Created' % (newGenreItem))
        return redirect(url_for('genreItem', genre_id=genre_id))
    else:
        return render_template('newgenreitem.html', genre_id=genre_id)


# Edit current band
@app.route('/genres/<int:genre_id>/band/<int:band_id>/edit',
           methods=['GET', 'POST'])
def editGenreItem(genre_id, band_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Band).filter_by(id=band_id).one()
    genre = session.query(Genre).filter_by(id=genre_id).one()
    if login_session['user_id'] != genre.user_id:
        flash("Not authorized")
        return redirect('/')
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['year']:
            editedItem.price = request.form['year']
        session.add(editedItem)
        session.commit()
        flash('Band Item Successfully Edited')
        return redirect(url_for('genreItem', genre_id=genre_id))
    else:

        return render_template(
            'editgenreitem.html', genre_id=genre_id,
            band_id=band_id, item=editedItem)


# Delete a Band
@app.route('/genres/<int:genre_id>/band/<int:band_id>/delete',
           methods=['GET', 'POST'])
def deleteGenreItem(genre_id, band_id):
    if 'username' not in login_session:
        return redirect('/login')
    genre = session.query(Genre).filter_by(id=genre_id).one()
    itemToDelete = session.query(Band).filter_by(id=band_id).one()
    if login_session['user_id'] != genre.user_id:
        return redirect('/')
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Band Item Successfully Deleted')
        return redirect(url_for('genreItem', genre_id=genre_id))
    else:
        return render_template('deletegenreitem.html', item=itemToDelete)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
