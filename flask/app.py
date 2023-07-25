import re
import os
import time
import hashlib
from flask import Flask,request,jsonify, session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, and_
from flask_sqlalchemy import SQLAlchemy,BaseQuery
from sqlalchemy.exc import OperationalError
from time import sleep
from flask_session import Session
from werkzeug.exceptions import HTTPException


class RetryingQuery(BaseQuery):
    __retry_count__ = 3
    __retry_sleep_interval_sec__ = 0.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __iter__(self):
        attempts = 0
        while True:
            attempts += 1
            try:
                return super().__iter__()
            except OperationalError as ex:
                if "Lost connection to MySQL server during query" not in str(ex):
                    raise
                if attempts < self.__retry_count__:
                    sleep(self.__retry_sleep_interval_sec__)
                    continue
                else:
                    raise


db = SQLAlchemy(query_class=RetryingQuery)
app = Flask(__name__)
# app.config['DEBUG'] = True
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Max number of allowed failed attempts
MAX_FAILED_ATTEMPTS = 5

# Minimum wait time in seconds after 5 failed attempts
WAIT_TIME_SECONDS = 60

with open('/run/secrets/db-password','r') as f:
    db_pwd = f.read()

with open('/run/secrets/password-salt','r',encoding='utf-8') as f:
    PASSWORD_SALT = f.read()

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://root:{db_pwd}@db:3306/Account"
db.init_app(app)

# ORM SQLAlchemy
class User(db.Model):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    password: Mapped[str] = mapped_column(String(128))




@app.route("/create_account",methods=["POST"])
def create_account():

    ret = dict()
    ret['success'] = False

    # check mimetype
    if not request.is_json:
        ret['reson'] =  "Wrong mimetype"
        return jsonify(ret)

    # check post body
    body_data = request.json
    if body_data.get('username',None) is None or body_data.get('password',None) is None:
        ret['reson'] = "Missing parameter"
        return jsonify(ret)

    # username check
    if len(body_data['username']) > 32 or len(body_data['username']) < 3:
        ret['reson'] = 'Username length not accepted'
        return jsonify(ret)

    # password check
    if len(body_data['password']) > 32 or len(body_data['password']) < 8:
        ret['reson'] = 'Password length not accepted'
        return jsonify(ret)
    
    # Check if the password matches the pattern
    # at least 1 uppercase letter, 1 lowercase letter, and 1 number
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$'
    if not re.match(pattern, body_data['password']):
        ret['reson'] = 'Wrong password pattern'
        return jsonify(ret)
    
    # check user name is used
    res = db.session.execute(db.select(User).where(User.name==body_data['username'])).one_or_none()
    if res is not None:
        ret['reson'] = 'Username already exists'
        return jsonify(ret)

    # insert db and hash password
    user = User(
        name=body_data["username"],
        password= hashlib.sha512((body_data["password"]+PASSWORD_SALT).encode('utf-8')).hexdigest() ,
    )
    db.session.add(user)
    db.session.commit()
    ret['success'] = True
    ret['reson'] = 'Create User Success'
    return jsonify(ret)


@app.route("/verify",methods=["POST"])
def verify():

    ret = dict()
    ret['success'] = False

    # check mimetype
    if not request.is_json:
        ret['reson'] =  "Wrong mimetype"
        return jsonify(ret)

    # check post body
    body_data = request.json
    if body_data.get('username',None) is None or body_data.get('password',None) is None:
        ret['reson'] = "Missing parameter"
        return jsonify(ret)

    # username
    name=request.json["username"]
    
    # password most add salt and hash by frontend
    password=request.json["password"]

    # Check if the user's session exists or initialize it
    user_session = session.get(name, {'attempts': 0, 'last_attempt_time': 0})

    # Calculate the time since the last attempt
    time_since_last_attempt = time.time() - user_session['last_attempt_time']

    # Check if the user needs to wait due to too many failed attempts
    if user_session['attempts'] >= MAX_FAILED_ATTEMPTS and time_since_last_attempt < WAIT_TIME_SECONDS:
        time_left = WAIT_TIME_SECONDS - int(time_since_last_attempt)
        ret['reson'] = f'Too many failed attempts. Please try again in {time_left} seconds.'
        return jsonify(ret),429

    res = db.session.execute(db.select(User).where(and_(User.name==name,User.password==password))).one_or_none()
    # password verification success
    if res is not None:
        ret['success'] = True
        ret['reson'] = 'Verify Success'

        user_session['attempts'] = 0
        user_session['last_attempt_time'] = 0
        session[name] = user_session
        
        return jsonify(ret)
    
    #  password verification fail
    else:
        ret['success'] = False
        ret['reson'] = 'Verify Fail'

        user_session['attempts'] += 1
        user_session['last_attempt_time'] = time.time()
        session[name] = user_session

        return jsonify(ret),401

@app.route('/flask-health-check')
def flask_health_check():
	return "success"




@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    ret = dict()
    ret['success'] = False
    ret['reson'] = 'Oops! something wrong'
    return jsonify(ret),e.code


@app.errorhandler(Exception)
def handle_exception_all(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    ret = dict()
    ret['success'] = False
    ret['reson'] = f'Server error{e}'
    # now you're handling non-HTTP exceptions only
    return jsonify(ret), 500