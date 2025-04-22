from datetime import datetime, timedelta, timezone
from ..models import db, Auction, Bid, Transaction, Item, Notification, User
import json

def close_expired_auctions(app):
    """
    Scheduled task: Close expired auctions and notify winning buyers or sellers.
    """
    with app.app_context():
        
        print(f"[SCHEDULER] Running job at {datetime.now(timezone.utc)}")

        now = datetime.now(timezone.utc)

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

                        # Update item status to "sold"
                        item = Item.query.get(auction.ItemID)
                        item.Status = "sold"
                        # db.session.add(item)

                        # Notify buyer (winner)
                        buyer = User.query.get(highest_bid.BidderID)
                        item = Item.query.get(auction.ItemID)
                        message = json.dumps({
                            "type": "auction_won",
                            "title": "🎉 Auction Won!",
                            "item_id": item.ItemID,
                            "item_title": item.Title,
                            "bid_amount": float(highest_bid.Amount),
                            "transaction_id": transaction.TransactionID
                        })
                        notification = Notification(
                            UserID=buyer.UserID,
                            Message=message,
                            CreatedAt=now,
                            Status="unread"
                        )
                        db.session.add(notification)
                    else:
                        # Highest bid < secret min price → auction reserve not met
                        auction.IsClosed = True
                        item = Item.query.get(auction.ItemID)
                        seller = User.query.get(item.OwnerID)
                        message = json.dumps({
                            "type": "auction_reserve_not_met",
                            "title": "Auction Reserve Price Not Met",
                            "item_id": item.ItemID,
                            "item_title": item.Title,
                            "highest_bid": float(highest_bid.Amount),
                            "secret_min_price": float(auction.SecretMinPrice)
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
                    item = Item.query.get(auction.ItemID)
                    seller = User.query.get(item.OwnerID)
                    message = json.dumps({
                        "type": "auction_no_bids",
                        "title": "Auction Ended Without Bids",
                        "item_id": item.ItemID,
                        "item_title": item.Title
                    })
                    notification = Notification(
                        UserID=seller.UserID,
                        Message=message,
                        CreatedAt=now,
                        Status="unread"
                    )
                    db.session.add(notification)

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                print(f"Error processing auction {auction.AuctionID}: {str(e)}")