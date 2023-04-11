# Import necessary libraries

from flask import Flask, render_template, request, redirect, session

import numpy as np
import os
import tensorflow

from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model

from flask_sqlalchemy import SQLAlchemy

# load model
model = load_model("model/v3_pred_cott_dis.h5")
print('@@ Model loaded')

# prediction functionality functions


def pred_cot_dieas(cott_plant):
  test_image = load_img(cott_plant, target_size=(150, 150))  # load image
  print("@@ Got Image for prediction")

  # convert image to np array and normalize
  test_image = img_to_array(test_image)/255
  test_image = np.expand_dims(test_image, axis=0)  # change dimention 3D to 4D

  result = model.predict(test_image).round(3)  # predict diseased palnt or not
  print('@@ Raw result = ', result)

  pred = np.argmax(result)  # get the index of max value

  if pred == 0:
    return "Healthy Cotton Plant", 'healthy_plant_leaf.html'  # if index 0 burned leaf
  elif pred == 1:
      return 'Diseased Cotton Plant', 'disease_plant.html'  # if index 1
  elif pred == 2:
      return 'Healthy Cotton Plant', 'healthy_plant.html'  # if index 2  fresh leaf
  else:
    return "Healthy Cotton Plant", 'healthy_plant.html'  # if index 3

# ------------>>pred_cot_dieas<<--end


# Create flask instance
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'


# Database functionality
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def authenticate_user(email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            return True
        else:
            return False

    def create_user(name, email, password):
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()


# db functionality end

# error handlers for different HTTP error codes
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


# render index.html page at start
@app.route('/')
def home():
    return render_template('index.html')


# render loginSignup page and login functionality
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if login credentials are valid
        email = request.form['email']
        password = request.form['password']
        # return redirect('/dashboard') # TOBE resolved for login
        if User.authenticate_user(email, password):
            session['email'] = email
            return redirect('/dashboard')
        else:
            return render_template('loginSignup.html', error='Invalid email or password')

    # Render the login page
    if request.method == 'GET':
        return render_template('loginSignup.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Create the user account
        User.create_user(name, email, password)
        session['email'] = email
        return redirect('/dashboard')
    else:
        return render_template('loginSignup.html')

# render dashboard page

@app.route('/dashboard', methods=['GET'])
def dashboard():
    # return render_template('dashboard.html') # TOBO resolved for login
    if 'email' in session:
        email = session['email']
        return render_template('dashboard.html', email=email)
    else:
        return redirect('/login')


# logout functionality
@app.route('/logout')
def logout():
    # Remove the email from the session if it's there
    session.pop('email', None)
    return redirect('/login')
# render predict page for detection of image
# get input image from client then predict class and render respective .html page for solution
@app.route("/predict", methods = ['GET', 'POST'])
def predict():
    if request.method == 'POST':
        file = request.files['image']  # fet input
        filename = file.filename
        print("@@ Input posted = ", filename)

        file_path = os.path.join('static/user uploaded', filename)
        file.save(file_path)

        print("@@ Predicting class......")
        pred, output_page = pred_cot_dieas(cott_plant=file_path)

        return render_template(output_page, pred_output= pred, user_image = file_path)


# For local system & cloud
if __name__ == "__main__":
    app.secret_key = os.urandom(12)  # secret key
    app.run(threaded=False)
