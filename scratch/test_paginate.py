from app import app
import models

with app.app_context():
    try:
        # Test default Query.paginate
        pag = models.User.query.paginate(page=1, per_page=10, error_out=False)
        print("Paginate attributes:")
        print(f"has_prev: {pag.has_prev}")
        print(f"has_next: {pag.has_next}")
        print(f"prev_num: {pag.prev_num}")
        print(f"next_num: {pag.next_num}")
        print(f"page: {pag.page}")
        print(f"pages: {pag.pages}")
        print(f"items count: {len(pag.items)}")
        print("SQLAlchemy pagination is working perfectly!")
    except Exception as e:
        print(f"Error testing pagination: {e}")
