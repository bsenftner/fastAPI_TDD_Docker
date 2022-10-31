import json
from typing import List

import pytest

from app.api import crud
from app.api.models import NoteDB

# ----------------------------------------------------------------------------------------------
# use the pytest monkeypatch fixture to mock out the crud.post operation: 
def test_create_note(test_app, monkeypatch):
    test_request_payload = {"title": "something", "description": "something else", "data": '{"datum": 10}' }
    
    test_response_payload = {"id": 1, "owner": 1, "title": "something", "description": "something else", "data": '{"datum": 10}' }
    
    async def mock_get_note_by_title(id) -> NoteDB:
        return None

    monkeypatch.setattr(crud, "get_note_by_title", mock_get_note_by_title)
    
    async def mock_post(payload, user_id):
        return 1

    monkeypatch.setattr(crud, "post_note", mock_post)

    response = test_app.post("/notes/", data=json.dumps(test_request_payload))

    assert response.status_code == 201
    assert response.json() == test_response_payload

# ----------------------------------------------------------------------------------------------
def test_create_note_invalid_json(test_app):
    response = test_app.post("/notes/", data=json.dumps({"title": "something"}))
    assert response.status_code == 422

    response = test_app.post("/notes/", data=json.dumps({"title": "1", "description": "2"}))
    assert response.status_code == 422

# ----------------------------------------------------------------------------------------------
def test_read_note(test_app, monkeypatch):
    test_data = {"id": 1, 
                 "owner": 1, 
                 "title": "something", 
                 "description": "something else",
                 "data": "{'datum':10}"}

    async def mock_get(id) -> NoteDB:
        ndb = NoteDB( id=1, 
                      owner=1, 
                      title="something", 
                      description="something else",
                      data="{'datum':10}")
        return ndb

    monkeypatch.setattr(crud, "get_note", mock_get)

    response = test_app.get("/notes/1")
    assert response.status_code == 200
    assert response.json() == test_data

# ----------------------------------------------------------------------------------------------
def test_read_note_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_note", mock_get)

    response = test_app.get("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"

    response = test_app.get("/notes/0")
    assert response.status_code == 422

# ----------------------------------------------------------------------------------------------
def test_read_all_notes(test_app, monkeypatch):
    test_data = [NoteDB( id=1, 
                       owner=1, 
                       title="something", 
                       description="something else",
                       data="{'datum':10}"),
               NoteDB( id=2, 
                       owner=1, 
                       title="someone", 
                       description="someone else",
                       data="{'datum':10}")
        ]
    
    test_response = [{ "id": 1, 
                       "owner": 1, 
                       "title": "something", 
                       "description": "something else",
                       "data": "{'datum':10}"
                    },
                    { "id": 2, 
                       "owner": 1, 
                       "title": "someone", 
                       "description": "someone else",
                       "data": "{'datum':10}"
                    }]

    async def mock_get_all() -> List[NoteDB]:
        return test_data

    monkeypatch.setattr(crud, "get_all_notes", mock_get_all)

    response = test_app.get("/notes/")
    assert response.status_code == 200
    assert response.json() == test_response

# ----------------------------------------------------------------------------------------------
def test_update_note(test_app, monkeypatch):
    test_update_data = { "title": "someone", 
                         "description": "someone else", 
                         "data": '{"datum": 10}' 
                       }

    async def mock_get(id) -> NoteDB:
        ndb = NoteDB( id=1, 
                      owner=1, 
                      title="someone", 
                      description="something else",
                      data='{"datum": 10}')
        return ndb

    monkeypatch.setattr(crud, "get_note", mock_get)

    async def mock_put(id, payload, owner):
        return 1

    monkeypatch.setattr(crud, "put_note", mock_put)

    test_response = {"id": 1, 
                     "owner": 1, 
                     "title": "someone", 
                     "description": "someone else",
                     "data": '{"datum": 10}'}
    
    response = test_app.put("/notes/1/", data=json.dumps(test_update_data))
    assert response.status_code == 200
    assert response.json() == test_response

# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "id, payload, status_code",
    [
        [1, {"data": "{'datum':10}"}, 422],
        [1, {"description": "bar", "data": "{'datum':10}"}, 422],
        [999, {"title": "foo", "description": "bar", "data": "{'datum':10}" }, 404],
        [1, {"title": "1", "description": "bar", "data": "{'datum':10}"}, 422],
        [1, {"title": "foo", "description": "1", "data": "{'datum':10}"}, 422],
        [0, {"title": "foo", "description": "bar", "data": "{'datum':10}"}, 422],
    ],
)
def test_update_note_invalid(test_app, monkeypatch, id, payload, status_code):
    
    async def mock_get(id) -> NoteDB:
        if id==1:
            ndb = NoteDB( id=1, 
                          owner=1, 
                          title="something", 
                          description="something else",
                          data="{'datum':10}")
            return ndb
        return None

    monkeypatch.setattr(crud, "get_note", mock_get)
    
    response = test_app.put(f"/notes/{id}/", data=json.dumps(payload),)
    
    assert response.status_code == status_code

# ----------------------------------------------------------------------------------------------
def test_remove_note(test_app, monkeypatch):
    test_data = { "id": 1, 
                  "owner": 1, 
                  "title": "something", 
                  "description": "something else",
                  "data": "{'datum':10}"
                }

    async def mock_get(id) -> NoteDB:
        ndb = NoteDB( id=1, 
                      owner=1, 
                      title="something", 
                      description="something else",
                      data="{'datum':10}")
        return ndb

    monkeypatch.setattr(crud, "get_note", mock_get)

    async def mock_delete(id):
        return id

    monkeypatch.setattr(crud, "delete_note", mock_delete)

    response = test_app.delete("/notes/1/")
    assert response.status_code == 200
    assert response.json() == test_data

# ----------------------------------------------------------------------------------------------
def test_remove_note_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_note", mock_get)

    response = test_app.delete("/notes/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"

    response = test_app.delete("/notes/0/")
    assert response.status_code == 422

