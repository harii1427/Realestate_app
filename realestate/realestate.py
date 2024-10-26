from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estate.db'
UPLOAD_FOLDER="static/photos/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    state_and_city = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    details = db.Column(db.String(200))
    thumbnail = db.Column(db.String(100))
    photos = db.relationship('Photo', backref='property', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    filename = db.Column(db.String(100))

@app.route('/')
def index():
    properties = Property.query.all()
    return render_template('test_index.html', properties=properties)

@app.route('/sell')
def sell():
    return render_template('sell.html')

@app.route('/details')
def details():
    return render_template('details.html')


@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Create the uploads directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Initialize thumbnail_filename variable
        thumbnail_filename = None

        # Handle thumbnail upload
        thumbnail_file = request.files['thumbnails']
        if thumbnail_file:
            thumbnail_filename = thumbnail_file.filename
            thumbnail_file.save(os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename))

        # Handle other photos upload
        other_photos = request.files.getlist('photos')
        for photo in other_photos:
            photo_filename = photo.filename
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        # Create Property instance with thumbnail_filename
        address = request.form['address']
        state_and_city = request.form['stateAndCity']
        pincode = request.form['Pincode']
        phone = request.form['phone']
        details = request.form['details']
        new_property = Property(address=address, state_and_city=state_and_city, pincode=pincode, 
                                phone=phone, details=details, thumbnail=thumbnail_filename)
        db.session.add(new_property)
        db.session.commit()

    return redirect(url_for('index'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
