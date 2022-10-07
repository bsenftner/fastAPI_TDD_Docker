# FastAPI_TDD_Docker : Notes and BlogPosts
## Simple CRUD APIs for "notes" and "blog posts" with tests & CI/CD via Docker

1. You'll need Docker
2. Within the project's root:
```
docker compose up -d --build
```
3. visit `http://localhost:8002/docs` to use the OpenAPI GUI
4. Run tests from project root with `docker compose exec web pytest .`


When you're done:
1. docker compose down -v
