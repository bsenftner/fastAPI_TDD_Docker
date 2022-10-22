# FastAPI_TDD_Docker : Notes and BlogPosts

## Static HTML GUI on top of FastAPI CRUD APIs for "notes" and "blog posts" with tests & CI/CD via Docker

1. You'll need Docker; this was developed using WSL2-Ubuntu on Win10 with Docker Desktop 4.12.0 (85629)
2. Via terminal navigate to `src\app` and create a file named `.env` in the same directory as main.py
3. Enter `openssl rand -hex 32` to generate a random hex string, and again because you'll need two.
4. Edit the `.env` file to have contents like this:

    ```text
    JWT_SECRET_KEY=[that-first-hex-string-generated-in-step-3]
    JWT_SECRET_REFRESH_KEY=[that-second-hex-string-generated-in-step-3]
    ACCESS_TOKEN_EXPIRES_MINUTES=15
    REFRESH_TOKEN_EXPIRES_MINUTES=60
    JWT_ALGORITHM=HS256
    CLIENT_ORIGIN=http://localhost:8002
    MAIL_USERNAME=[email-username-often-same-as-email-address]
    MAIL_PASSWORD=[email-password]
    MAIL_FROM=[email-from-account]
    MAIL_PORT=587
    MAIL_SERVER=[smtp-email-server-addr]
    MAIL_FROM_NAME=[email-from-account-username]
    ```

    Unless you already have a programmatic email address you use and can get the various
    email settings for above, I suggest looking up using GMail and their secure app email password system.

5. Navigate back the project's root, where the `docker-compose.yml` file is located and enter:

    ```text
    docker compose up -d --build
    ```

6. Via your web browser visit `http://localhost:8002/docs` to use the OpenAPI GUI
7. Run tests from project root with `docker compose exec web pytest .`

   * And I realize the tests are failing; that's because I've not accounted for the newly added authentication on endpoints...

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

Next time you do step 5, above, the previous database info will still be there.

## Notes

* Registration, login, email verification, post navigating, logout and logging back in all flow smooth.

* An initial blog post needs to be created via the OpenAPI GUI to get blog page HTML interfaces.

* Uses JWT Bearer Token Authentication, using both local storage and httpOnly cookies.

* New is a user account settings page. This is for changing email, changing password or deleting the account.
  Currently this page only has working password changes. Expect an update pretty quickly.

* There's a 'contact me' page that sends an email to the admin account.
  Currently that contact page is public access.
  I'll be extending the account settings page to include admin changes like having the contact page be protected or not.
  