class TestGetAggregates:
    """Tests for the GET /aggregates/ endpoint."""
    
    def test_get_aggregates_without_query_params(self, client, setup_test_data):
        response = client.get("/aggregates/")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["link_id"] == 9999991
        assert data[0]["average_speed"] == 20.0
        assert data[1]["link_id"] == 9999992
        assert data[1]["average_speed"] == 45.0

    def test_get_aggregates_with_query_params(self, client, setup_test_data):
        response = client.get("/aggregates/", params={"day": "Monday", "period": "AM Peak", "limit": 5})
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["link_id"] == 9999991
        assert data[0]["average_speed"] == 20.0
    
    def test_get_aggregates_with_pagination(self, client, setup_test_data):
        response = client.get("/aggregates/", params={"limit": 1})
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["link_id"] == 9999991
        assert data[0]["average_speed"] == 20.0

    def test_get_aggregates_empty_result(self, client, setup_test_data):
        response = client.get("/aggregates/", params={"day": "Sunday", "period": "Evening"})
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestGetLinkAggregates:
    """Tests for the GET /aggregates/{link_id} endpoint."""
    
    def test_get_link_aggregates(self, client, setup_test_data):
        response = client.get("/aggregates/9999991", params={"period": "AM Peak"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 9999991
        assert data["road_name"] == "Test Road A"
        assert len(data["speeds"]) == 2

    def test_get_link_aggregates_not_found(self, client):
        response = client.get("/aggregates/123456789")
        assert response.status_code == 404


class TestSpatialFilter:
    """Tests for the POST /aggregates/spatial_filter endpoint."""
    
    def test_spatial_filter(self, client, setup_test_data):
        payload = {
            "min_lon": -81.6,
            "min_lat": 29.5,
            "max_lon": -81.4,
            "max_lat": 30.5,
            "day": "Monday",
            "period": "AM Peak"
        }
        response = client.post("/aggregates/spatial_filter", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == 9999991
        assert data[0]["road_name"] == "Test Road A"
        assert len(data[0]["speeds"]) == 2

    def test_spatial_filter_invalid_bbox(self, client):
        payload = {
            "min_lon": -81.0,
            "min_lat": 29.5,
            "max_lon": -82.0,
            "max_lat": 30.5,
            "day": "Monday",
            "period": "AM Peak"
        }
        response = client.post("/aggregates/spatial_filter", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "min_lon must be less than max_lon" in data["detail"][0]["msg"]
