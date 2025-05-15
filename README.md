# FastAPI Application

A modern FastAPI application with SQLModel and PostgreSQL.

## Technologies Used

- ⚡ FastAPI for the Python backend API
- 🧰 SQLModel for SQL database interactions (ORM)
- 🔍 Pydantic for data validation and settings management
- 💾 PostgreSQL as the SQL database
- 📦 UV package manager
- 🐳 Docker and Docker Compose
- 🔄 GitLab CI for continuous integration

## Features

- RESTful API with FastAPI
- PostgreSQL database with SQLModel ORM
- Authentication with JWT tokens
- User management (CRUD operations)
- Docker support
- GitLab CI/CD configuration
- Comprehensive test suite
- Database migrations with Alembic

## Getting Started

1. Clone the repository
2. Copy `.env.example` to `.env` and update the values
3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the API documentation at `http://localhost:8000/docs`

## Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Testing

Run tests with pytest:
```bash
pytest
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Project Structure

```
blog-api/
├── alembic/                    # Database migration tool
├── app/                        # Application package
│   ├── api/                    # API routes
│   ├── config/                 # Configuration
│   ├── core/                   # Core functionality
│   ├── models/                 # SQLModel models
│   ├── schemas/                # Pydantic schemas
│   ├── services/              # Business logic
│   └── repositories/          # Database access
├── tests/                      # Test files
└── [Configuration files]
```

## API Documentation

Once the application is running, you can access:
- Swagger UI documentation at: `http://localhost:8000/docs`
- ReDoc documentation at: `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

Chạy độc lập: Bạn có thể chạy database độc lập và để nó hoạt động liên tục, trong khi backend có thể được build, start, restart nhiều lần mà không ảnh hưởng đến database
Dòng lệnh
Chạy chỉ database:

   docker-compose -f docker-compose.db.yml up -d
Chạy backend (kết nối đến DB đã chạy):

   docker-compose up -d
Chạy tất cả từ file chính:

docker-compose --profile all up -d
