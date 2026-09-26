from flask_bcrypt import Bcrypt
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['UPLOAD_FOLDER'] = 'SAN/static/uploads'

app.secret_key = 'chave_secreta'
app.permanent_session_lifetime = 3600  # 1 hora

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///san.db'
db = SQLAlchemy()
db.init_app(app)

usuarios = []
atividades = []
materias=[]
turmas=[]
    
from SAN import  rotas

with app.app_context():
    db.create_all()