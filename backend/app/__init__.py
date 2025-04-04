import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # ==============================
    # Configuration
    # ==============================
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')

    # ==============================
    # Initialize Extensions
    # ==============================
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # ==============================
    # Import Models
    # ==============================
    from . import models

    # ==============================
    # Register Blueprints (Routes)
    # ==============================
    from .routes.auth_routes import auth_bp
    from .routes.admin_routes import admin_bp
    from .routes.customer_rep_routes import rep_bp
    from .routes.seller_routes import seller_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(rep_bp, url_prefix='/rep')
    app.register_blueprint(seller_bp, url_prefix='/seller')

    return app
