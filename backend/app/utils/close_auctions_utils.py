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

                        # Notify buyer (winner of the auction to make payment)
                        notification = Notification(
                            UserID=highest_bid.BidderID,
                            Message=json.dumps({
                                "type": "payment_required",
                                "transaction_id": transaction.TransactionID,
                                "item_id": item.ItemID,
                                "item_title": item.Title,
                                "price": float(highest_bid.Amount)
                            }),
                            Status='unread'
                        )
                        db.session.add(notification)

                        # Notify seller (item sold)
                        seller = User.query.get(item.OwnerID)
                        buyer = User.query.get(highest_bid.BidderID)
                        seller_message = json.dumps({
                            "type": "item_sold",
                            "title": "Your Item Was Sold!",
                            "item_id": item.ItemID,
                            "item_title": item.Title,
                            "sold_price": float(highest_bid.Amount),
                            "buyer_id": buyer.UserID,
                            "buyer_name": buyer.Name if hasattr(buyer, "Name") else "",
                            "transaction_id": transaction.TransactionID
                        })
                        seller_notification = Notification(
                            UserID=seller.UserID,
                            Message=seller_message,
                            CreatedAt=now,
                            Status="unread"
                        )
                        db.session.add(seller_notification)
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