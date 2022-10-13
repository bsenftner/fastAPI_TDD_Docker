# FastAPI_TDD_Docker : Notes and BlogPosts

## Static HTML GUI on top of FastAPI CRUD APIs for "notes" and "blog posts" with tests & CI/CD via Docker

1. You'll need Docker; this was developed using WSL2-Ubuntu on Win10 with Docker Desktop 4.12.0 (85629)
2. Via terminal navigate to `src\app` and create a file named `.env` in the same directory as main.py
3. Enter `openssl rand -hex 32` to generate a random hex string
4. Edit the `.env` file to have contents like this:

    ```text
    JWT_SECRET=[that-hex-string-generated-in-step-3]
    ```

5. Navigate back the project's root, where the `docker-compose.yml` file is located and enter:

    ```text
    docker compose up -d --build
    ```

6. Via your web browser visit `http://localhost:8002/docs` to use the OpenAPI GUI
7. Run tests from project root with `docker compose exec web pytest .`
8. Visit `http://localhost:8002/register` to create the first user on the static GUI.

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
