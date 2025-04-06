from ..models import Item, Attribute, ItemAttributeValue
from sqlalchemy import or_, and_
from datetime import datetime

def filter_items(filters, only_my_items=False, user_id=None, sort_by='created_desc', offset=0, limit=20):
    query = Item.query

    # Restrict to current user's items if requested
    if only_my_items and user_id:
        query = query.filter(Item.OwnerID == user_id)

    # Valid fields from Item model that can be filtered
    ALLOWED_ITEM_FIELDS = ['Brand', 'Condition', 'SubcategoryID', 'Status']

    # --- Filter by item fields ---
    if filters:
        for field_name, values in filters.items():
            if field_name in ['attributes', 'CreatedAtFrom', 'CreatedAtTo']:
                continue  # handle separately

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
            pass  # You can log or raise error if needed

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
            query = query.filter(Item.CreatedAt <= date_to)
        except ValueError:
            pass

    # --- Filter by attributes ---
    attr_filters = filters.get("attributes", {})
    for attr_name, attr_values in attr_filters.items():
        query = query.join(ItemAttributeValue, Item.ItemID == ItemAttributeValue.ItemID)\
                     .join(Attribute, Attribute.AttributeID == ItemAttributeValue.AttributeID)\
                     .filter(
                         Attribute.Name == attr_name,
                         ItemAttributeValue.Value.in_(attr_values)
                     )

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

    # --- Build Response ---
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
