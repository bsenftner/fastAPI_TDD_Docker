# FastAPI_TDD_Docker : BlogPosts and Data Notes wrapped in a mini-CMS

## HTML w/ minimal JavaScript GUI on top of FastAPI CRUD APIs for "blog posts" and "data notes" with tests & CI/CD via Docker

### Note: this is a Python project, a website, that has a few Three.js pages. Three.js is hosted, and the number of Three.js source files makes Github statistics treat the project as JavaScript in the repo's metadata when it is really Python. 

A "data note" is arbitary JSON with a title and description. It's used for tracking site data, and providing data for visualizations.

Note Dec 18, 22: I just added several hundred megs worth of Three.js lib and utils. A `/a3da_basic` endpoint is a basic three.js scene. Just loads a gltf of Obama.

Note Jan 2, 23: First pass at some face controls for a custom 3D avatar, visible at `/a3da_newBody` endpoint. This is an experiment playground. Warning, large download, around 200 MB.

1. You'll need Docker to use this repo; this was developed using WSL2-Ubuntu on Win10 with Docker Desktop 4.12.0 (85629)
   - If you intend to place this public & online, then you will also need:
     - a public hosting location,
     - a domain you control,
     - and an email address at that domain.
   - The following steps describe how one would work with this repo locally, with variations for docker compose use on a hosting acct as well.
   - The difference when running in a hosting environment consists of running Traefik, a reverse proxy, in front of our app
   and Traefik handles routing between https and http to our app, as well as automated Let's Encrypt ssl cert generation.
     - As far as you're concerned, you just need two things:
       - make sure you do the steps outlined in the **Running on a public server** section, bottom of this document,
       - and when using `docker compose` make sure to specify the production yaml files containing the Traefik configuration for the public server's ssl needs.
         - those variations of yaml file use are included in the steps below.
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
    ADMIN_USERNAME=[admin-username]
    ADMIN_EMAIL=[admin-email-address]
    MAIL_USERNAME=[email-username-often-same-as-email-address]
    MAIL_PASSWORD=[email-password]
    MAIL_FROM=[email-from-account]
    MAIL_PORT=587
    MAIL_SERVER=[smtp-email-server-addr]
    MAIL_FROM_NAME=[email-from-account-username]
    ```

    Replace the values on the first two lines with the random hex strings generated in step 3.

    The `ADMIN_USERNAME` and `ADMIN_EMAIL` lines should be modified to be the username and email you intend to use as the site's admin.

    Unless you already have a programmatic email address you use and can get the various `MAIL_*`
    settings for above, I suggest looking up using GMail and their secure app email password system.

5. Navigate back the project's root, where the `docker-compose.yml` file is located and enter:

    ```text
    docker compose -f docker-compose.yml up -d --build
    ```

    Note: if you are doing this on a live hosted server, you need to specify the production version:

    ```text
    docker compose -f docker-compose-prod.yml up -d --build
    ```

    the production docker compose includes the Traefik proxy with automated ssl cert generation.

6. Via your web browser visit `http://localhost:8002/docs` to use the OpenAPI GUI
7. Run tests from project root with `docker compose exec web pytest .`

   - Tests should pass.
   - These are testing the CRUD REST endpoints, but there are more tests I should add that are not just CRUD operations.

8. Visit `http://localhost:8002/register` to create the first user on the website GUI.

   - I suggest registering the admin account first, using the info supplied in the .env file (described step 4).

This produces two Docker containers, one hosting postgres and the other our FastAPI app.
It is pretty basic at this point, quite easy to make your own. The file page_frags.py is the only one
with text branding, and the single photo jpeg used so far is in that file too.

The database itself is saved to the Docker host system. You can choose to take the app down deleting the database or preserving it.
The pair of containers can be taken down with the db deleted using:

```text
docker compose -f docker-compose.yml down -v
```

Or, if you want to preserve the info in the database, just use:

```text
docker compose -f docker-compose.yml down
```

Next time you do step 5, above, the previous database info will still be there.

Note: just like before, if this on a live hosted server, you need to specify the production yamls:

```text
docker compose -f docker-compose-prod.yml down -v
```

Or to take the app down preserving the production database:

```text
docker compose -f docker-compose-prod.yml down
```

For my own mental ease, I've adopted the practice of explicitly stating the yaml file to use to docker compose.

## Database Backups

Look in the `app/backups` directory for two scipts, one generates a backup of the database and the other restores a backup. These are run from the Docker host as follows:

```text
cd [your-docker-container's-app/backups-directory]
./new_backup.sh [postgres-docker-container-id]
```

The above will generate a gzip compressed file named dump_[timestamp].gz. Below restores one of them:

```text
cd [your-docker-container's-app/backups-directory]
./restore_backup.sh [database-backup.gz] [postgres-container-id]
```

The web site's Settings page has a pulldown selection and button to download existing database backups from a browser.
Backups still need to be created by logging into the container host and running `new_backup.sh`.
The Settings page download feature is convenience.

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

### Running on a public server

- When running this repo in public, before launching the app via docker compose, do these steps on your hosting acct:
  - Go to the Traefik directory and edit `traefik.toml`, line 15, to be the email address you control at the domain you control.
  - You need a secure password for your Traefik router admin account, so first install these tools:

    ```text
    sudo apt-get install apache2-utils
    ```

  - The utility needed is called `htpasswd` and you use it like this (replacing `secure_password` with your actual password):

    ```text
    htpasswd -nb admin secure_password
    ```

  - The output will look something like the below, save it for use in a bit:

    ```text
    admin:$apr1$ruca84Hq$mbjdMZBAG.KWn7vfN/SNK/
    ```

  - Now go to the Traefik directory again, this time edit `traefik_dynamic.toml`, line 3, to be
  that output generated by `htpasswd`. Put the `htpasswd` output inside the quotation marks.
  - Still inside that `traefik_dynamic.toml` file, go to line 7 and modify the line to be your domain. Save and quit your editor.
  - Now execute `launch_traefik.sh` to cause a Docker container hosting traefik to be downloaded, if necessary,
  and launched. This will auto-generate ssl certs via Let's Encrypt.
  - If you are having issues with this, I followed this guide to figure it out myself:
    - <https://www.digitalocean.com/community/tutorials/how-to-use-traefik-v2-as-a-reverse-proxy-for-docker-containers-on-ubuntu-20-04>
