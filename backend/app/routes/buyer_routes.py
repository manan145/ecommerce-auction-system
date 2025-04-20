from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from ..models import db, Auction, Bid, User, Item
from ..models import db, User, Transaction, Auction, Item, Alert
from sqlalchemy.orm import joinedload

buyer_bp = Blueprint('buyer', __name__)

@buyer_bp.route('/bid', methods=['POST'])
@jwt_required()
def place_bid():
    """
    API Endpoint: POST /bid

    This endpoint lets an authenticated buyer place a bid on an auction.
    It enforces the following rules:
      - Only users with role "buyer" can bid.
      - The auction must exist, be open, and its end time has not passed.
      - Buyers cannot bid on their own items.
      - The bid amount must be at least:
          • If no bids exist: the auction's StartPrice.
          • If there is a current highest bid: current highest bid plus the auction's MinIncrement.
      - The provided max_auto_bid must be at least equal to the bid amount.
      - If the buyer is already the highest bidder, further bids are rejected.
      - After inserting the bid, the system automatically checks for competing bids
        and places auto-bids on behalf of competing buyers (up to their secret maximum).
      - Finally, the final highest bid and winning bidder are returned.
      
    Note: SecretMinPrice is not exposed via this route.
    """
    # -------------------------------
    # 1. Authenticate & Validate Role
    # -------------------------------
    current_user_id = get_jwt_identity()
    buyer = User.query.get(current_user_id)
    if not buyer or buyer.Role != 'buyer':
        return jsonify({"error": "Only buyers can place bids"}), 403

    # -------------------------------
    # 2. Parse Request Data
    # -------------------------------
    data = request.get_json()
    auction_id = data.get("auction_id")
    bid_amount = data.get("amount")
    max_auto_bid = data.get("max_auto_bid")

    if not auction_id or bid_amount is None:
        return jsonify({"error": "Auction ID and bid amount are required"}), 400

    # -------------------------------
    # 3. Retrieve Auction & Validate Timing
    # -------------------------------
    auction = Auction.query.get(auction_id)
    end_time = auction.EndTime
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    if not auction or auction.IsClosed:
        return jsonify({"error": "Invalid or closed auction"}), 400
    if datetime.now(timezone.utc) > end_time:
        return jsonify({"error": "Auction has ended"}), 400

    # -------------------------------
    # 4. Prevent Buyers from Bidding on Their Own Item
    # -------------------------------
    # Retrieve associated item via auction's ItemID.
    item = Item.query.get(auction.ItemID)
    if not item:
        return jsonify({"error": "Associated item not found"}), 400
    if buyer.UserID == item.OwnerID:
        return jsonify({"error": "You cannot bid on your own item"}), 403

    # -------------------------------
    # 5. Validate Max Auto Bid Input
    # -------------------------------
    # if float(max_auto_bid) < float(bid_amount):
    #     return jsonify({"error": "Maximum auto bid must not be less than the bid amount"}), 400

    # -------------------------------
    # 6. Determine the Minimum Valid Bid
    # -------------------------------
    current_highest = Bid.query.filter_by(AuctionID=auction_id)\
                               .order_by(Bid.Amount.desc()).first()
    # If a bid already exists, new bid must be at least (current highest + MinIncrement)
    if current_highest:
        # Prevent duplicate bid from same user
        if current_highest.BidderID == buyer.UserID:
            return jsonify({"error": "You are already the highest bidder"}), 400
        min_valid_bid = float(current_highest.Amount) + float(auction.MinIncrement)
    else:
        min_valid_bid = float(auction.StartPrice)

    if float(bid_amount) < min_valid_bid:
        return jsonify({"error": f"Your bid must be at least {min_valid_bid}"}), 400

    # -------------------------------
    # 7. Insert the Buyer’s Bid
    # -------------------------------
    new_bid = Bid(
        AuctionID=auction_id,
        BidderID=buyer.UserID,
        Amount=bid_amount,
        MaxAutoBid=float(max_auto_bid) if max_auto_bid else None,  # Set to None if not provided
        BidTime=datetime.now(timezone.utc)
    )
    db.session.add(new_bid)
    db.session.flush()  # Flush so we can use new_bid in auto-bid logic

    # Initialize highest bid to the new bid.
    highest_bid = new_bid

    # -------------------------------
    # 8. Automatic Bidding Logic Loop
    # -------------------------------
    # This loop attempts to trigger auto-bids from competing buyers.
    while max_auto_bid and True:  # Only enter loop if max_auto_bid is set
        # Find the top competing bid from a different bidder whose max_auto_bid is high enough
        competitor = Bid.query.filter(
            Bid.AuctionID == auction_id,
            Bid.BidderID != highest_bid.BidderID,
            Bid.MaxAutoBid > (float(highest_bid.Amount) + float(auction.MinIncrement))
        ).order_by(Bid.MaxAutoBid.desc(), Bid.BidTime.asc()).first()

        # If no competitor qualifies, break the loop.
        if not competitor:
            break

        # Calculate the next bid amount: current highest + minimum increment.
        next_bid_amount = float(highest_bid.Amount) + float(auction.MinIncrement)

        # Automatically place the bid for the competitor.
        auto_bid = Bid(
            AuctionID=auction_id,
            BidderID=competitor.BidderID,
            Amount=next_bid_amount,
            MaxAutoBid=competitor.MaxAutoBid,
            BidTime=datetime.now(timezone.utc)
        )
        db.session.add(auto_bid)
        db.session.flush()

        # Update the highest bid to the auto bid.
        highest_bid = auto_bid

    # Commit all changes atomically.
    db.session.commit()

    # -------------------------------
    # 9. Return Final Bid Status
    # -------------------------------
    return jsonify({
        "message": "Bid placed successfully",
        "auction_id": auction_id,
        "final_highest_bid": float(highest_bid.Amount),
        "winning_bidder": highest_bid.BidderID
    }), 201

