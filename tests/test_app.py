"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state for each test"""
    # Save original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy(),
        }
        for name, activity in activities.items()
    }

    yield

    # Restore original state after test
    for name, activity in activities.items():
        activity["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert len(data) > 0

    def test_get_activities_includes_required_fields(
        self, client, reset_activities
    ):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_participants_are_strings(self, client, reset_activities):
        """Test that all participants are email strings"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity in data.items():
            for participant in activity["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant_to_list(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        email = "newsignup@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")

        # Verify by fetching activities
        response = client.get("/activities")
        data = response.json()
        assert email in data["Basketball"]["participants"]

    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Test that signing up the same student twice fails"""
        email = "duplicate@mergington.edu"

        # First signup should succeed
        response1 = client.post(f"/activities/Basketball/signup?email={email}")
        assert response1.status_code == 200

        # Second signup should fail
        response2 = client.post(f"/activities/Basketball/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/NonexistentClub/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_students_different_activities(
        self, client, reset_activities
    ):
        """Test that different students can sign up for different activities"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"

        client.post(f"/activities/Basketball/signup?email={email1}")
        client.post(f"/activities/Tennis Club/signup?email={email2}")

        response = client.get("/activities")
        data = response.json()

        assert email1 in data["Basketball"]["participants"]
        assert email2 in data["Tennis Club"]["participants"]
        assert email2 not in data["Basketball"]["participants"]
        assert email1 not in data["Tennis Club"]["participants"]

    def test_signup_same_student_multiple_activities(self, client, reset_activities):
        """Test that the same student can sign up for multiple activities"""
        email = "versatile@mergington.edu"

        client.post(f"/activities/Basketball/signup?email={email}")
        client.post(f"/activities/Tennis Club/signup?email={email}")

        response = client.get("/activities")
        data = response.json()

        assert email in data["Basketball"]["participants"]
        assert email in data["Tennis Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_successful(self, client, reset_activities):
        """Test successful removal of a participant"""
        # First add a participant
        email = "todelete@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")

        # Then remove them
        response = client.delete(
            f"/activities/Basketball/participants?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]

    def test_remove_participant_from_list(self, client, reset_activities):
        """Test that removal actually removes from the list"""
        email = "toremove@mergington.edu"
        client.post(f"/activities/Basketball/signup?email={email}")

        # Verify participant is added
        response = client.get("/activities")
        assert email in response.json()["Basketball"]["participants"]

        # Remove participant
        client.delete(f"/activities/Basketball/participants?email={email}")

        # Verify participant is removed
        response = client.get("/activities")
        assert email not in response.json()["Basketball"]["participants"]

    def test_remove_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from non-existent activity fails"""
        response = client.delete(
            "/activities/NonexistentClub/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing non-existent participant fails"""
        response = client.delete(
            "/activities/Basketball/participants?email=notexist@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_does_not_affect_other_activities(
        self, client, reset_activities
    ):
        """Test that removing from one activity doesn't affect others"""
        email = "shared@mergington.edu"

        # Add to multiple activities
        client.post(f"/activities/Basketball/signup?email={email}")
        client.post(f"/activities/Tennis Club/signup?email={email}")

        # Remove from Basketball
        client.delete(f"/activities/Basketball/participants?email={email}")

        # Verify removed from Basketball but still in Tennis Club
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Basketball"]["participants"]
        assert email in data["Tennis Club"]["participants"]


class TestRootRedirect:
    """Tests for root path redirect"""

    def test_root_redirects_to_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert "Mergington High School" in response.text or "html" in response.text


class TestActivityStructure:
    """Tests for activity data structure integrity"""

    def test_all_activities_have_consistent_structure(
        self, client, reset_activities
    ):
        """Test that all activities have the same structure"""
        response = client.get("/activities")
        data = response.json()

        required_fields = {
            "description",
            "schedule",
            "max_participants",
            "participants",
        }

        for activity_name, activity in data.items():
            assert set(activity.keys()) == required_fields
            assert isinstance(activity["description"], str)
            assert isinstance(activity["schedule"], str)
            assert isinstance(activity["max_participants"], int)
            assert isinstance(activity["participants"], list)

    def test_max_participants_is_positive(self, client, reset_activities):
        """Test that max_participants is a positive integer"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity in data.items():
            assert activity["max_participants"] > 0
