from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:ZZAswr05%40@127.0.0.1:3306/campus_cat_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


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


@app.route("/api/cats", methods=["GET"])
def get_cats():
    cats = Cat.query.filter_by(audit_status="published").all()
    return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})


# 核心接口升级：处理认领与取消，并校验身份
@app.route("/api/cats/<int:cat_id>/feed", methods=["POST"])
def add_cat():
    # 接收前端传来的 JSON 数据
    data = request.json

    # 组装一只新的猫咪模型
    new_cat = Cat(
        name=data.get("name"),
        color=data.get("color"),
        gender=data.get("gender"),
        location=data.get("location"),
        character_desc=data.get("character_desc"),
        health_status=data.get("health_status"),
        # 图片暂时给个默认的占位图，后续我们再专门攻克真实文件上传
        avatar_url="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop",
        # 新提报的猫咪默认是待审核状态
        audit_status="pending",
    )

    # 塞进数据库并保存
    db.session.add(new_cat)
    db.session.commit()

    return jsonify({"status": "success", "message": "档案提报成功，等待审核！"})


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
@app.route("/api/admin/pending", methods=["GET"])
def get_pending_cats():
    # 只查询状态为 pending 的猫咪
    cats = Cat.query.filter_by(audit_status="pending").all()
    return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})


# 2. 执行审核操作 (通过或删除)
@app.route("/api/admin/approve/<int:cat_id>", methods=["POST"])
def approve_cat(cat_id):
    data = request.json
    action = data.get("action")  # 'pass' 或 'reject'
    cat = Cat.query.get_or_404(cat_id)

    if action == "pass":
        cat.audit_status = "published"
        message = f"【{cat.name}】已成功发布到首页"
    else:
        db.session.delete(cat)
        message = f"已拒绝并删除【{cat.name}】的申请"

    db.session.commit()
    return jsonify({"status": "success", "message": message})


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
