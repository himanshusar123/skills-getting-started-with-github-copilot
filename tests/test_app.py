from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] > 0
    assert "participants" in data["Chess Club"]


def test_signup_for_activity_success():
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_for_activity_rejects_duplicate_email():
    email = "duplicate@mergington.edu"
    client.post(f"/activities/Chess Club/signup?email={email}")

    response = client.post(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_for_activity_rejects_full_activity():
    activity = app_module.activities["Basketball Club"]
    original_participants = deepcopy(activity["participants"])
    activity["participants"] = [f"student{i}@mergington.edu" for i in range(activity["max_participants"])]

    try:
        response = client.post("/activities/Basketball Club/signup?email=overflow@mergington.edu")
    finally:
        activity["participants"] = original_participants

    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


def test_signup_for_activity_not_found():
    response = client.post("/activities/Unknown Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
