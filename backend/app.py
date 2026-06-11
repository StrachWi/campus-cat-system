import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# 本地开发：使用 SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///campus_cat.db"

# 生产环境：连接 MySQL
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "mysql+pymysql://root:ZZAswr05%40@127.0.0.1:3306/campus_cat_db"
# )

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
    is_admin = db.Column(db.Boolean, default=False)


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
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # 记录谁提报的

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


class FeedingRecord(db.Model):
    """投喂打卡记录表"""
    __tablename__ = "feeding_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    cat_id = db.Column(db.Integer, db.ForeignKey("cats.id"), nullable=False)
    time = db.Column(db.Integer, nullable=False)  # 1:早 2:中 3:晚
    food = db.Column(db.String(100), nullable=False)  # 投喂食物
    water = db.Column(db.String(20), default="否")  # "是"/"否"
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        user = User.query.get(self.user_id)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": user.username if user else "unknown",
            "cat_id": self.cat_id,
            "time": self.time,
            "food": self.food,
            "water": self.water,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def save_uploaded_image(*field_names):
    for field_name in field_names:
        image_file = request.files.get(field_name)
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(save_path)
            return f"/api/uploads/{filename}"
    return ""


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
    # print("Content-Type:", request.headers.get('Content-Type'))
    # print("Raw data:", request.get_data(as_text=True))
    
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
        # 支持搜索和筛选
        search = request.args.get("search", "").strip()
        gender = request.args.get("gender", "").strip()
        color = request.args.get("color", "").strip()
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)

        query = Cat.query.filter_by(audit_status="published")

        # 模糊搜索：名字或地点
        if search:
            query = query.filter(
                db.or_(
                    Cat.name.contains(search),
                    Cat.location.contains(search)
                )
            )

        # 按性别筛选
        if gender:
            query = query.filter_by(gender=gender)

        # 按毛色筛选
        if color:
            query = query.filter_by(color=color)

        # 分页
        total = query.count()
        cats = query.offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            "status": "success",
            "data": [c.to_dict() for c in cats],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        })

    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color")
        gender = request.form.get("gender")
        location = request.form.get("location")
        character_desc = request.form.get("character_desc")
        health_status = request.form.get("health_status")
        user_id = request.form.get("user_id")
        final_avatar_url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop"

        uploaded_url = save_uploaded_image("image")
        if uploaded_url:
            final_avatar_url = uploaded_url

        new_cat = Cat(
            name=name,
            color=color,
            gender=gender,
            location=location,
            character_desc=character_desc,
            health_status=health_status,
            avatar_url=final_avatar_url,
            audit_status="pending",
            user_id=user_id
        )
        db.session.add(new_cat)
        db.session.commit()
        return jsonify({"status": "success"})


@app.route("/api/cats/<int:cat_id>", methods=["GET"])
def get_cat_detail(cat_id):
    """获取单只猫咪的详细信息"""
    cat = Cat.query.get_or_404(cat_id)
    return jsonify({"status": "success", "data": cat.to_dict()})


@app.route("/api/cats/pending_count", methods=["GET"])
def get_pending_count():
    """获取待审核的猫咪数量（用于红点角标）"""
    count = Cat.query.filter_by(audit_status="pending").count()
    return jsonify({"status": "success", "count": count})


@app.route("/api/cats/feeding", methods=["POST", "GET"])
def handle_feeding():
    """投喂打卡记录接口"""
    if request.method == "POST":
        # 记录一条投喂打卡
        user_id = request.json.get("user_id")
        cat_id = request.json.get("cat_id")
        time = request.json.get("time")  # 1:早 2:中 3:晚
        food = request.json.get("food")
        water = request.json.get("water", "否")  # 默认不投喂水

        if not all([user_id, cat_id, time, food]):
            return jsonify({"status": "error", "message": "缺少必填项"}), 400

        # 验证猫咪是否存在
        if not Cat.query.get(cat_id):
            return jsonify({"status": "error", "message": "猫咪不存在"}), 404

        record = FeedingRecord(
            user_id=user_id,
            cat_id=cat_id,
            time=time,
            food=food,
            water=water
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({"status": "success", "data": record.to_dict()})

    elif request.method == "GET":
        # 获取投喂记录列表（支持按猫咪ID或用户ID筛选）
        cat_id = request.args.get("cat_id", type=int)
        user_id = request.args.get("user_id", type=int)
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)

        query = FeedingRecord.query

        if cat_id:
            query = query.filter_by(cat_id=cat_id)
        if user_id:
            query = query.filter_by(user_id=user_id)

        # 按时间倒序
        total = query.count()
        records = query.order_by(FeedingRecord.created_at.desc()).offset(
            (page - 1) * limit
        ).limit(limit).all()

        return jsonify({
            "status": "success",
            "data": [r.to_dict() for r in records],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total
            }
        })


@app.route("/api/cats/<int:cat_id>/feeding", methods=["GET"])
def get_cat_feeding_records(cat_id):
    """获取某只猫咪的投喂时间线"""
    # 验证猫咪存在
    if not Cat.query.get(cat_id):
        return jsonify({"status": "error", "message": "猫咪不存在"}), 404

    records = FeedingRecord.query.filter_by(cat_id=cat_id).order_by(
        FeedingRecord.created_at.desc()
    ).all()

    return jsonify({
        "status": "success",
        "data": [r.to_dict() for r in records]
    })


@app.route("/api/user/issued", methods=["GET"])
def get_user_issued_cats():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "missing user_id"}), 400

    cats = Cat.query.filter_by(user_id=user_id).order_by(Cat.id.desc()).all()
    return jsonify({
        "status": "success",
        "data": [
            {
                "cat_name": cat.name,
                "time": 1,
                "location": cat.location,
                "desc": cat.character_desc,
                "avatar_url": cat.avatar_url,
            }
            for cat in cats
        ],
    })


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


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
