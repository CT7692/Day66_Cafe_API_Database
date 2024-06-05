from flask import Flask, jsonify, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import Integer, String, Boolean, select, desc

import os
import secrets

app = Flask(__name__)
API_KEY: str = os.environ.get('API_KEY')
SECRET_KEY = os.urandom(32)
app.config['SECURITY_KEY'] = SECRET_KEY

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    with Session(app):
        cafes = db.session.execute(select(Cafe).order_by(Cafe.name)).scalars()
    return render_template("index.html", cafes=cafes)

@app.route("/random", methods=['GET'])
def random_cafe():
    num_cafes = db.session.query(Cafe).count()
    rand_id = secrets.SystemRandom().randint(1, num_cafes)
    cafe = db.session.execute(select(Cafe).where(Cafe.id == rand_id))
    random_cafe = cafe.scalar()
    return jsonify(id=random_cafe.id,
                   name=random_cafe.name,
                   map_url=random_cafe.map_url,
                   img_url=random_cafe.img_url,
                   location=random_cafe.location,
                   seats=random_cafe.seats,
                   has_toilet=random_cafe.has_toilet,
                   has_wifi=random_cafe.has_wifi,
                   has_sockets=random_cafe.has_sockets,
                   can_take_calls=random_cafe.can_take_calls,
                   coffee_price=random_cafe.coffee_price)

@app.route("/all", methods=['GET'])
def all_cafes():
    cafe_jsons = []
    with Session(app):
        cafes = db.session.execute(select(Cafe).order_by(Cafe.id)).scalars()

        for cafe in cafes:
            cafe_dict = create_dict(cafe)
            cafe_jsons.append(cafe_dict)

    return  jsonify(cafe_jsons)

@app.route("/search")
def search_cafe():
        with Session(app):
            results = []
            search_location = request.args.get("loc").title()

            existing_cafes = db.session.execute(
                select(Cafe).where(Cafe.location == search_location)).scalars()

            location_exists = db.session.query(
                Cafe.location).filter_by(location=search_location).first() is not None

            if location_exists:
                for cafe in existing_cafes:
                    cafe_dict = create_dict(cafe)
                    results.append(cafe_dict)

                return jsonify(results)

            else:
                error = error_dict("Not Found: We don't have a cafe registered to this locatin.")

                return jsonify(error)


@app.route("/add", methods=['POST'])
def add_cafe():
    try:
        new_cafe = Cafe(name=request.form.get('name'),
                        map_url=request.form.get('map_url'),
                        img_url=request.form.get('img_url'),
                        location=request.form.get('location'),
                        seats=request.form.get('seats'),
                        has_toilet=bool(request.form.get('has_toilet')),
                        has_wifi=bool(request.form.get('has_wifi')),
                        has_sockets=bool    (request.form.get('has_sockets')),
                        can_take_calls=bool(request.form.get('can_take_calls')),
                        coffee_price=request.form.get('coffee_price'))
        with Session(app):
            db.session.add(new_cafe)
            db.session.commit()

    except Exception as err:
        error = error_dict(err)

        return jsonify(error)

    else:
        success = {}
        success['response'] = "Successfully added new cafe."

        return jsonify(success)


@app.route("/update-price", methods=['PATCH'])
def update_price():
    id = request.args.get('id')
    with Session(app):
        desired_cafe = db.session.get(Cafe, id)

        if desired_cafe is not None:
            desired_cafe.coffee_price = request.args.get('new_price')
            db.session.commit()
            success = {}
            success['success'] = "Coffee price updated successfully."

            return jsonify(success), 200
        else:
            error = error_dict("No cafe record exists with that ID.")

            return jsonify(error), 404


@app.route("/report-closure", methods=['DELETE'])
def delete_cafe():
    id = request.args.get('id')
    api_key = request.args.get('api_key')
    with Session(app):
        undesired_cafe = db.session.get(Cafe, id)
        if undesired_cafe is None:
            error = error_dict("No cafe record exists with that ID.")

            return jsonify(error), 404

        elif api_key != API_KEY:
            error = error_dict("Please enter the valid API key to remove the cafe.")

            return jsonify(error), 403

        else:
            db.session.delete(undesired_cafe)
            db.session.commit()
            success = {}
            success['response'] = "Successfully removed cafe."

            return jsonify(success), 200



def create_dict(cafe):
    cafe_dict = {}
    cafe_dict["id"] = cafe.id
    cafe_dict["name"] = cafe.name
    cafe_dict["map_url"] = cafe.map_url
    cafe_dict["img_url"] = cafe.img_url
    cafe_dict["location"] = cafe.location
    cafe_dict["seats"] = cafe.seats
    cafe_dict["has_toilet"] = cafe.has_toilet
    cafe_dict["has_wifi"] = cafe.has_wifi
    cafe_dict["has_sockets"] = cafe.has_sockets
    cafe_dict["can_take_calls"] = cafe.can_take_calls
    cafe_dict["coffee_price"] = cafe.coffee_price

    return cafe_dict


def error_dict(exc):
    error = {}
    error['error'] = f"{exc}"

    return error

if __name__ == "__main__":
    app.run(debug=True)
