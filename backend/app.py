import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename  # 核心：用来安全处理图片文件名
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:ZZAswr05%40@127.0.0.1:3306/campus_cat_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # 如果没有这个文件夹，系统会自动帮你建一个
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


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

    # 核心修改：存认领人的 user_id。如果是空字符串 ''，说明没人认领
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
    db.drop_all()  # 删掉旧表重来
    db.create_all()
    # 模拟数据里，大橘的早餐被 'user_001' 认领了
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
    return jsonify(
        {"status": "success", "message": "数据库重新初始化成功，字段已升级！"}
    )


# === 终极版：同时处理获取(GET)和带图片的新增(POST) ===
@app.route("/api/cats", methods=["GET", "POST"])
def handle_cats():
    # 1. 首页获取猫咪列表 (GET) 保持不变
    if request.method == "GET":
        cats = Cat.query.filter_by(audit_status="published").all()
        return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})

    # 2. 接收包含图片的表单 (POST)
    if request.method == "POST":
        # 因为带了文件，必须用 request.form 来接文字数据
        name = request.form.get("name")
        color = request.form.get("color")
        gender = request.form.get("gender")
        location = request.form.get("location")
        character_desc = request.form.get("character_desc")
        health_status = request.form.get("health_status")

        # 默认占位图（万一没传图片兜底用）
        final_avatar_url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop"

        # 核心：拆包拿图片文件
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            # 净化文件名（防止特殊字符黑客攻击）
            filename = secure_filename(image_file.filename)
            # 拼出文件要存放在你电脑里的绝对路径
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            # 物理保存到文件夹里！
            image_file.save(save_path)
            # 生成可以通过浏览器访问的图片网址
            final_avatar_url = f"http://192.168.43.202:5000/static/uploads/{filename}"

        new_cat = Cat(
            name=name,
            color=color,
            gender=gender,
            location=location,
            character_desc=character_desc,
            health_status=health_status,
            avatar_url=final_avatar_url,  # 存入真实的图片链接
            audit_status="pending",
        )
        db.session.add(new_cat)
        db.session.commit()
        return jsonify({"status": "success", "message": "档案及图片提报成功！"})


def feed_cat(cat_id):
    data = request.json
    meal = data.get("meal")  # morning, noon, evening
    action = data.get("action")  # claim (认领) 或 cancel (取消)
    user_id = data.get("user_id")  # 谁在操作？

    if not user_id:
        return jsonify({"status": "error", "message": "未登录，缺少用户身份"}), 400

    cat = Cat.query.get_or_404(cat_id)

    # 动态获取当前这顿饭是谁认领的
    current_claimer = getattr(cat, f"{meal}_claimer")

    if action == "claim":
        if current_claimer:
            return jsonify(
                {"status": "error", "message": "手慢了，该时段已被他人认领"}
            ), 400
        setattr(cat, f"{meal}_claimer", user_id)
        message = f"成功认领{cat.name}的餐段"

    elif action == "cancel":
        if current_claimer != user_id:
            return jsonify(
                {"status": "error", "message": "无权操作，只能取消自己的认领"}
            ), 403
        setattr(cat, f"{meal}_claimer", "")  # 清空认领人
        message = "已取消认领，时段已重新释放"

    db.session.commit()
    return jsonify(
        {
            "status": "success",
            "message": message,
            "new_claimer": getattr(cat, f"{meal}_claimer"),
        }
    )


# ================= 管理员接口 =================


# 1. 获取所有待审核的猫咪列表
@app.route("/api/admin/pending_cats", methods=["GET"])
def get_pending_cats():
    # 去数据库里捞出所有状态为 'pending' 的猫咪
    cats = Cat.query.filter_by(audit_status="pending").all()
    return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})


# 2. 处理审核通过(pass)或打回(reject)
@app.route("/api/admin/review_cat", methods=["POST"])
def review_cat():
    data = request.json
    cat_id = data.get("cat_id")
    action = data.get("action")

    cat = Cat.query.get_or_404(cat_id)

    if action == "pass":
        cat.audit_status = "published"  # 改为已发布状态，首页就能看到了！
        message = "已通过审核"
    elif action == "reject":
        db.session.delete(cat)  # 垃圾数据直接从数据库删除
        message = "已打回并删除"

    db.session.commit()
    return jsonify({"status": "success", "message": message})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
