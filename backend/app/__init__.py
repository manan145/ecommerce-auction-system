import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler


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
    from .routes.public_routes import public_bp
    # from .routes.bid_routes import bid_bp
    # from .routes.auction_routes import auction_bp
    from .routes.buyer_routes import buyer_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(rep_bp, url_prefix='/rep')
    app.register_blueprint(seller_bp, url_prefix='/seller')
    app.register_blueprint(public_bp, url_prefix='/public')
    # app.register_blueprint(bid_bp, url_prefix='/bid')
    # app.register_blueprint(auction_bp, url_prefix='/auction')
    app.register_blueprint(buyer_bp, url_prefix='/buyer')

    # ==============================
    # Initialize APScheduler
    # ==============================
    from .utils.close_auctions_utils import close_expired_auctions
    print("Scheduler started")
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: close_expired_auctions(app), trigger="interval", seconds=3600)
    scheduler.start()

    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        try:
            if scheduler.running:
                print("Scheduler is running — skipping shutdown from teardown to avoid thread conflict.")
                return
            scheduler.shutdown()
        except Exception as e:
            print(f"[Scheduler Shutdown Skipped] {e}")

    return app
