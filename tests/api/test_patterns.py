class TestGetSlowLinks:
    """Tests for the GET /patterns/slow_links endpoint."""

    def test_get_slow_links(self, client, setup_test_data):
        response = client.get("/patterns/slow_links", params={
            "period": "AM Peak",
            "threshold": 22.0,
            "min_days": 1
        })
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["link_id"] == 9999991
        assert data[0]["average_speed"] == 20.0
        assert data[0]["slow_days"] == 1

    def test_get_slow_links_not_slow_enough(self, client, setup_test_data):
        response = client.get("/patterns/slow_links", params={
            "period": "AM Peak",
            "threshold": 10.0,
            "min_days": 1
        })
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_slow_links_schema_validation_error(self, client):
        response = client.get("/patterns/slow_links", params={"threshold": 10.0, "min_days": 1})
        assert response.status_code == 422
