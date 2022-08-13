#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from ast import dump
from cgitb import text
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from sqlalchemy import distinct
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy.orm import load_only
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500), nullable=False, unique=True)
    facebook_link = db.Column(db.String(120), nullable=False, unique=True)
    website_link = db.Column(db.String(120), nullable=False, unique=True)
    seeking_talent = db.Column(db.String)
    seeking_description = db.Column(db.String)
    show = db.relationship('Show', backref='venues', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name} {self.city} {self.state} {self.address} {self.phone} {self.image_link} {self.facebook_link} {self.website_link}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String())
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.String)
    seeking_description = db.Column(db.String)
    show = db.relationship('Show', backref='artists', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name} {self.city} {self.state} {self.phone} {self.image_link} {self.facebook_link} {self.website_link}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

Artist_show = db.Table('artist_show',
    db.Column('show_id', db.Integer, db.ForeignKey('shows.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)

Venue_show = db.Table('venue_show',
    db.Column('show_id', db.Integer, db.ForeignKey('shows.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), primary_key=True)
)

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
      return f'< Venue {self.id} {self.venue_id} {self.artist_id} {self.start_time}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#





def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  locations = db.session.query(distinct(Venue.city), Venue.state).all()
  current_time = datetime.now()
  data = []
  for location in locations:
      city = location[0]
      state = location[1]

      Allvenues = Venue.query.filter(Venue.city == city, Venue.state==state).all()
      for venue in Allvenues:
        upcoming = Show.query.filter(venue.id == venue.id).filter(Show.start_time>current_time).all()
        venues = []
        venues.append({
        'id' : venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(upcoming)
        })
      location_data = {
            "city": city,
            "state": state,
            "venues": venues
        }
      data.append(location_data)
      # flash(data)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search-term', '')
  print(search_term)
  venues = db.session.query(Venue).filter(Venue.name.ilike(f"%{search_term}%")).all()
  current_time = datetime.now()
  data = []
  for venue in venues:
    upcoming = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > current_time).all()
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len(upcoming)
    })
    response={
      "count": len(venues),
      "data": data
    }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  current_time = datetime.now()
  upcoming = Show.query.join(Venue).filter(Show.venue_id == venue_id).filter(Show.start_time > current_time)
  upcoming_shows = []
  for show in upcoming:
    upcoming_shows.append({
        'artist_id': show.artist_id,
        'artist_name': show.artists.name,
        'artist_image_link': show.artists.image_link,
        'start_time': str(show.start_time)
    })

  past = Show.query.join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time < current_time)
  past_shows = []
  for show in past:
    past_shows.append({
        'artist_id': show.artist_id,
        'artist_name': show.artists.name,
        'artist_image_link': show.artists.image_link,
        'start_time': str(show.start_time)
    })
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = {}
  data['id'] = venue.id
  data['name'] = venue.name
  data['genres'] = venue.genres
  data['address'] = venue.address
  data['city'] = venue.city
  data['state'] = venue.state
  data['phone'] = venue.phone
  data['website_link'] = venue.website_link
  data['facebook_link'] = venue.facebook_link
  data['seeking_talent'] = venue.seeking_talent
  data['seeking_description'] = venue.seeking_description
  data['image_link'] = venue.image_link
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_show_count'] = len(past_shows)
  data['upcoming_show_count'] = len(upcoming_shows)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
    error = False
    try:
      name = request.form.get('name')
      city = request.form.get('city')
      state = request.form.get('state')
      phone = request.form.get('phone')
      address = request.form.get('address')
      genres = request.form.get('genres')
      image_link = request.form.get('image_link')
      facebook_link = request.form.get('facebook_link')
      website_link = request.form.get('website_link')
      seeking_talent = request.form.get('seeking_talent')
      seeking_description = request.form.get('seeking_descriptionk')
      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, image_link=image_link,
                    facebook_link=facebook_link, website_link=website_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        abort(500)
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
        venue = Venue.query.get(venue_id)
        for show in venue.show:
            db.session.delete(show)
        db.session.delete(venue)
        db.session.commit()
  except:
        db.session.rollback()
        error = True
  finally:
        db.session.close()
  if error == True:
        abort(500)
  else:
        return jsonify({'success': True})
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
        'id': artist.id,
        'name': artist.name
    })
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search-term', '')
  artists = db.session.query(Artist).filter(func.lower(Artist.name).ilike(f'%{search_term}%')).all()
  current_time = datetime.now()
  data = []
  for artist in artists:
    upcoming = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > current_time).all()
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': len(upcoming)
    })
  response={
    "count": len(artists),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  current_time = datetime.now()
  upcoming = Show.query.join(Artist).filter(Show.artist_id == artist_id).filter(Show.start_time > current_time)
  upcoming_shows = []
  for show in upcoming:
    upcoming_shows.append({
        'venue_id': show.venue_id,
        'venue_name': show.venues.name,
        'venue_image_link': show.venues.image_link,
        'start_time': str(show.start_time)
    })

  past = Show.query.join(Artist).filter(
      Show.artist_id == artist_id).filter(Show.start_time < current_time)
  past_shows = []
  for show in past:
    past_shows.append({
        'venue_id': show.venue_id,
        'venue_name': show.venues.name,
        'venue_image_link': show.artists.image_link,
        'start_time': str(show.start_time)
    })
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_idt
  data = {}
  data['id'] = artist.id
  data['name'] = artist.name
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website'] = artist.website_link
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue
  data['seeking_description'] = artist.seeking_description
  data['image_link'] = artist.image_link
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_show_count'] = len(past_shows)
  data['upcoming_show_count'] = len(upcoming_shows)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)

  artist_data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
   }
  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
    artist = Artist.query.get(artist_id)
    name = request.form.get('name')
    artist.name = name
    city = request.form.get('city')
    artist.city = city
    state = request.form.get('state')
    artist.state = state
    phone = request.form.get('phone')
    artist.phone = phone
    genres = request.form.get('genres')
    artist.genres = genres
    image_link = request.form.get('image_link')
    artist.image_link = image_link
    facebook_link = request.form.get('facebook_link')
    artist.facebook_link = facebook_link
    website_link = request.form.get('website_link')
    artist.websitelink = website_link
    seeking_talent = request.form.get('seeking_talent')
    artist.seeking_talent = seeking_talent
    seeking_description = request.form.get('seeking_descriptionk')
    artist.seeking_description = seeking_description
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updateded.')
      abort(500)
  else:
    flash('Artist' + request.form['name'] + ' was successfully updated!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venue_data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
   }
  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
    venue = Venue.query.get(venue_id)
    name = request.form.get('name')
    venue.name = name
    city = request.form.get('city')
    venue.city = city
    state = request.form.get('state')
    venue.state = state
    phone = request.form.get('phone')
    venue.phone = phone
    address = request.form.get('address')
    venue.address = address
    genres = request.form.get('genres')
    venue.genres = genres
    image_link = request.form.get('image_link')
    venue.image_link = image_link
    facebook_link = request.form.get('facebook_link')
    venue.facebook_link = facebook_link
    website_link = request.form.get('website_link')
    venue.websitelink = website_link
    seeking_talent = request.form.get('seeking_talent')
    venue.seeking_talent = seeking_talent
    seeking_description = request.form.get('seeking_descriptionk')
    venue.seeking_description = seeking_description
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        genres = request.form.get('genres')
        image_link = request.form.get('image_link')
        facebook_link = request.form.get('facebook_link')
        website_link = request.form.get('website_link')
        seeking_venue = request.form.get('seeking_venue')
        seeking_description = request.form.get('seeking_description')
        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, image_link=image_link,
                      facebook_link=facebook_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      abort(500)
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  display_show = []
  shows = Show.query.order_by('start_time').all()
  # flash(shows)
  data = []

  for show in shows:
    data.append({
      'venue_id': show.venue_id,
      'venue_name': show.venues.name,
      'artist_id': show.artist_id,
      'artist_name': show.artists.name,
      'artist_image_link': show.artists.image_link,
      'start_time': str(show.start_time)
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error == True:
    flash('An error occurred. Show could not be listed.')
    abort(500)
  else:
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
