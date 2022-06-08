#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
from datetime import datetime
import collections
import collections.abc
collections.Callable = collections.abc.Callable

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from sqlalchemy import desc
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *


#----------------------------------------------------------------------------#
# Import models.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
        __tablename__ = 'venues'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        city = db.Column(db.String(120))
        state = db.Column(db.String(120))
        address = db.Column(db.String(120))
        phone = db.Column(db.String(120))
        genres = db.Column(db.ARRAY(db.String), nullable=False)
        website = db.Column(db.String(120))
        image_link = db.Column(db.String(500))
        facebook_link = db.Column(db.String(120))
        seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
        seeking_description = db.Column(db.String(2000))
        shows = db.relationship('Show', backref = "venue", lazy=True, 
                cascade="all, delete")

class Artist(db.Model):
        __tablename__ = 'artists'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        city = db.Column(db.String(120))
        state = db.Column(db.String(120))
        phone = db.Column(db.String(120))
        genres = db.Column(db.ARRAY(db.String), nullable=False)
        website = db.Column(db.String(120))
        image_link = db.Column(db.String(500))
        facebook_link = db.Column(db.String(120))
        seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
        seeking_description = db.Column(db.String(2000))
        shows = db.relationship('Show', backref = "artist", lazy=True, 
                cascade="all, delete")

class Show(db.Model):
        __tablename__ = "shows"
        id = db.Column(db.Integer, primary_key=True)
        start_time = db.Column(db.DateTime())
        venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
        artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# app = Flask(__name__)
# moment = Moment(app)
# app.config.from_object('config')
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
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


#    Venues
#    ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = {}
    for row in Venue.query.all():
        city = row.city
        if city not in data:
            data[city] = {}
            data[city]['city'] = city
            data[city]['state'] = row.state
            data[city]['venues'] = []
        venue_info = {}
        venue_info['id'] = row.id
        venue_info['name'] = row.name
        upcoming_shows = db.session.query(Show).filter(Show.venue_id == row.id)\
        .filter(Show.start_time > datetime.now()).all()
        venue_info['num_upcoming_shows'] = len(upcoming_shows)
        data[city]['venues'].append(venue_info)

    return render_template('pages/venues.html', areas=data.values());

@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_term = request.form.get('search_term', '')
    search_results = db.session.query(Venue)\
    .filter(Venue.name.ilike(f'%{search_term}%')).all()

    response = {}
    response['count'] = len(search_results)
    response['data'] = []
    for row in search_results:
        venue_info = {}
        venue_info['id'] = row.id
        venue_info['name'] = row.name
        upcoming_shows = db.session.query(Show).filter(Show.venue_id == row.id)\
        .filter(Show.start_time > datetime.now()).all()
        venue_info['num_upcoming_shows'] = len(upcoming_shows)
        response['data'].append(venue_info)

    return render_template('pages/search_venues.html', results=response, 
        search_term=search_term)

@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    
    # basic information about the venue
    venue = Venue.query.filter_by(id=venue_id).first()
    data = {}
    data['id'] = venue.id
    data['name'] = venue.name
    data['genres'] = venue.genres
    data['address'] = venue.address
    data['city'] = venue.city
    data['state'] = venue.state
    data['phone'] = venue.phone
    data['website'] = venue.website
    data['facebook_link'] = venue.facebook_link
    data['seeking_talent'] = venue.seeking_talent
    if venue.seeking_talent:
        data['seeking_description'] = venue.seeking_description
    data['image_link'] = venue.image_link

    # get the data of past shows and upcoming shows
    data['past_shows'] = []
    data['upcoming_shows'] = []

    past_shows = Show.query.filter(Show.venue_id == venue_id)\
        .filter(Show.start_time < datetime.now()).order_by(desc(Show.start_time)).all()

    data['past_shows_count'] = len(past_shows)
    for row in past_shows:
        show_info = {}
        show_info['artist_id'] = row.artist_id
        show_info['artist_name'] = row.artist.name
        show_info['artist_image_link'] = row.artist.image_link
        show_info['start_time'] = row.start_time
        data['past_shows'].append(show_info)

    upcoming_shows = Show.query.filter(Show.venue_id == venue_id)\
        .filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()
    data['upcoming_shows_count'] = len(upcoming_shows)
    for row in upcoming_shows:
        show_info = {}
        show_info['artist_id'] = row.artist_id
        show_info['artist_name'] = row.artist.name
        show_info['artist_image_link'] = row.artist.image_link
        show_info['start_time'] = row.start_time
        data['upcoming_shows'].append(show_info)

    return render_template('pages/show_venue.html', venue=data)

