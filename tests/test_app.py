import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    isolated_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activities):
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_list_activities_returns_current_activity_data(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_student_to_activity(client, activities):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert "new.student@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_student(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_student_from_activity(client, activities):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_nonparticipant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("post", "/activities/Chess%20Club/signup"),
        ("delete", "/activities/Chess%20Club/participants"),
    ],
)
def test_mutation_routes_require_email_query_parameter(client, method, url):
    response = getattr(client, method)(url)

    assert response.status_code == 422
    assert response.json()["detail"]
