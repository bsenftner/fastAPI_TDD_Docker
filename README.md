# FastAPI_TDD_Docker : BlogPosts and Data Notes wrapped in a mini-CMS

## HTML w/ minimal JavaScript GUI on top of FastAPI CRUD APIs for "blog posts" and "data notes" with tests & CI/CD via Docker

A "data note" is arbitary JSON with a title and description. It's used for tracking site data, and providing data for visualizations.

1. You'll need Docker to use this repo; this was developed using WSL2-Ubuntu on Win10 with Docker Desktop 4.12.0 (85629)
   - If you intend to place this public & online, then you will also need a public hosting location, a domain you control, and an email address at that domain.
   - The following steps describe how one would work with this repo locally.
   - The difference when running in a hosting environment consists of running Traefik, a reverse proxy, in front of our app
   and Traefik handles routing between https and http to our app, as well as automated Let's Encrypt ssl cert generation.
     - These steps are described in the notes section, bottom of this document.
2. After getting your own copy of the repo, via a terminal navigate to `src\app` and create a file named `.env` in the same directory as main.py
3. Enter `openssl rand -hex 32` to generate a random hex string, and again because you'll need two. These will be your secret hash strings.
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

   - Tests should pass.
   - These are testing the CRUD REST endpoints, but there are more tests I should add that are not just CRUD operations.

8. Visit `http://localhost:8002/register` to create the first user on the static GUI.

9. Currently the "admin" account is hardcoded to my info, but you can change that by modifying the "/users/register" endpoint.

   - Look in app/api/users_htmlpages.html around line 128, where the user roles are initialized. Just change that info to yours.
   - Next version will have this "admin" info in the Settings/config .env file.

This produces two Docker images, one hosting postgres and the other the FastAPI app.
It is pretty basic at this point, quite easy to make your own. The file page_frags.py is the only one
with text branding, and the single photo jpeg used so far is in that file too.

The database itself is saved to the Docker host system. You can choose to take the app down deleting the database or preserving it.
The pair of containers can be taken down with the db deleted using:

`docker compose down -v`

Or, if you want to preserve the info in the database, just use:

`docker compose down`

Next time you do step 5, above, the previous database info will still be there.

## Notes

- Uses JWT Bearer Token Authentication, using both local storage and httpOnly cookies.

- New users are sent an email with an email verification code.
  - That code is requested upon login.
  - Without the code the account cannot post or make account settings changes.

- Just modified the "notes" to be data containers with a title and a description.
  - The data is arbitary JSON, with ownership controls for privacy.
  - I'll be using these "notes" for various things as this shapes up into a showcase type CMS.

- There's a basic user account settings page. This is for changing email, changing password or disabling the account.
  - If the user is an admin, additional site admin controls are added to the Settings page
  - User settings cannot be changed unless the user has a verified email.
  - When either the email or password changes, a notification email is sent.
  - In the case of an email change, that notification is sent to the new email account with a new email verification code.

  Each of these user settings page features work. Be aware "deleting" an account is disabling, all that account's info is retained.

- There is a 'contact me' page that sends an email to the admin account.
  - On the Settings page for admins there is a control to make the Contact page public or require login.
    - If not public, going to the Contact redirects to the homepage.
  