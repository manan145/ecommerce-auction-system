from ..models import Item, Attribute, ItemAttributeValue, Auction
from sqlalchemy.orm import aliased
from datetime import datetime

def filter_items(filters, only_my_items=False, user_id=None, sort_by='created_desc', offset=0, limit=20, **kwargs):
    query = Item.query

    # Restrict to current user's items if requested
    if only_my_items and user_id:
        query = query.filter(Item.OwnerID == user_id)

    # Allowed direct Item fields for filtering
    ALLOWED_ITEM_FIELDS = ['Brand', 'Condition', 'SubcategoryID', 'Status']

    # --- Filter by item fields ---
    if filters:
        for field_name, values in filters.items():
            if field_name in ['attributes', 'CreatedAtFrom', 'CreatedAtTo']:
                continue  # handled separately

            if isinstance(values, list) and field_name in ALLOWED_ITEM_FIELDS:
                column = getattr(Item, field_name)
                query = query.filter(column.in_(values))

    # --- Filter by CreatedAt date range ---
    date_from_str = filters.get("CreatedAtFrom")
    date_to_str = filters.get("CreatedAtTo")

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
            query = query.filter(Item.CreatedAt >= date_from)
        except ValueError:
            pass

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            query = query.filter(Item.CreatedAt <= date_to)
        except ValueError:
            pass

    # --- Filter by attributes using aliased joins ---
    attr_filters = filters.get("attributes", {})
    for i, (attr_name, attr_values) in enumerate(attr_filters.items()):
        if not attr_values:
            continue

        iav_alias = aliased(ItemAttributeValue, name=f'iav_{i}')
        attr_alias = aliased(Attribute, name=f'attr_{i}')

        query = query.join(iav_alias, iav_alias.ItemID == Item.ItemID)
        query = query.join(attr_alias, attr_alias.AttributeID == iav_alias.AttributeID)
        query = query.filter(attr_alias.Name == attr_name, iav_alias.Value.in_(attr_values))

    # --- Filter by auction fields ---
    auction_filters = kwargs.get('auction_filters', {})
    min_price = auction_filters.get('min_price')
    max_price = auction_filters.get('max_price')
    is_closed = auction_filters.get('is_closed')

    if min_price is not None or max_price is not None or is_closed is not None:
        query = query.join(Auction, Auction.ItemID == Item.ItemID)

        if min_price is not None:
            query = query.filter(Auction.StartPrice >= min_price)

        if max_price is not None:
            query = query.filter(Auction.StartPrice <= max_price)

        if is_closed is not None:
            query = query.filter(Auction.IsClosed == is_closed)

    # --- Sorting ---
    if sort_by == 'title_asc':
        query = query.order_by(Item.Title.asc())
    elif sort_by == 'title_desc':
        query = query.order_by(Item.Title.desc())
    else:
        query = query.order_by(Item.CreatedAt.desc())

    # --- Pagination ---
    query = query.offset(offset).limit(limit)
    items = query.all()

    # --- Build response with attributes ---
    results = []
    for item in items:
        attributes = ItemAttributeValue.query.filter_by(ItemID=item.ItemID).all()
        attr_list = [{
            "attribute_id": attr.AttributeID,
            "name": Attribute.query.get(attr.AttributeID).Name,
            "value": attr.Value
        } for attr in attributes]

        results.append({
            "ItemID": item.ItemID,
            "Title": item.Title,
            "Description": item.Description,
            "Brand": item.Brand,
            "Model": item.Model,
            "Condition": item.Condition,
            "SubcategoryID": item.SubcategoryID,
            "CreatedAt": item.CreatedAt,
            "OwnerID": item.OwnerID,
            "Attributes": attr_list
        })

    return {
        "count": len(results),
        "results": results
    }