#    Create Venue
#    ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    try:
        newVenue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            website=form.website_link.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data, 
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data)

        db.session.add(newVenue)
        db.session.commit()
        flash(f'Venue {form.name.data} was successfully listed!')
    except:
        db.session.rollback()
        flash(f'An error occurred. Venue {form.name.data} could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        db.session.delete(venue)
        db.session.commit()
        flash('The venue has been removed together with all of its shows.')
        return render_template('pages/home.html')
    except ValueError:
        db.session.rollback()
        flash('It was not possible to delete this Venue')
    finally:
        db.session.close()
    return redirect(url_for('venues'))

#    Artists
#    ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.order_by('id').all()
    data = []
    for row in artists:
        artist_info = {}
        artist_info['id'] = row.id
        artist_info['name'] = row.name
        data.append(artist_info)

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    response = {}
    search_results = db.session.query(Artist)\
    .filter(Artist.name.ilike(f'%{search_term}%')).all()

    response = {}
    response['count'] = len(search_results)
    response['data'] = []
    for row in search_results:
        artist_info = {}
        artist_info['id'] = row.id
        artist_info['name'] = row.name
        upcoming_shows = db.session.query(Show).filter(Show.artist_id == row.id)\
        .filter(Show.start_time > datetime.now()).all()
        artist_info['num_upcoming_shows'] = len(upcoming_shows)
        response['data'].append(artist_info)

    return render_template('pages/search_artists.html', results=response, 
        search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    # basic information about the artist
    artist = Artist.query.filter_by(id=artist_id).all()[0]
    data = {}
    data['id'] = artist.id
    data['name'] = artist.name
    data['genres'] = artist.genres
    data['city'] = artist.city
    data['state'] = artist.state
    data['phone'] = artist.phone
    data['website'] = artist.website
    data['facebook_link'] = artist.facebook_link
    data['seeking_venue'] = artist.seeking_venue
    if artist.seeking_venue:
        data['seeking_description'] = artist.seeking_description
    data['image_link'] = artist.image_link

    # get the data of past shows and upcoming shows
    data['past_shows'] = []
    data['upcoming_shows'] = []

    past_shows = Show.query.filter(Show.artist_id == artist_id)\
        .filter(Show.start_time < datetime.now()).order_by(desc(Show.start_time)).all()

    data['past_shows_count'] = len(past_shows)
    for row in past_shows:
        show_info = {}
        show_info['venue_id'] = row.venue_id
        show_info['venue_name'] = row.venue.name
        show_info['venue_image_link'] = row.venue.image_link
        show_info['start_time'] = row.start_time
        data['past_shows'].append(show_info)

    upcoming_shows = Show.query.filter(Show.artist_id == artist_id)\
        .filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()
    data['upcoming_shows_count'] = len(upcoming_shows)
    for row in upcoming_shows:
        show_info = {}
        show_info['venue_id'] = row.venue_id
        show_info['venue_name'] = row.venue.name
        show_info['venue_image_link'] = row.venue.image_link
        show_info['start_time'] = row.start_time
        data['upcoming_shows'].append(show_info)

    return render_template('pages/show_artist.html', artist=data)

#    Update
#    ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_result = Artist.query.get(artist_id)
    artist = {}
    artist['id'] = artist_result.id
    artist['name'] = artist_result.name
    artist['genres'] = artist_result.genres
    artist['city'] = artist_result.city
    artist['state'] = artist_result.state
    artist['phone'] = artist_result.phone
    artist['website'] = artist_result.website
    artist['facebook_link'] = artist_result.facebook_link
    artist['seeking_venue'] = artist_result.seeking_venue
    artist['seeking_description'] = artist_result.seeking_description
    artist['image_link'] = artist_result.image_link

    form.name.data = artist_result.name
    form.genres.data = artist_result.genres
    form.city.data = artist_result.city
    form.state.data = artist_result.state
    form.phone.data = artist_result.phone
    form.website_link.data = artist_result.website
    form.facebook_link.data = artist_result.facebook_link
    form.seeking_venue.data = artist_result.seeking_venue
    form.seeking_description.data = artist_result.seeking_description
    form.image_link.data = artist_result.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    try:
        artist.name=form.name.data
        artist.city=form.city.data
        artist.state=form.state.data
        artist.phone=form.phone.data
        artist.genres=form.genres.data
        artist.website=form.website_link.data
        artist.image_link=form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.seeking_venue=form.seeking_venue.data
        artist.seeking_description=form.seeking_description.data
        db.session.commit()
        flash(f'Artist {artist.name} was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())

        flash(f'An error occurred. Artist {artist.name} could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    
    venue_result = Venue.query.get(venue_id)
    venue = {}
    venue['id'] = venue_result.id
    venue['name'] = venue_result.name
    venue['genres'] = venue_result.genres
    venue['address'] = venue_result.address
    venue['city'] = venue_result.city
    venue['state'] = venue_result.state
    venue['phone'] = venue_result.phone
    venue['website'] = venue_result.website
    venue['facebook_link'] = venue_result.facebook_link
    venue['seeking_talent'] = venue_result.seeking_talent
    venue['seeking_description'] = venue_result.seeking_description
    venue['image_link'] = venue_result.image_link

    form.name.data = venue_result.name
    form.genres.data = venue_result.genres
    form.address.data = venue_result.address
    form.city.data = venue_result.city
    form.state.data = venue_result.state
    form.phone.data = venue_result.phone
    form.website_link.data = venue_result.website
    form.facebook_link.data = venue_result.facebook_link
    form.seeking_talent.data = venue_result.seeking_talent
    form.seeking_description.data = venue_result.seeking_description
    form.image_link.data = venue_result.image_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes

    form = VenueForm()
    venue = Venue.query.get(venue_id)

    try:
        venue.name=form.name.data
        venue.address=form.address.data
        venue.city=form.city.data
        venue.state=form.state.data
        venue.phone=form.phone.data
        venue.genres=form.genres.data
        venue.website=form.website_link.data
        venue.image_link=form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.seeking_talent=form.seeking_talent.data
        venue.seeking_description=form.seeking_description.data
        db.session.commit()
        flash(f'Venue {venue.name} was successfully updated!')
    except:
        db.session.rollback()
        flash(f'An error occurred. Venue {venue.name} could not be updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#    Create Artist
#    ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    form = ArtistForm()
    try:
        newArtist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            website=form.website_link.data,
            image_link=form.image_link.data,
            facebook_link = form.facebook_link.data, 
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data)

        db.session.add(newArtist)
        db.session.commit()
        flash(f'Artist {form.name.data} was successfully listed!')
    except:
        db.session.rollback()
        flash(f'An error occurred. Artist {form.name.data} could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

#    Shows
#    ----------------------------------------------------------------
@app.route('/shows')
def shows():

    # basic information about the shows
    shows = Show.query.order_by('id').all()
    data = []
    for row in shows:
        show_info = {}
        show_info['venue_id'] = row.venue_id
        show_info['venue_name'] = row.venue.name
        show_info['artist_id'] = row.artist_id
        show_info['artist_name'] = row.artist.name
        show_info['artist_image_link'] = row.artist.image_link
        show_info['start_time'] = format_datetime(row.start_time)
        print(type(show_info['start_time']))
        data.append(show_info)

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    form = ShowForm()
    try:
        newShow = Show(
            venue_id=form.venue_id.data,
            artist_id=form.artist_id.data,
            start_time=form.start_time.data)
        db.session.add(newShow)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exec_info())
        flash(f'An error occurred. Show could not be listed.')
    finally:
        db.session.close()
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
