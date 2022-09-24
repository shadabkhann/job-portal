from ast import Str
from cProfile import Profile
from collections import UserList
from csv import Dialect
from dataclasses import fields
from flask_migrate import Migrate
import dataclasses
from enum import unique
from signal import Signals
import sqlite3
from turtle import Turtle
from flask import Flask,request,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename
import jwt
import datetime
from functools import wraps
from blinker import Namespace
from sqlalchemy.dialects import sqlite




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///job.db"
app.config['SECRET_KEY'] = 'a097d311e4d0e47e00d7d254c00b7265'
db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db)
namespace = Namespace()
message_sent = namespace.signal('mail_sent')
 


# class Gender(enum.Enum):
#     female = 0
#     male = 1   
#     other = 2

class Register(db.Model):
    # __tablename__ == 'register'
    # id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String, nullable=False)
    l_name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String, nullable=False)
    # gender = db.Column(db.Enum(Gender), nullable=False)
    password = db.Column(db.String(300))
    admin = db.Column(db.Boolean)
    profile = db.relationship('profile', backref='Register', uselist=False)

    def __repr__(self):
        return self.f_name

class profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String, nullable=False)
    l_name = db.Column(db.String, nullable=False)
    Register_id = db.Column(db.Integer, db.ForeignKey(Register.user_id))

@message_sent.connect
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         profile.objects.create(Register=instance)
#         print("profile update")
def create_profile(sender, post, *kwargs):
    user = Register()
    user.post  = post
    user.save()

def post_detail(slug, is_preview=False):
    post = profile.objects.get_or_404(slug=slug, post_type=post)
    # print (str(post.statement.compile(dialect=sqlite.dialect())))
    # Register['post'] = post

    # do something.# send signal
    # if not is_preview:
    #     Signals.post_visited.send(current_app._get_current_object(), post=post)


 

   

class Education(db.Model):
    education_id = db.Column(db.Integer, primary_key=True)
    education = db.Column(db.String, nullable=False)
    board = db.Column(db.String, nullable=False)
    passing_out_year = db.Column(db.Integer, nullable=False)
    school_medium = db.Column(db.String, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return self.education

class Experience(db.Model):
    experience_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String, nullable=False)
    joining_date = db.Column(db.Integer, nullable=False)
    currently_work = db.Column(db.String, nullable=False)
    total_experence = db.Column(db.String, nullable=False)
    notice_period = db.Column(db.String, nullable=False)
    current_CTC = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.company_name


class Project(db.Model):
    project_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String, nullable=False)
    project_desc = db.Column(db.String, nullable=False)
    start_date = db.Column(db.Integer, nullable=False)
    end_date = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.project_name










class UserSchema(ma.Schema):
    class Meta:
        fields = ("user_id","f_name","l_name","age","phone","email","admin")
user_schema = UserSchema()
users_schema = UserSchema(many=True)


# token_requirment
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = Register.query.filter_by(user_id=data['user_id']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user,*args, **kwargs)

    return decorated
@app.route('/user',methods=['GET'])
# @token_required
def get_all_users():
    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    users=Register.query.all()
    result=users_schema.dump(users)
    return jsonify(result)
  

@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    if data:
        hashed_password = generate_password_hash(data['password'])     
        new_user = Register(user_id=data['user_id'], f_name=data['f_name'], l_name=data['l_name'], age=data['age'], phone=data['phone'], email=data['email'], password=hashed_password, admin=False)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg':'register completed'})
    else:
        return jsonify({'msg':'Register Failed!'})

@app.route('/login')
def login():
    auth=request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user=Register.query.filter_by(f_name=auth.username).first()

    if not user:
        return make_response('Incorrect username',404,{'WWW-Authenticate' : 'Basic realm="username required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'user_id' : user.user_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'])
        return jsonify({'token':'User login seccessfully'})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})


@app.route('/education', methods=['POST'])

def education():
    data = request.get_json()
    user = Education(education=data['education'], board=data['board'], passing_out_year=data['passing_out_year'], school_medium=data['school_medium'], total_marks=data['total_marks'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg':'Education filled successfully'})

@app.route('/experience', methods=['POST'])
def experience():
    data = request.get_json()
    exp = Experience(company_name=data['company_name'], joining_date=data['joining_date'], currently_work=data['currently_work'], total_experence=data['total_experence'], notice_period=data['notice_period'], current_CTC=data['current_CTC'])
    db.session.add(exp)
    db.session.commit()
    return jsonify ({'msg':'Experience data entered seccessfully'})


@app.route('/project', methods=['POST'])
def project():
    data = request.get_json()
    proj = Project(project_name=data['project_name'], project_desc=data['project_desc'], start_date=data['start_date'], end_date=data['end_date'])
    db.session.add(proj)
    db.session.commit()
    return jsonify({'msg':'add project details seccessfully'})



if __name__ == "__main__":
    app.run(debug=True)

