# FastAPI_TDD_Docker : Notes and BlogPosts

## Static HTML GUI on top of FastAPI CRUD APIs for "notes" and "blog posts" with tests & CI/CD via Docker

1. You'll need Docker
2. Within the project's root:

    ```text
    docker compose up -d --build
    ```

3. Visit `http://localhost:8002/docs` to use the OpenAPI GUI
4. Run tests from project root with `docker compose exec web pytest .`
5. Visit `http://localhost:8002` to use the static GUI.

This produces two Docker images, one hosting postgres and the other the FastAPI app.
It is pretty basic at this point, quite easy to make your own. The file page_frags.py is the only one
with text branding, and the single photo jpeg used so far is in that file too.

The database itself is saved to the Docker host system. You can choose to take the app down deleting
the database or preserving it.
The pair of containers can be taken down with the db deleted using:

`docker compose down -v`

Or, if you want to preserve the info in the database, just use:

`docker compose down`

Next time you do step 2, above, the previous database info will still be there.

## Notes

* The new registration page can be used at `/register` to create an initial user.

* An initial blog post needs to be created via the OpenAPI GUI to get blog page HTML interfaces.

* This version has JWT Bearer Token Authentication, using both local storage and httpOnly cookies.

* Coming next is email verification, password recovery, and separate user/admin capabilities.
