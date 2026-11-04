from app import create_app


def create_warehouse(client, name, capacity):
    return client.post(
        "/warehouses",
        data={"name": name, "capacity": str(capacity)},
        follow_redirects=True,
    )


def add_to_warehouse(client, warehouse_id, amount):
    return client.post(
        f"/warehouses/{warehouse_id}/add",
        data={"amount": str(amount)},
        follow_redirects=True,
    )


def remove_from_warehouse(client, warehouse_id, amount):
    return client.post(
        f"/warehouses/{warehouse_id}/remove",
        data={"amount": str(amount)},
        follow_redirects=True,
    )


def test_listing_shows_empty_state_when_no_warehouses_exist():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"No warehouses available" in response.data


def test_create_warehouse_validates_name_and_capacity():
    app = create_app()
    client = app.test_client()

    invalid_inputs = [
        ("", "1"),
        ("   ", "1"),
        ("a" * 51, "1"),
        ("Ware@house", "1"),
        ("Warehouse1", "-1"),
        ("Warehouse1", "not-a-number"),
    ]

    for name, capacity in invalid_inputs:
        response = create_warehouse(client, name, capacity)
        assert response.status_code == 200
        assert b"No warehouses available" in response.data

    first = create_warehouse(client, "Warehouse1", "1")
    assert b"Warehouse1 | used: 0 | capacity: 1" in first.data

    duplicate = create_warehouse(client, "Warehouse1", "2")
    assert b"Warehouse1 | used: 0 | capacity: 1" in duplicate.data
    assert b"Warehouse1 | used: 0 | capacity: 2" not in duplicate.data


def test_listing_shows_warehouse_data_and_updates_from_additions():
    app = create_app()
    client = app.test_client()

    create_warehouse(client, "Warehouse1", "1")
    assert b"Warehouse1 | used: 0 | capacity: 1" in client.get("/").data

    add_to_warehouse(client, 0, 0.5)
    assert b"Warehouse1 | used: 0.5 | capacity: 1" in client.get("/").data

    add_to_warehouse(client, 0, -5)
    assert b"Warehouse1 | used: 0.5 | capacity: 1" in client.get("/").data

    add_to_warehouse(client, 0, 5)
    assert b"Warehouse1 | used: 1 | capacity: 1" in client.get("/").data


def test_can_create_ten_warehouses_and_modify_all_using_ids():
    app = create_app()
    client = app.test_client()

    capacities = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    for index, capacity in enumerate(capacities):
        create_warehouse(client, f"Warehouse{index}", capacity)

    listing = client.get("/").data
    for index, capacity in enumerate(capacities):
        entry = f"Warehouse{index} | used: 0 | capacity: {capacity}".encode()
        assert entry in listing

    for index in range(10):
        add_to_warehouse(client, index, index)

    listing = client.get("/").data
    for index, capacity in enumerate(capacities):
        used_capacity = min(float(index), float(capacity))
        formatted = int(used_capacity) if used_capacity.is_integer() else used_capacity
        expected = (
            f"Warehouse{index} | used: {formatted} | capacity: {capacity}".encode()
        )
        assert expected in listing


def test_add_and_remove_updates_used_capacity_and_handles_edge_cases():
    app = create_app()
    client = app.test_client()

    create_warehouse(client, "Warehouse1", "1")

    add_to_warehouse(client, 0, 0.5)
    assert b"Warehouse1 | used: 0.5 | capacity: 1" in client.get("/").data

    remove_from_warehouse(client, 0, 0.2)
    assert b"Warehouse1 | used: 0.3 | capacity: 1" in client.get("/").data

    remove_from_warehouse(client, 0, 0.3)
    emptied = client.get("/").data
    assert b"Warehouse1 | used: 0 | capacity: 1" in emptied
    assert b"/warehouses/0/remove" not in emptied

    remove_from_warehouse(client, 0, 0.5)
    assert b"Warehouse1 | used: 0 | capacity: 1" in client.get("/").data

    add_to_warehouse(client, 0, "invalid")
    assert b"Warehouse1 | used: 0 | capacity: 1" in client.get("/").data

    remove_from_warehouse(client, 99, 1)
    add_to_warehouse(client, 99, 1)
    assert b"Warehouse1 | used: 0 | capacity: 1" in client.get("/").data
