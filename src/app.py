from flask import (
    Flask,
    current_app,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)

from varasto import Varasto


def _parse_non_negative_float(value):
    try:
        parsed_value = float(value)
    except ValueError:
        return None
    if parsed_value < 0:
        return None
    return parsed_value


def _validate_warehouse_name(name):
    cleaned_name = name.strip()
    if not cleaned_name:
        return None, "Warehouse name is required and cannot be only whitespace."
    if len(cleaned_name) > 50:
        return None, "Warehouse name can be at most 50 characters long."
    if not all(character.isalnum() or character.isspace()
               for character in cleaned_name):
        return None, (
            "Warehouse name can only contain letters, numbers and spaces."
        )
    return cleaned_name, None


def _validate_capacity(value):
    capacity = _parse_non_negative_float(value)
    if capacity is None:
        return None, "Capacity must be a non-negative number."
    return capacity, None


def _validate_amount(value):
    amount = _parse_non_negative_float(value)
    if amount is None:
        return None, "Amount must be a non-negative number."
    return amount, None


def _format_number(value):
    if value.is_integer():
        return str(int(value))
    return str(value)


def _find_warehouse(warehouses, id):  # pylint: disable=redefined-builtin
    for warehouse in warehouses:
        if warehouse.id == id:
            return warehouse
    return None


def _redirect_with_message(message):
    flash(message)
    return redirect(url_for("index"))


def _validate_create_request(warehouses):
    name, name_error = _validate_warehouse_name(request.form.get("name", ""))
    if name_error is not None:
        return None, None, name_error

    capacity, capacity_error = _validate_capacity(
        request.form.get("capacity", "")
    )
    if capacity_error is not None:
        return None, None, capacity_error

    if any(warehouse.nimi == name for warehouse in warehouses):
        return None, None, "Warehouse name must be unique."

    return name, capacity, None


def _adjust_warehouse_balance(warehouse, amount, operation):
    if operation == "add":
        warehouse.lisaa_varastoon(amount)
        return None
    if operation == "remove":
        warehouse.ota_varastosta(amount)
        return None
    return "Invalid operation selected."


def index():
    return render_template(
        "index.html",
        warehouses=current_app.config["WAREHOUSES"],
        format_number=_format_number,
        messages=get_flashed_messages(),
    )


def create_warehouse():
    warehouses = current_app.config["WAREHOUSES"]
    name, capacity, validation_error = _validate_create_request(warehouses)
    if validation_error is not None:
        return _redirect_with_message(validation_error)

    warehouses.append(
        Varasto(
            capacity,
            id=current_app.config["NEXT_ID"],
            nimi=name,
        )
    )
    current_app.config["NEXT_ID"] += 1

    return redirect(url_for("index"))


def adjust_warehouse(id):  # pylint: disable=redefined-builtin
    warehouse = _find_warehouse(current_app.config["WAREHOUSES"], id)
    if warehouse is None:
        return _redirect_with_message("Warehouse not found.")

    amount, amount_error = _validate_amount(request.form.get("amount", ""))
    if amount_error is not None:
        return _redirect_with_message(amount_error)

    error = _adjust_warehouse_balance(
        warehouse, amount, request.form.get("operation")
    )
    if error is not None:
        return _redirect_with_message(error)

    return redirect(url_for("index"))


def create_app():
    flask_app = Flask(__name__)
    flask_app.config["WAREHOUSES"] = []
    flask_app.config["NEXT_ID"] = 0
    flask_app.secret_key = "dev"
    flask_app.add_url_rule("/", "index", index, methods=["GET"])
    flask_app.add_url_rule(
        "/warehouses",
        "create_warehouse",
        create_warehouse,
        methods=["POST"],
    )
    flask_app.add_url_rule(
        "/warehouses/<int:id>/adjust",
        "adjust_warehouse",
        adjust_warehouse,
        methods=["POST"],
    )
    return flask_app


app = create_app()