# ================================================
# API → Buyer completes payment for a transaction
# ================================================
@buyer_bp.route('/make-payment', methods=['POST'])
@jwt_required()
def make_payment():
    """
    Endpoint: POST /auction/make-payment

    Description:
    Buyer triggers this endpoint to complete payment for a won auction.
    On success:
    - Transaction is marked 'completed'
    - Item ownership is transferred to buyer
    - Item status is set to 'sold'

    Request JSON:
    {
        "transaction_id": 123
    }

    Returns:
        200 OK with transaction details if successful.
        4xx on validation or permission errors.
    """

    current_user_id = get_jwt_identity()
    buyer = User.query.get(current_user_id)
    
    if not buyer or buyer.Role != 'buyer':
        return jsonify({"error": "Only buyers can make payments"}), 403

    data = request.get_json()
    transaction_id = data.get("transaction_id")

    if not transaction_id:
        return jsonify({"error": "Transaction ID is required"}), 400

    # Fetch transaction
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    if transaction.Status != "pending":
        return jsonify({"error": f"Transaction is already '{transaction.Status}'"}), 400

    if transaction.BuyerID != buyer.UserID:
        return jsonify({"error": "You are not authorized to complete this transaction"}), 403

    # Fetch related auction & item
    auction = Auction.query.get(transaction.AuctionID)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    item = Item.query.get(auction.ItemID)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        # Update transaction
        transaction.Status = "completed"
        transaction.TransactionDate = datetime.now(timezone.utc)

        # Transfer item ownership
        item.OwnerID = buyer.UserID
        item.Status = "sold"

        db.session.commit()

        return jsonify({
            "message": "Payment successful. Item ownership transferred.",
            "transaction_id": transaction.TransactionID,
            "item_id": item.ItemID,
            "final_price": float(transaction.Price),
            "buyer_id": buyer.UserID
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to complete payment: {str(e)}"}), 500
    
# ================================================
# API → Buyer creates an alert for items        
# ================================================
@buyer_bp.route('/create-alert', methods=['POST'])
@jwt_required()
def create_alert():
    """
    Endpoint: POST /create-alert

    Description:
    Buyers create alerts for specific item preferences. When a matching item is added to the system,
    the buyer is notified via a structured notification message. This feature helps buyers track
    hard-to-find or highly specific items like older models, limited editions, or items with specific attributes.

    Request JSON:
    {
        "subcategory": "Smartphones",
        "search_criteria": {
            "Brand": ["Apple"],
            "Model": ["iPhone 13"],
            "Condition": ["New"],
            "attributes": {
                "Storage": ["128GB", "256GB"],
                "Color": ["Black"]
            }
        }
    }

    Returns:
        201 Created with alert ID if the alert was successfully saved.
        4xx error if missing fields or validation fails.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'buyer':
        return jsonify({"error": "Only buyers can create alerts"}), 403

    data = request.get_json()
    subcategory = data.get('subcategory')
    search_criteria = data.get('search_criteria')

    if not subcategory or not search_criteria:
        return jsonify({"error": "Subcategory and search_criteria are required"}), 400

    alert = Alert(
        UserID=user.UserID,
        Subcategory=subcategory,
        SearchCriteria=search_criteria
    )
    db.session.add(alert)
    db.session.commit()

    return jsonify({"message": "Alert created successfully", "alert_id": alert.AlertID}), 201

# ================================================
# API → Buyer views all alerts they have created
# ================================================
@buyer_bp.route('/my-alerts', methods=['GET'])
@jwt_required()
def view_alerts():
    """
    Endpoint: GET /my-alerts

    Description:
    Retrieves all alerts created by the currently logged-in buyer.
    This allows the user to review their saved alert preferences,
    such as subcategory, brand, condition, and attribute filters.

    Returns:
        200 OK with a list of all alert objects belonging to the buyer.
        Each object includes alert ID, subcategory name, criteria, and created date.
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.Role != 'buyer':
        return jsonify({"error": "Only buyers can view alerts"}), 403

    alerts = Alert.query.filter_by(UserID=user.UserID).all()
    result = [{
        "alert_id": alert.AlertID,
        "subcategory": alert.Subcategory,
        "search_criteria": alert.SearchCriteria,
        "created_at": alert.CreatedAt
    } for alert in alerts]

    return jsonify(result), 200

# ================================================
# API → Buyer views their bid history       
# ================================================
@buyer_bp.route('/my-bids', methods=['GET'])
@jwt_required()
def get_my_bids():
    from datetime import timezone
    from collections import defaultdict

    user_id = int(get_jwt_identity())  # ensure integer for comparison
    now = datetime.now(timezone.utc)

    # Fetch and group all bids by this user
    user_bids = Bid.query.filter_by(BidderID=user_id).order_by(Bid.BidTime.desc(), Bid.Amount.desc()).all()
    bids_by_auction = defaultdict(list)
    for bid in user_bids:
        bids_by_auction[bid.AuctionID].append(bid)

    result = []

    for auction_id, user_bids_for_auction in bids_by_auction.items():
        auction = Auction.query.get(auction_id)
        if not auction:
            continue

        item = Item.query.get(auction.ItemID)
        if not item:
            continue

        end_time = auction.EndTime
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        is_closed = auction.IsClosed or end_time <= now
        status = "closed" if is_closed else "active"

        transaction = Transaction.query.filter_by(AuctionID=auction_id).first()
        is_winner = (
            transaction is not None and
            transaction.BuyerID == user_id and
            is_closed
        )
        transaction_id = transaction.TransactionID if transaction else None
        transaction_status = transaction.Status if transaction else None
        has_paid = transaction_status == "completed" if transaction_status else False

        # Find the actual highest bid for the auction
        highest_bid = (
            Bid.query
            .filter_by(AuctionID=auction_id)
            .order_by(Bid.Amount.desc(), Bid.BidTime.asc())
            .first()
        )
        highest_bid_id = highest_bid.BidID if highest_bid else None

        # Mark only the user's highest bid (among all auction bids) as highest bidder
        for bid in user_bids_for_auction:
            result.append({
                "amount": float(bid.Amount),
                "bid_time": bid.BidTime.isoformat(),
                "item_title": item.Title,
                "status": status,
                "is_closed": is_closed,
                "auction_id": auction_id,
                "transaction_id": transaction_id,
                "transaction_status": transaction_status,
                "has_paid": has_paid,
                "is_winner": is_winner,
                "won": is_winner,
                "is_highest_bidder": (bid.BidID == highest_bid_id and highest_bid.BidderID == user_id and not is_closed)
            })

    print("DEBUG: Final My Bids Result:")
    for entry in result:
        print(entry)

    return jsonify(result), 200


# ================================================
# API → Buyer views bid history for a specific auction
# ================================================
@buyer_bp.route('/bid-history/<int:auction_id>', methods=['GET'])
@jwt_required()
def bid_history(auction_id):
    current_user_id = get_jwt_identity()
    print("JWT identity:", current_user_id)
    # Join with User table to get bidder names
    bids = (
        db.session.query(Bid, User.Username)
        .join(User, Bid.BidderID == User.UserID)
        .filter(Bid.AuctionID == auction_id)
        .order_by(Bid.BidTime.desc(), Bid.Amount.desc())
        .all()
    )

    return jsonify([
        {
            "bidder_name": username,
            "amount": float(bid.Amount),
            "timestamp": bid.BidTime.isoformat()
        } for bid, username in bids
    ])
