import traceback
import re
from utils import get_response_dict, update_user_fields
from flask import Flask,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates

app=Flask("__name__")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config['JSON_SORT_KEYS'] = False

db=SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer,primary_key=True,)
    username = db.Column(db.String(50),nullable=False)
    password = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(50),nullable=False)
    city = db.Column(db.String(80))
    country = db.Column(db.String(80))

    def __repr__(self):
        return self.username

    @validates("username")
    def validate_username(self,key,username):
        if User.query.filter_by(username=username).first():
            raise AssertionError("User with username "+username+" already exists!")
        if len(username)<3 or len(username)>50:
            raise AssertionError("Username must be between 3 and 50 characters!")
        return username

    @validates("password")
    def validate_password(self,key,password):
        pattern_uppercase = re.compile("[A-Z]")
        pattern_numerical = re.compile("[0-9]")
        pattern_special_characters = re.compile("[!@#$%^&*()_+\\-=\\[\\]{};':\\\|,\\.<>\\/?]")
        if not password:
            raise AssertionError("You must provide a password!")
        if len(password)<10:
            raise AssertionError("Password is too short! Please, provide a password with at least 10 characters!")
        if not pattern_uppercase.search(password):
            raise AssertionError("Password does not contain any capital letter!")
        if not pattern_special_characters.search(password):
            raise AssertionError("Password does not contain any special character!")
        if not pattern_numerical.search(password):
            raise AssertionError("Password does not contain any numerical value!")

        return password

    @validates("email")
    def validate_email(self,key,email):
        if not email:
            raise AssertionError("You must provide an email!")
        if not re.match("[^@]+@[^@]+\.[^@]+",email):
            raise AssertionError("E-mail is not written in valid form!")

        return email

    @validates("country")
    def validate_country(self,key,country):
        if not country:
            raise AssertionError("You must provide a country!")
        if len(country)>80:
            raise AssertionError("Name of the country is not supposed to have more than 80 characters!")

        return country

    @validates("city")
    def validate_city(self,key,city):
        if not city:
            raise AssertionError("You must provide a city!")
        if len(city)>80:
            raise AssertionError("Name of the city is not supposed to have more than 80 characters!")

        return city

    def get_user_dict(self):
        user_dict= {
            "user_id": self.user_id,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "country": self.country,
            "city": self.city
        }
        return user_dict

    def update_field(self,key,value):
        if key == "password":
            self.password = value
        elif key == "email":
            self.email = value
        elif key == "country":
            self.country = value
        elif key == "city":
            self.country = value
        else:
            raise Exception("You did not provide adequate keys!")


@app.route("/user/<username>",methods=["POST"])
def create_new_user(username):
    user={}
    message = None
    status_code = "400 BAD REQUEST"
    try:
        user = User(username=username, password=request.json.get("password",None), email=request.json.get("email",None),
                    country=request.json.get("country",None), city=request.json.get("city",None))
        db.session.add(user)
        db.session.commit()
        message = "User with username "+username+" is successfully created!"
        status_code = "201 CREATED"
    except AssertionError as ass_error:
        db.session.rollback()
        message = ass_error.message
        status_code = "409 CONFLICT" if message == "User with username "+username+" already exists!" else "422 UNPROCESSABLE ENTITY"
    except AttributeError as attr_error:
        db.session.rollback()
        message = "You must provide JSON in the body of the request!"
    except Exception as ex:
        db.session.rollback()
        message = traceback.format_exc().split("\n")[-2]

    return get_response_dict(user,message,status_code)

@app.route("/user")
def get_all_users():
    users = User.query.all()
    users_list=[]
    for user in users:
        user_dict=user.get_user_dict()
        users_list.append(user_dict)
    status_code = "200 OK" if users else "404 NOT FOUND"
    message = "Users are found!" if users else "Users are not found!"
    return get_response_dict(users_list,message,status_code)

@app.route("/user/<username>")
def get_user(username):
    user = User.query.filter_by(username=username).first()
    message = "User with username "+username+" is found!" if user else "User with username "+username+" does not exist!"
    status_code = "200 OK" if user else "404 NOT FOUND"
    return get_response_dict(user,message,status_code)

@app.route("/user/<username>",methods=["PUT"])
def update_user(username):
    user = {}
    message = None
    status_code = "400 BAD REQUEST"
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return get_response_dict({},"User with username "+username+" does not exist!","404 NOT FOUND")
        update_user_fields(user,request.json)
        db.session.commit()
        message = "User with username "+username+" is successfully updated!"
        status_code = "200 OK"
    except AssertionError as ass_error:
        db.session.rollback()
        message = ass_error.message
        status_code = "422 UNPROCESSABLE ENTITY"
    except AttributeError as attr_error:
        db.session.rollback()
        message = "You must provide JSON in the body of the request!"
    except Exception as ex:
        db.session.rollback()
        message = traceback.format_exc().split("\n")[-2]
    return get_response_dict(user,message,status_code)

@app.route("/user/<username>",methods=["DELETE"])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    message = "User with username "+username+" does not exist!"
    status_code = "404 NOT FOUND"
    try:
        db.session.delete(user)
        db.session.commit()
        message = "User with username " + username + " is deleted!"
        status_code = "200 OK"
    except Exception as ex:
        db.session.rollback()
        print(traceback.print_exc())

    return get_response_dict(user,message,status_code)

@app.route("/login",methods=["POST"])
def login():
    user = {}
    message = None
    status_code = "400 BAD REQUEST"
    try:
        if not request.json.get("username", None) or not request.json.get("password", None):
            return get_response_dict({}, "You must provide both username and password!", "400 BAD REQUEST")
        user = User.query.filter_by(username=request.json.get("username",None), password=request.json.get("password",None)).first()
        if not user:
            return get_response_dict({},"Your username or password does not match any user!","404 NOT FOUND")
        message = "Successfully loggeed in!"
        status_code = "200 OK"
    except AttributeError as attr_err:
        print(traceback.print_exc())
        message = "You must provide JSON in the body of the request!"
    except Exception as ex:
        print(traceback.print_exc())
        message = traceback.format_exc().split("\n")[-2]
    return get_response_dict(user,message,status_code)