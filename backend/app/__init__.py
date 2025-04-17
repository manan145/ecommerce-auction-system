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

    with app.app_context():
        db.create_all()  # ← This will create the tables if they don’t already exist

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

from flask import request, jsonify
from ..models import db, Auction, Item, Bid, User
from flask_jwt_extended import jwt_required

@rep_bp.route('/remove-auction/<int:auction_id>', methods=['DELETE'])
@jwt_required()
def remove_auction(auction_id):
    """
    API → Customer rep removes an auction and marks associated item as withdrawn.

    Returns:
        200 OK if auction is deleted
        404 Not Found if auction does not exist
    """
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({'error': 'Auction not found'}), 404

    item = Item.query.get(auction.ItemID)
    if item:
        item.Status = 'withdrawn'

    db.session.delete(auction)
    db.session.commit()

    return jsonify({'message': f'Auction {auction_id} removed and item marked as withdrawn'}), 200

@rep_bp.route('/remove-bid/<int:bid_id>', methods=['DELETE'])
@jwt_required()
def remove_bid(bid_id):
    """
    API → Customer rep removes a specific bid by BidID.

    Returns:
        200 OK if bid is deleted
        404 Not Found if bid does not exist
    """
    bid = Bid.query.get(bid_id)
    if not bid:
        return jsonify({'error': 'Bid not found'}), 404

    db.session.delete(bid)
    db.session.commit()

    return jsonify({'message': f'Bid {bid_id} removed successfully'}), 200
