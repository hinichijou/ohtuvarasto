from app import create_app


def create_warehouse(client, name, capacity):
    return client.post(
        "/warehouses",
        data={"name": name, "capacity": str(capacity)},
        follow_redirects=True,
    )


def adjust_warehouse(client, id, amount, operation):
    return client.post(
        f"/warehouses/{id}/adjust",
        data={"amount": str(amount), "operation": operation},
        follow_redirects=True,
    )


def test_listing_shows_empty_state_when_no_warehouses_exist():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Warehouse application" in response.data
    assert b"No warehouses available" in response.data


def test_form_contains_required_typed_inputs_and_helpful_placeholders():
    app = create_app()
    client = app.test_client()

    response = client.get("/").data

    assert b"Create a warehouse" in response
    assert b'type="number"' in response
    assert b'name="capacity"' in response
    assert b'placeholder="e.g. 10.5"' in response
    assert b'placeholder="Only letters, numbers and spaces"' in response
    assert b"required" in response


def test_create_warehouse_shows_validation_messages():
    app = create_app()
    client = app.test_client()

    invalid_inputs = [
        ("", "1", b"Warehouse name is required"),
        ("   ", "1", b"Warehouse name is required"),
        ("a" * 51, "1", b"at most 50 characters"),
        ("Ware@house", "1", b"can only contain letters, numbers and spaces"),
        ("Warehouse1", "-1", b"Capacity must be a non-negative number"),
        ("Warehouse1", "not-a-number", b"Capacity must be a non-negative number"),
    ]

    for name, capacity, error_message in invalid_inputs:
        response = create_warehouse(client, name, capacity)
        assert response.status_code == 200
        assert error_message in response.data
        assert b"No warehouses available" in response.data

    first = create_warehouse(client, "Warehouse1", "1")
    assert b"Warehouse1" in first.data
    assert b"used: 0 | capacity: 1" in first.data

    duplicate = create_warehouse(client, "Warehouse1", "2")
    assert b"Warehouse name must be unique." in duplicate.data
    assert b"Warehouse1" in duplicate.data
    assert b"used: 0 | capacity: 2" not in duplicate.data


def test_listing_shows_warehouse_data_and_updates_from_additions():
    app = create_app()
    client = app.test_client()

    create_warehouse(client, "Warehouse1", "1")
    assert b"Warehouse1" in client.get("/").data
    assert b"used: 0 | capacity: 1" in client.get("/").data

    adjust_warehouse(client, 0, 0.5, "add")
    assert b"used: 0.5 | capacity: 1" in client.get("/").data

    negative_add = adjust_warehouse(client, 0, -5, "add").data
    assert b"Amount must be a non-negative number." in negative_add
    assert b"used: 0.5 | capacity: 1" in negative_add

    adjust_warehouse(client, 0, 5, "add")
    assert b"used: 1 | capacity: 1" in client.get("/").data


def test_can_create_ten_warehouses_and_modify_all_using_ids():
    app = create_app()
    client = app.test_client()

    capacities = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    for index, capacity in enumerate(capacities):
        create_warehouse(client, f"Warehouse{index}", capacity)

    listing = client.get("/").data
    for index, capacity in enumerate(capacities):
        entry_name = f"Warehouse{index}".encode()
        entry_values = f"used: 0 | capacity: {capacity}".encode()
        assert entry_name in listing
        assert entry_values in listing

    for index in range(10):
        adjust_warehouse(client, index, index, "add")

    listing = client.get("/").data
    for index, capacity in enumerate(capacities):
        used_capacity = min(float(index), float(capacity))
        formatted = int(used_capacity) if used_capacity.is_integer() else used_capacity
        expected = f"used: {formatted} | capacity: {capacity}".encode()
        assert f"Warehouse{index}".encode() in listing
        assert expected in listing


def test_add_and_remove_updates_used_capacity_and_handles_edge_cases():
    app = create_app()
    client = app.test_client()

    create_warehouse(client, "Warehouse1", "1")
    initial_listing = client.get("/").data
    assert b'value="remove"' in initial_listing
    assert b"disabled" in initial_listing

    adjust_warehouse(client, 0, 0.5, "add")
    assert b"used: 0.5 | capacity: 1" in client.get("/").data

    adjust_warehouse(client, 0, 0.2, "remove")
    assert b"used: 0.3 | capacity: 1" in client.get("/").data

    adjust_warehouse(client, 0, 0.3, "remove")
    emptied = client.get("/").data
    assert b"used: 0 | capacity: 1" in emptied
    assert b"disabled" in emptied

    adjust_warehouse(client, 0, 0.5, "remove")
    assert b"used: 0 | capacity: 1" in client.get("/").data

    invalid_amount = adjust_warehouse(client, 0, "invalid", "add").data
    assert b"Amount must be a non-negative number." in invalid_amount
    assert b"used: 0 | capacity: 1" in invalid_amount

    invalid_operation = adjust_warehouse(client, 0, 1, "invalid")
    assert b"Invalid operation selected." in invalid_operation.data

    missing = adjust_warehouse(client, 99, 1, "add")
    assert b"Warehouse not found." in missing.data
