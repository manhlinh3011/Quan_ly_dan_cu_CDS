from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def get_db():
    """Create database connection without circular imports"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    return db, app