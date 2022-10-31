import json

import pytest

from app.api import crud
from app.api.models import BlogPostDB

# ----------------------------------------------------------------------------------------------
# use the pytest monkeypatch fixture to mock out the crud.post operation: 
def test_create_blogpost(test_app, monkeypatch):
    test_request_payload = {"title": "something", "description": "something else"}
    test_response_payload = {"id": 1, "owner": 1, "title": "something", "description": "something else"}

    async def mock_post(payload, user_id):
        return 1

    mock_user_id = 1
    
    monkeypatch.setattr(crud, "post_blogpost", mock_post)


    response = test_app.post("/blogposts/", 
                             data=json.dumps(test_request_payload))

    assert response.status_code == 201
    assert response.json() == test_response_payload

# ----------------------------------------------------------------------------------------------
def test_create_blogpost_invalid_json(test_app):
    response = test_app.post("/blogposts/", data=json.dumps({"title": "something"}))
    assert response.status_code == 422

    response = test_app.post("/blogposts/", data=json.dumps({"title": "1", "description": "2"}))
    assert response.status_code == 422

# ----------------------------------------------------------------------------------------------
def test_read_blogpost(test_app, monkeypatch):
    test_data = {"id": 1, 
                 "owner": 1, 
                 "title": "something", 
                 "description": "something else"}

    async def mock_get(id):
        return test_data

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    response = test_app.get("/blogposts/1")
    assert response.status_code == 200
    assert response.json() == test_data

# ----------------------------------------------------------------------------------------------
def test_read_blogpost_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    response = test_app.get("/blogposts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "BlogPost not found"

    response = test_app.get("/blogposts/0")
    assert response.status_code == 422

# ----------------------------------------------------------------------------------------------
def test_read_all_blogposts(test_app, monkeypatch):
    test_data = [
        {"owner": 1, "title": "something", "description": "something else", "id": 1},
        {"owner": 1, "title": "someone", "description": "someone else", "id": 2},
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, "get_all_blogposts", mock_get_all)

    response = test_app.get("/blogposts/")
    assert response.status_code == 200
    assert response.json() == test_data

# ----------------------------------------------------------------------------------------------
def test_update_blogpost(test_app, monkeypatch):
    test_id = 1
    
    test_update_data = {"id": test_id, "owner": 1, "title": "someone", "description": "someone else"}

    async def mock_get(id) -> BlogPostDB:
        bp = BlogPostDB(id=id, owner=1, title="someone", description="someone else")
        return bp

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    async def mock_put(test_id, payload):
        return test_id

    monkeypatch.setattr(crud, "put_blogpost", mock_put)

    response = test_app.put("/blogposts/1/", data=json.dumps(test_update_data))
    assert response.status_code == 200
    assert response.json() == test_update_data

# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "id, payload, status_code",
    [
        [1, {}, 422],
        [1, {"description": "bar"}, 422],
        [999, {"title": "foo", "description": "bar"}, 404],
        [1, {"title": "1", "description": "bar"}, 422],
        [1, {"title": "foo", "description": "1"}, 422],
        [0, {"title": "foo", "description": "bar"}, 422],
    ],
)
def test_update_blogpost_invalid(test_app, monkeypatch, id, payload, status_code):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    response = test_app.put(f"/blogposts/{id}/", data=json.dumps(payload),)
    assert response.status_code == status_code

# ----------------------------------------------------------------------------------------------
def test_remove_blogpost(test_app, monkeypatch):
    test_data = {"id": 1, "owner": 1, "title": "something", "description": "something else"}
    
    async def mock_get(id) -> BlogPostDB:
        td = BlogPostDB(id=1, owner=1, title="something", description="something else")
        return td

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    async def mock_delete(id):
        return id

    monkeypatch.setattr(crud, "delete_blogpost", mock_delete)

    response = test_app.delete("/blogposts/1/")
    assert response.status_code == 200
    assert response.json() == test_data

# ----------------------------------------------------------------------------------------------
def test_remove_blogpost_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_blogpost", mock_get)

    response = test_app.delete("/blogposts/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "BlogPost not found"

    response = test_app.delete("/blogposts/0/")
    assert response.status_code == 422

