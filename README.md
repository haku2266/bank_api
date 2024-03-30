# Bank API

### `FastAPI` project for learning purposes

#### -|- List of technologies unitilized:

-   `SQLAlchemy` as an ORM
-   `PyJWT` as a decoder for custom JWT
-   `Redis` as both message broker and NoSQL database
-   `PostgreSQL` as a SQL database
-   `Celery Worker` for background tasks
-   `Docker & Docker-composer` for containerization
-   `Gunicorn & Univorn Workers` to handle the run state
-   and more

#### -|- How to run the project:

_Clone the application to your local device_

```bash
git clone git@github.com:haku2266/bank_api.git
```

_Get into the app directory_

```bash
cd bank_api/
```

_Run docker-compose file_

``` bash
docker-compose up --build
```

_Access the swagger app thought the next link_

**http://0.0.0.0:8000/docs**


###### P.S: The project is not complete. Few endpoints might be out of service.
