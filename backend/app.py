import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:ZZAswr05%40@127.0.0.1:3306/campus_cat_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Cat(db.Model):
    __tablename__ = "cats"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(255))
    color = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    is_neutered = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(100))
    character_desc = db.Column(db.String(50))
    health_status = db.Column(db.String(50))
    audit_status = db.Column(db.String(20), default="pending")
    morning_claimer = db.Column(db.String(100), default="")
    noon_claimer = db.Column(db.String(100), default="")
    evening_claimer = db.Column(db.String(100), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "color": self.color,
            "gender": self.gender,
            "is_neutered": self.is_neutered,
            "location": self.location,
            "character_desc": self.character_desc,
            "health_status": self.health_status,
            "feed_status": {
                "morning": self.morning_claimer,
                "noon": self.noon_claimer,
                "evening": self.evening_claimer,
            },
        }


@app.route("/api/init_db", methods=["GET"])
def init_db():
    db.drop_all()
    db.create_all()
    cat1 = Cat(
        name="大橘",
        color="橘猫",
        gender="公",
        is_neutered=True,
        location="南区三食堂",
        character_desc="亲人贪吃，随便撸",
        health_status="健康偏胖",
        audit_status="published",
        morning_claimer="user_001",
    )
    cat2 = Cat(
        name="踏雪",
        color="奶牛猫",
        gender="母",
        is_neutered=False,
        location="图书馆后花园",
        character_desc="警惕怕生，只可远观",
        health_status="健康",
        audit_status="published",
    )
    db.session.add_all([cat1, cat2])
    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "该账号已被注册"})

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"status": "success", "user_id": new_user.id})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        return jsonify(
            {"status": "success", "user_id": user.id, "username": user.username}
        )

    return jsonify({"status": "error", "message": "账号或密码错误"})


@app.route("/api/cats", methods=["GET", "POST"])
def handle_cats():
    if request.method == "GET":
        cats = Cat.query.filter_by(audit_status="published").all()
        return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})

    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color")
        gender = request.form.get("gender")
        location = request.form.get("location")
        character_desc = request.form.get("character_desc")
        health_status = request.form.get("health_status")
        final_avatar_url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop"

        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            final_avatar_url = f"/api/uploads/{filename}"

        new_cat = Cat(
            name=name,
            color=color,
            gender=gender,
            location=location,
            character_desc=character_desc,
            health_status=health_status,
            avatar_url=final_avatar_url,
            audit_status="pending",
        )
        db.session.add(new_cat)
        db.session.commit()
        return jsonify({"status": "success"})


@app.route("/api/cats/<int:cat_id>/feed", methods=["POST"])
def feed_cat(cat_id):
    data = request.json
    meal = data.get("meal")
    action = data.get("action")
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"status": "error"}), 400

    cat = Cat.query.get_or_404(cat_id)
    current_claimer = getattr(cat, f"{meal}_claimer")

    if action == "claim":
        if current_claimer:
            return jsonify({"status": "error"}), 400
        setattr(cat, f"{meal}_claimer", user_id)
    elif action == "cancel":
        if current_claimer != user_id:
            return jsonify({"status": "error"}), 403
        setattr(cat, f"{meal}_claimer", "")

    db.session.commit()
    return jsonify(
        {"status": "success", "new_claimer": getattr(cat, f"{meal}_claimer")}
    )


@app.route("/api/admin/pending_cats", methods=["GET"])
def get_pending_cats():
    cats = Cat.query.filter_by(audit_status="pending").all()
    return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})


@app.route("/api/admin/review_cat", methods=["POST"])
def review_cat():
    data = request.json
    cat_id = data.get("cat_id")
    action = data.get("action")
    cat = Cat.query.get_or_404(cat_id)

    if action == "pass":
        cat.audit_status = "published"
    elif action == "reject":
        db.session.delete(cat)

    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/admin/delete_cat", methods=["POST"])
def delete_cat():
    data = request.json
    cat_id = data.get("cat_id")
    cat = Cat.query.get_or_404(cat_id)

    if cat.avatar_url:
        file_name = cat.avatar_url.split("/")[-1]
        file_path = os.path.join(app.root_path, "static", "uploads", file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(cat)
    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/admin/update_cat", methods=["POST"])
def update_cat():
    data = request.json
    cat_id = data.get("cat_id")
    cat = Cat.query.get_or_404(cat_id)

    if "name" in data:
        cat.name = data["name"]
    if "location" in data:
        cat.location = data["location"]
    if "character_desc" in data:
        cat.character_desc = data["character_desc"]

    db.session.commit()
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
