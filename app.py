from flask import Flask, jsonify, request, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
import os
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///'+os.path.join(basedir,'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'  #change this IRL
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# todo
app.config['MAIL_USERNAME'] = ''    #add username from mailtrap
app.config['MAIL_PASSWORD'] = ''    #add password from mailtrap


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('database created')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('database dropped')

@app.cli.command('db_seed')
def db_seed():
    jalebi = Movie(movie_name='Jalebi',location='Delhi',show_time='noon',theater_id=1111,theater_name= 'deva',total_tickets= 50,available_tickets=25,ticket_price =100,status= 'upcoming',release= '03/08/2020' )
    db.session.add(jalebi)
    db.session.commit()
    print('database seeded')


@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/upcoming')
def upcoming():
    up_movies = Movie.query.filter_by(status='upcoming').all()
    result = movies_schema.dump(up_movies)
    return render_template("upcoming_movies.html",result=result)

@app.route('/current')
def current():
    return render_template("current_movies.html")

@app.route('/search')
def search():
    return render_template("search_movies.html")

@app.route('/theaters', methods=['POST'])
def theaters():
    movie_name = request.form['movie_name']
    theaters_list = Movie.query.filter_by(movie_name=movie_name).all()
    result = movies_schema.dump(theaters_list)
    return render_template("theaters.html", result=result)

@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str,age: int ):
    if(age < 18):
        return  jsonify(message='Sorry '+name+", not old enough"),401
    return jsonify(message='Welcome '+name+", you are old enough")

@app.route('/planets', methods=['GET'])
def planets():
    planets_list=Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)

@app.route('/register', methods=['POST'])
def register():
    email= request.form['email']
    test = User.query.filter_by(email=email).first()
    if test :
        return jsonify(message="That email already exists"), 409
    else:
        first_name= equest.form['first_name']
        last_name=request.form['last_name']
        password=request.form['password']
        user= User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User Created Sucessfully"), 201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    
    test = User.query.filter_by(email=email,password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="login succeeded", access_token=access_token)
    else:
        return jsonify(message="Bad email or pass"), 401

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email:str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your password is " + user.password, sender="admin@planetary.com", recipients=[email])
        mail.send(msg)
        return jsonify(message="password sent to" + email)
    else:
        return jsonify(message="email doesn't exist"), 401

@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id : int):
    planet=Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result= planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify("planet doesn't exist"), 404

@app.route('/add_planet', methods=['POST'])
@jwt_required
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message="there is already a planet in that name"), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type, home_star=home_star,mass=mass, radius=radius, distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="planet added"), 201

@app.route('/update_planet', methods=['PUT'])
@jwt_required
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="planet updated"), 202
    else:
        return jsonify(message="planet doesnot exist"), 404

@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required
def remove_planet(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="planet deleted"), 202
    else:
        return jsonify(message="planet doesnot exist"), 404



# database models
class User(db.Model):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String)
    movie_id = Column(Integer)
    movie_name = Column(String)
    theater_id = Column(Integer)
    theater_name = Column(String)
    tickets = Column(String)  

class Movie(db.Model):
    __tablename__ = 'movies'
    movie_id = Column(Integer, primary_key=True)
    movie_name = Column(String)
    location = Column(String)
    show_time = Column(String)
    theater_id = Column(Integer)
    theater_name = Column(String)
    total_tickets = Column(Integer)
    available_tickets = Column(Integer)
    ticket_price = Column(Integer)  
    status = Column(String)
    release = Column(String)

class UserLog(db.Model):
    __tablename__ = 'user_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,)
    user_name = Column(String)
    role = Column(String)
    last_login = Column(String)
    expiry = Column(String)
    reg_date = Column(String)

class UserSchema(ma.Schema):
    class Meta:
        fields = ( 'user_id', 'user_name', 'movie_id', 'movie_name', 'theater_id', 'theater_name', 'tickets' )

class MovieSchema(ma.Schema):
    class Meta:
        fields = ( 'movie_id', 'movie_name', 'location', 'show_time', 'theater_id', 'theater_name',
         'total_tickets','available_tickets','ticket_price', 'status', 'release' )

class UserLogSchema(ma.Schema):
    class Meta:
        fields = ( 'id', 'user_id', 'user_name', 'role', 'last_login', 'expiry', 'reg_date' )


user_schema = UserSchema()
users_schema = UserSchema(many=True)

user_log_schema = UserLogSchema()
users_log_schema = UserLogSchema(many=True)

movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)

if __name__ == '__main__':
    app.run()
