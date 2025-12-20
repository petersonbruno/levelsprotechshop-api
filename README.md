# LevelsProShop API

A RESTful Django REST Framework API for LevelsProShop e-commerce application that sells laptops, desktops, gaming PCs, and tech accessories.

## Setup Instructions

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** (optional, for environment variables):
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Health Check
- **GET /api/health/** - Health check endpoint
  - Response: `{ "success": true, "data": { "status": "healthy" }, "message": "API is running successfully" }`

### Authentication

#### POST /api/login/
Login with username and password to get an authentication token.

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 1,
    "username": "your_username",
    "email": "user@example.com"
  },
  "message": "Login successful"
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Invalid username or password"
}
```

**Note:** Use the returned token in the `Authorization` header for authenticated endpoints:
```
Authorization: Token <your_token_here>
```

### Dashboard

#### GET /api/dashboard/
Get all products created by the authenticated user (Product Creator Dashboard).

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Query Parameters:**
- `category` (optional): Filter by category - "Laptops", "Desktops", "Gaming PCs", "Accessories"
- `search` (optional): Search products by name (case-insensitive)
- `limit` (optional): Number of results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Sort by - "name", "-name", "price", "-price", "date", "-date"

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [...],
    "count": 15,
    "limit": 20,
    "offset": 0,
    "total_pages": 1,
    "creator": {
      "id": 1,
      "username": "your_username",
      "email": "user@example.com"
    }
  },
  "message": "Dashboard data retrieved successfully"
}
```

### Products CRUD Operations

#### 1. GET /api/products/
Get all products with filtering, search, pagination, and sorting.

**Query Parameters:**
- `category` (optional): Filter by category - "Laptops", "Desktops", "Gaming PCs", "Accessories"
- `search` (optional): Search products by name (case-insensitive)
- `limit` (optional): Number of results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort` (optional): Sort by - "name", "-name", "price", "-price", "date", "-date"

**Example:**
```bash
GET /api/products/?category=Laptops&search=MacBook&limit=10&offset=0&sort=-date
```

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [...],
    "count": 50,
    "limit": 10,
    "offset": 0,
    "total_pages": 5
  },
  "message": "Products retrieved successfully"
}
```

#### 2. GET /api/products/{id}/
Get a single product by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "MacBook Pro",
    "category": "Laptops",
    "price": "950,000 TZS",
    "specs": ["16GB RAM", "512GB SSD"],
    "warranty": "3 Months",
    "image_urls": ["http://localhost:8000/media/products/image1.png"],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "message": "Product retrieved successfully"
}
```

#### 3. POST /api/products/
Create a new product.

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Note:** The product creator is automatically set to the authenticated user.

**Request Body (JSON):**
```json
{
  "name": "MacBook Pro",
  "category": "Laptops",
  "price": "950,000 TZS",
  "specs": ["16GB RAM", "512GB SSD", "M2 Chip"],
  "warranty": "3 Months",
  "images_data": ["base64_image_string_1", "base64_image_string_2"]
}
```

**Request Body (multipart/form-data):**
- `name`: string (required)
- `category`: string (required)
- `price`: string (required)
- `specs`: JSON array (required)
- `warranty`: string (optional, default: "3 Months")
- `images`: file[] (required, max 10 images, 5MB each)

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Product created successfully"
}
```

#### 4. PUT /api/products/{id}/
Update an existing product (full update).

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Request Body:** Same as POST

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Product updated successfully"
}
```

#### 5. PATCH /api/products/{id}/
Partially update an existing product.

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Request Body:** Any subset of product fields

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Product updated successfully"
}
```

#### 6. DELETE /api/products/{id}/
Delete a product by ID.

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Response:**
```json
{
  "success": true,
  "data": null,
  "message": "Product deleted successfully"
}
```

#### 7. DELETE /api/products/{id}/images/{image_id}/
Delete a specific product image.

**Authentication:** Required (Token Authentication)

**Headers:**
```
Authorization: Token <your_token_here>
```

**Response:**
```json
{
  "success": true,
  "message": "Image deleted successfully"
}
```

## Product Data Model

```json
{
  "id": "uuid (auto-generated)",
  "name": "string (required, 3-200 characters)",
  "category": "string (required) - one of: 'Laptops', 'Desktops', 'Gaming PCs', 'Accessories'",
  "price": "string (required) - format: '950,000 TZS'",
  "specs": ["array of strings (each max 500 characters)"],
  "warranty": "string (optional, default: '3 Months')",
  "images": ["array of image objects"],
  "image_urls": ["array of image URLs"],
  "creator": "user_id (auto-set on creation, read-only)",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## Validation Rules

- **Product name**: Required, 3-200 characters
- **Category**: Required, must be one of: "Laptops", "Desktops", "Gaming PCs", "Accessories"
- **Price**: Required, format: "950,000 TZS" (numbers with commas + " TZS")
- **Specs**: Array of strings, each spec max 500 characters
- **Images**: At least 1 image required, max 10 images per product
- **Image file size**: Max 5MB per image
- **Image file types**: jpg, jpeg, png, gif, webp
- **Warranty**: Optional, default "3 Months"

## Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "details": "Additional error details (optional)"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required or invalid credentials)
- `404` - Not Found
- `500` - Internal Server Error

## Image Handling

The API supports two methods for image upload:

1. **Base64 strings** (via JSON):
   - Include `images_data` array in JSON request body
   - Each element is a base64-encoded image string

2. **File upload** (via multipart/form-data):
   - Use `images` field with file input
   - Supports multiple files (max 10)
   - Each file max 5MB

Images are stored in the `media/products/` directory and URLs are returned in responses.

## Example API Usage

### Login
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### Get Dashboard (View Your Products)
```bash
curl -X GET "http://localhost:8000/api/dashboard/?category=Laptops&sort=-date" \
  -H "Authorization: Token <your_token_here>"
```

### Create Product with Base64 Images (Authenticated)
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your_token_here>" \
  -d '{
    "name": "MacBook Pro 16",
    "category": "Laptops",
    "price": "2,500,000 TZS",
    "specs": ["16GB RAM", "512GB SSD", "M2 Pro Chip", "16-inch Display"],
    "warranty": "1 Year",
    "images_data": ["base64_string_1", "base64_string_2"]
  }'
```

### Create Product with File Upload (Authenticated)
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Token <your_token_here>" \
  -F "name=MacBook Pro 16" \
  -F "category=Laptops" \
  -F "price=2,500,000 TZS" \
  -F "specs=[\"16GB RAM\", \"512GB SSD\"]" \
  -F "warranty=1 Year" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg"
```

### Get Products with Filters (Public - No Authentication Required)
```bash
curl "http://localhost:8000/api/products/?category=Laptops&search=MacBook&limit=10&sort=-date"
```

## Project Structure

```
levelsproshop_api/
├── api/                 # API app
│   ├── models.py        # Database models (Product, ProductImage)
│   ├── serializers.py   # DRF serializers with validation
│   ├── views.py         # API views with CRUD operations
│   ├── urls.py          # API URL routing
│   ├── admin.py         # Admin configuration
│   └── utils.py         # Utility functions (validation, responses)
├── config/              # Django project settings
│   ├── settings.py      # Project settings
│   ├── urls.py          # Main URL configuration
│   ├── wsgi.py          # WSGI configuration
│   └── asgi.py          # ASGI configuration
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore file
└── README.md           # This file
```

## Technologies Used

- **Django 4.2.7** - Web framework
- **Django REST Framework 3.14.0** - REST API framework
- **django-cors-headers 4.3.1** - CORS support
- **python-decouple 3.8** - Environment variable management
- **Pillow 10.1.0** - Image processing
- **django-filter 23.5** - Advanced filtering

## Database Schema

The API uses SQLite by default (can be changed to PostgreSQL/MySQL in settings.py).

**Products Table:**
- `id` (UUID, Primary Key)
- `name` (CharField, indexed)
- `category` (CharField, indexed)
- `price` (CharField)
- `specs` (JSONField)
- `warranty` (CharField)
- `creator` (ForeignKey to User, indexed, nullable)
- `created_at` (DateTimeField, indexed)
- `updated_at` (DateTimeField)

**ProductImages Table:**
- `id` (AutoField, Primary Key)
- `product` (ForeignKey to Product)
- `image` (ImageField)
- `created_at` (DateTimeField)

## Admin Panel

Access the admin panel at `http://localhost:8000/admin/` to manage products and images through the Django admin interface.

## Authentication

The API uses **Token Authentication** for protected endpoints. 

**Public Endpoints (No Authentication Required):**
- `GET /api/health/` - Health check
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get single product

**Protected Endpoints (Authentication Required):**
- `POST /api/login/` - Login (no auth required, but returns token)
- `GET /api/dashboard/` - View your products
- `POST /api/products/` - Create product
- `PUT /api/products/{id}/` - Update product
- `PATCH /api/products/{id}/` - Partially update product
- `DELETE /api/products/{id}/` - Delete product
- `DELETE /api/products/{id}/images/{image_id}/` - Delete product image

**How to Authenticate:**
1. Login using `POST /api/login/` with username and password
2. Receive a token in the response
3. Include the token in the `Authorization` header for protected endpoints:
   ```
   Authorization: Token <your_token_here>
   ```

**Product Creator:**
- When creating a product, the `creator` field is automatically set to the authenticated user
- The dashboard endpoint shows only products created by the logged-in user
- Each product tracks who created it

## Notes

- The API uses UUID for product IDs instead of auto-increment integers
- Images are stored locally in development (can be configured for cloud storage)
- All responses follow a standardized format with `success`, `data`, and `message` fields
- CORS is enabled for frontend integration
- The API supports both JSON and multipart/form-data content types
- Token authentication is used for user authentication
- Product creators can only view their own products through the dashboard endpoint


# levelsprotechshop-api
