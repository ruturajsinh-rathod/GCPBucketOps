# Blogpost App

## To run the project in local

1. Set up Poetry Environment
```bash
poetry install
poetry shell
```

2. Run Database Migrations
```bash
alembic revision --autogenerate -m "Your migration message"
alembic upgrade head
```

3. Start the Application
```bash
python main.py 
```

## To run the project with docker-compose

```bash
docker-compose up --build 
```
