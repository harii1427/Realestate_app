from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import os
from flask import abort
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "ibots"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = 'static/photos/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3'])

database = SQLAlchemy(app)
migrate = Migrate(app, database)

class User(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(20), unique=True, nullable=False)
    password = database.Column(database.String(60), nullable=False)
    likes = database.relationship('Like', backref='user', lazy=True)


class Photo(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    filename = database.Column(database.String(255), nullable=False)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    likes = database.relationship('Like', backref='photo', lazy=True)



class Like(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    photo_id = database.Column(database.Integer, database.ForeignKey('photo.id'), nullable=False)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def upload_form():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        # Check if the user is loaded correctly
        if user is None:
            flash('User not found. Please log in again.')
            return redirect(url_for('login'))

        photos = Photo.query.all()
        

        if user.username:
            return render_template('upload_super.html', user=user, photos=photos)
    else:
        return redirect(url_for('login'))


@app.route('/photos')
def photos():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif')
        photos = Photo.query.filter(or_(*(Photo.filename.endswith(ext) for ext in image_extensions))).all()

        return render_template('photos.html', user=user, files=photos)

    else:
        return redirect(url_for('login'))


@app.route('/videos')
def videos():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        search_query = request.args.get('search', '')
        
        video_files = Photo.query.filter(Photo.filename.like('%.mp4')).all()
        
        return render_template('videos.html', user=user, files=video_files, search_query=search_query)
    else:
        return redirect(url_for('login'))


# Modify your /audio route in your Flask application
@app.route('/audio', methods=['GET'])
def audio():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        # Get the search query from the form submission
        search_query = request.args.get('search', '')
        
        audio_files = [audio.filename for audio in Photo.query.filter(Photo.filename.like('%.mp3')).all() if search_query.lower() in audio.filename.lower()]
        
        return render_template('audio.html', user=user, files=audio_files, search_query=search_query)
    else:
        return redirect(url_for('login'))

@app.route('/song_player/<filename>')
def song_player(filename):
    return render_template('song_player.html', filename=filename)


@app.route('/', methods=['GET', 'POST'])
def main_page():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        if request.method == 'POST':
            # Handle file uploads for the super account
            if 'files[]' in request.files:
                files = request.files.getlist('files[]')
                file_names = session.get('file_names', [])

                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_names.append(filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)

                        # Create a new Photo instance and set the user_id
                        photo = Photo(filename=filename, user_id=user.id)
                        database.session.add(photo)
                        database.session.commit()
                    else:
                        return redirect(request.url)

                session['file_names'] = file_names

            photos = Photo.query.all()

            if user.username:
                return render_template('upload_super.html', user=user, photos=photos)
            else:
                return render_template('upload_super.html', user=user, photos=photos)
        else:
            photos = Photo.query.all()
            return render_template('upload_super.html', user=user, photos=photos)
    else:
        return redirect(url_for('login'))


@app.route('/super_upload', methods=['POST'])
def super_upload():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        if user.username:

            if 'files[]' not in request.files:
                flash('No file part')
                return redirect(request.url)

            files = request.files.getlist('files[]')

            file_names = session.get('file_names', [])

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_names.append(filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    photo = Photo(filename=filename)
                    database.session.add(photo)
                    database.session.commit()
                else:
                    return redirect(request.url)

            session['file_names'] = file_names

        return redirect(url_for('main_page'))
    else:
        return redirect(url_for('login'))


def upload_image():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('files[]')

        file_names = session.get('file_names', [])

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_names.append(filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                photo = Photo(filename=filename)
                database.session.add(photo)
                database.session.commit()

            else:
                return redirect(request.url)

        session['file_names'] = file_names

        return redirect(url_for('upload_super.html'))

    else:
        return redirect(url_for('login'))


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='photos/' + filename), code=301)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            return redirect(url_for('upload_form'))


    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('')
        else:
            new_user = User(username=username, password=password)
            database.session.add(new_user)
            database.session.commit()

    return render_template('register.html')


@app.route('/like/<int:photo_id>', methods=['GET', 'POST'])
def like(photo_id):
    if 'user_id' in session:
        user_id = session['user_id']
        like = Like.query.filter_by(user_id=user_id, photo_id=photo_id).first()

        if not like:
            like = Like(user_id=user_id, photo_id=photo_id)
            database.session.add(like)

            photo = Photo.query.get(photo_id)
            photo.likes.append(like)

            database.session.commit()

        return redirect(url_for('upload_form'))
    else:
        return redirect(url_for('login'))


@app.route('/dislike/<int:photo_id>', methods=['POST'])
def dislike(photo_id):
    if 'user_id' in session:
        user_id = session['user_id']

        like = Like.query.filter_by(user_id=user_id, photo_id=photo_id).first()

        if like:

            photo = Photo.query.get(photo_id)
            if like in photo.likes:
                photo.likes.remove(like)

            database.session.delete(like)
            database.session.commit()

        return redirect(url_for('upload_form'))
    else:
        return redirect(url_for('login'))

@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if 'user_id' in session:
        user_id = session['user_id']

        # Get the photo and check if the user is the owner
        photo = Photo.query.get(photo_id)

        if not photo:
            return redirect(url_for('upload_form'))

        # Assuming each Photo has a user_id attribute
        if photo.user_id == user_id:
            # Delete associated likes
            likes_to_delete = Like.query.filter_by(photo_id=photo.id).all()
            for like in likes_to_delete:
                database.session.delete(like)

            # Delete the photo
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)

            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                flash("File not found: {}".format(file_path))

            database.session.delete(photo)
            database.session.commit()

            return redirect(url_for('upload_form'))
        else:
            # User is not the owner of the photo, handle accordingly
            abort(403)  # Forbidden

    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('upload_form'))


if __name__ == "__main__":
    with app.app_context():
        database.create_all()
        app.run(debug=True, host="0.0.0.0")
