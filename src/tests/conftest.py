import pytest
from starlette.testclient import TestClient
import os
from app.main import create_application
from app.config import get_settings, Settings
from app.api.models import UserInDB
from app.api.users import get_current_active_user

def get_settings_override():
    return Settings(testing=1, database_url=os.environ.get("DATABASE_TEST_URL"))

def get_current_active_user_override():
    return UserInDB(id=1,
                    verify_code='x',
                    hashed_password='bogus',
                    username='bsenftner', 
                    email='bsenftner@earthlink.net',
                    roles='user admin')

@pytest.fixture(scope="module")
def test_app():
    # set up
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    app.dependency_overrides[get_current_active_user] = get_current_active_user_override
    with TestClient(app) as test_client:

        # testing
        yield test_client

    # tear down
