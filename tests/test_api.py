"""
Tests for the Mergington High School API

Tests cover:
- Getting activities list
- Signing up for activities
- Unregistering from activities
- Error handling and validation
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Save original state
    original_state = {
        key: {
            "description": val["description"],
            "schedule": val["schedule"],
            "max_participants": val["max_participants"],
            "participants": val["participants"].copy()
        }
        for key, val in activities.items()
    }
    
    yield
    
    # Restore original state
    for key, val in original_state.items():
        activities[key]["participants"] = val["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, reset_activities):
        """Test that /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, reset_activities):
        """Test that /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_required_activities(self, reset_activities):
        """Test that response contains expected activities"""
        response = client.get("/activities")
        activities_data = response.json()
        
        expected_activities = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Math Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in activities_data
    
    def test_activity_has_required_fields(self, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_details in activities_data.items():
            for field in required_fields:
                assert field in activity_details, f"Missing field '{field}' in {activity_name}"


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200(self, reset_activities):
        """Test successful signup returns 200"""
        response = client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_returns_message(self, reset_activities):
        """Test signup response contains message"""
        response = client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": "student@mergington.edu"}
        )
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup adds participant to activity"""
        email = "newstudent@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_participants = response.json()["Basketball Team"]["participants"].copy()
        
        # Sign up
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        new_participants = response.json()["Basketball Team"]["participants"]
        assert len(new_participants) == len(initial_participants) + 1
        assert email in new_participants
    
    def test_signup_nonexistent_activity_returns_404(self, reset_activities):
        """Test signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_returns_400(self, reset_activities):
        """Test duplicate signup returns 400"""
        email = "test@mergington.edu"
        
        # First signup
        response1 = client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_existing_participant(self, reset_activities):
        """Test that existing participants are still registered"""
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Verify existing participants are present
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200(self, reset_activities):
        """Test successful unregister returns 200"""
        email = "test@mergington.edu"
        
        # First sign up
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Basketball%20Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_unregister_returns_message(self, reset_activities):
        """Test unregister response contains message"""
        email = "test@mergington.edu"
        
        # Sign up first
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        
        # Unregister
        response = client.post(
            "/activities/Basketball%20Team/unregister",
            params={"email": email}
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister removes participant from activity"""
        email = "test@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Basketball%20Team/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()["Basketball Team"]["participants"]
        
        # Unregister
        client.post(
            "/activities/Basketball%20Team/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()["Basketball Team"]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, reset_activities):
        """Test unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_nonparticipant_returns_400(self, reset_activities):
        """Test unregister for non-participant returns 400"""
        response = client.post(
            "/activities/Basketball%20Team/unregister",
            params={"email": "nonparticipant@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_existing_participant(self, reset_activities):
        """Test unregistering an existing participant"""
        # Unregister from Chess Club
        response = client.post(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]
        # Other participant should still be there
        assert "daniel@mergington.edu" in response.json()["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""
    
    def test_signup_and_unregister_flow(self, reset_activities):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Soccer Club"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Verify signed up
        response2 = client.get("/activities")
        assert email in response2.json()[activity]["participants"]
        
        # Unregister
        response3 = client.post(
            f"/activities/{activity.replace(' ', '%20')}/unregister",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify unregistered
        response4 = client.get("/activities")
        assert email not in response4.json()[activity]["participants"]
    
    def test_multiple_signups_same_activity(self, reset_activities):
        """Test multiple different students signing up for same activity"""
        activity = "Art Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signed up
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
    
    def test_signup_multiple_activities(self, reset_activities):
        """Test same student signing up for multiple activities"""
        email = "student@mergington.edu"
        activities_list = ["Basketball Team", "Soccer Club", "Art Club"]
        
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity.replace(' ', '%20')}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify signed up for all
        response = client.get("/activities")
        activities_data = response.json()
        for activity in activities_list:
            assert email in activities_data[activity]["participants"]
