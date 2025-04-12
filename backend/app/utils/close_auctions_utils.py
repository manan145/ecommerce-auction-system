from datetime import datetime, timedelta
from ..models import db, Auction, Bid, Transaction, Item, Notification, User
import json

def close_expired_auctions():
    """
    Scheduled task: Close expired auctions and notify winning buyers or sellers.
    """
    with db.app.app_context():
        now = datetime.utcnow()

        auctions = Auction.query.filter(
            Auction.IsClosed == False,
            Auction.EndTime < now
        ).all()

        for auction in auctions:
            try:
                highest_bid = Bid.query.filter_by(AuctionID=auction.AuctionID)\
                    .order_by(Bid.Amount.desc()).first()

                if highest_bid:
                    # Check if bid meets secret min price
                    if float(highest_bid.Amount) >= float(auction.SecretMinPrice):
                        # Close auction and create transaction
                        auction.IsClosed = True
                        transaction = Transaction(
                            AuctionID=auction.AuctionID,
                            BuyerID=highest_bid.BidderID,
                            Price=highest_bid.Amount,
                            TransactionDate=now,
                            Status="pending"
                        )
                        db.session.add(transaction)
                        db.session.flush()  # Get transaction ID

                        # Notify buyer
                        buyer = User.query.get(highest_bid.BidderID)
                        item = Item.query.get(auction.ItemID)
                        message = json.dumps({
                            "type": "payment_required",
                            "transaction_id": transaction.TransactionID,
                            "item_id": item.ItemID,
                            "price": float(transaction.Price)
                        })
                        notification = Notification(
                            UserID=buyer.UserID,
                            Message=message,
                            CreatedAt=now,
                            Status="unread"
                        )
                        db.session.add(notification)

                    else:
                        # Highest bid < secret min price → notify seller for decision
                        item = Item.query.get(auction.ItemID)
                        seller = User.query.get(item.OwnerID)

                        # Set response deadline (24 hrs from now)
                        response_deadline = (now + timedelta(hours=24)).isoformat()

                        # Structured message for frontend
                        message = json.dumps({
                            "type": "action_required",
                            "action": "post_auction_decision",
                            "auction_id": auction.AuctionID,
                            "item_id": item.ItemID,
                            "highest_bid": float(highest_bid.Amount),
                            "bidder_id": highest_bid.BidderID,
                            "response_deadline": response_deadline
                        })

                        notification = Notification(
                            UserID=seller.UserID,
                            Message=message,
                            CreatedAt=now,
                            Status="unread"
                        )
                        db.session.add(notification)

                else:
                    # No bids, just close the auction
                    auction.IsClosed = True

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                print(f"Error processing auction {auction.AuctionID}: {str(e)}")