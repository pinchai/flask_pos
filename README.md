# flask_pos

## Installation

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Copy the example environment file:

```bash
cp .env.example .env
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply database migrations:

```bash
flask --app app db upgrade
```

5. Seed sample data:

```bash
flask --app app seed-db
```

6. Run the app:

```bash
flask --app app run
```

Open the dashboard at `http://127.0.0.1:5000` and the API docs at `http://127.0.0.1:5000/api/docs`.

## API Documentation

The REST API is mounted under `/api` and includes interactive Swagger documentation.

- Swagger UI: `http://127.0.0.1:5000/api/docs`
- OpenAPI JSON: `http://127.0.0.1:5000/api/swagger.json`

### Authentication

Most API endpoints require a JWT access token.

1. Log in with an approved user:

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "1234556789"}'
```

2. Copy the returned `access_token`.

3. Send the token in protected requests:

```bash
Authorization: Bearer <access_token>
```

In Swagger UI, click `Authorize` and enter the token using the same format:

```text
Bearer <access_token>
```

### Main API Groups

- `POST /api/auth/login` authenticates an approved user and returns a JWT.
- `POST /api/auth/register` creates a pending student user.
- `/api/shops/` lists and creates shops for the logged-in user.
- `/api/shops/detail` gets, updates, or deletes one shop by `shop_id`.
- `/api/categories/` lists and creates categories for the logged-in user.
- `/api/categories/detail` gets, updates, or deletes one category by `category_id`.
- `/api/products/` lists and creates products for the logged-in user.
- `/api/products/detail` gets, updates, or deletes one product by `product_id`.
- `/api/payment-methods/` lists and creates payment methods for the logged-in user.
- `/api/payment-methods/detail` gets, updates, or deletes one payment method by `pm_id`.
- `/api/sales/` lists sales or creates a new sale transaction.
- `/api/sales/detail` returns invoice-style details for one sale by `sale_id`.

### Notes

API data is scoped to the authenticated user. A user can only access shops, categories, products, payment methods, and sales that belong to their own account.
