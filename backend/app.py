import os
from collections import defaultdict
from functools import wraps
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import ADMIN_PASSWORD, ADMIN_TOKEN

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
INSTANCE_DIR = os.path.join(PROJECT_ROOT, "instance")

app = Flask(__name__, instance_path=INSTANCE_DIR)
CORS(app)

# 本地开发：使用 SQLite
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "campus_cat.db").replace("\\", "/")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"

# 生产环境：连接 MySQL
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     "mysql+pymysql://root:ZZAswr05%40@127.0.0.1:3306/campus_cat_db"
# )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(255), default="")
    nickname = db.Column(db.String(50), default="")
    experience = db.Column(db.Integer, default=0)

    LEVEL_THRESHOLDS = [0, 50, 100, 200, 350, 850]
    LEVEL_COLORS = ["#fff", "#4caf50", "#2196f3", "#9c27b0", "#f44336", "#ffd700"]

    def compute_level(self):
        exp = self.experience or 0
        lv = 1
        for threshold in self.LEVEL_THRESHOLDS:
            if exp >= threshold:
                lv = self.LEVEL_THRESHOLDS.index(threshold) + 1
        return min(lv, 6)

    def add_experience(self, amount):
        old_lv = self.compute_level()
        self.experience = (self.experience or 0) + amount
        new_lv = self.compute_level()
        db.session.add(self)
        return {"leveled_up": new_lv > old_lv, "new_level": new_lv}


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
            "audit_status": self.audit_status,
            "user_id": self.user_id,
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


class LedgerFund(db.Model):
    """救助基金余额表"""
    __tablename__ = "ledger_fund"
    id = db.Column(db.Integer, primary_key=True)
    total_balance = db.Column(db.Numeric(10, 2), default=0.00)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {"total_balance": str(self.total_balance)}


class LedgerInventory(db.Model):
    """物资库存表"""
    __tablename__ = "ledger_inventory"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    count = db.Column(db.String(20), nullable=False)      # 字符串展示，如5kg，12支，半瓶
    unit = db.Column(db.String(10))                       # 单位
    quantity = db.Column(db.Float, default=0)             # 库存数量
    alert_threshold = db.Column(db.Float, default=0)      # 临界值
    updated_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        quantity = float(self.quantity or 0)
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count,
            "unit": self.unit or "",
            "quantity": quantity,
            "alert_threshold": float(self.alert_threshold or 0),
            "isAlert": quantity <= float(self.alert_threshold or 0)
                if float(self.alert_threshold or 0) > 0 else False,
        }


class LedgerTransaction(db.Model):
    """账目流水表，每笔账单的收入/支出"""
    __tablename__ = "ledger_transactions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    desc = db.Column(db.String(200), nullable=False)       # 描述
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 金额
    type = db.Column(db.String(10), nullable=False)        # income / expense
    invoice_url = db.Column(db.String(255), default="")    # 凭证图片URL
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "desc": self.desc,
            "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "amount": str(self.amount),
            "type": self.type,
            "invoiceUrl": self.invoice_url or "",
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


def get_required_int(data, key):
    value = data.get(key)
    if value in (None, ""):
        raise ValueError(key)
    return int(value)


def get_required_float(data, key):
    value = data.get(key)
    if value in (None, ""):
        raise ValueError(key)
    return float(value)


def format_inventory_count(quantity, unit=""):
    if float(quantity).is_integer():
        quantity_text = str(int(quantity))
    else:
        quantity_text = str(quantity)
    return f"{quantity_text}{unit or ''}"


def get_or_create_fund():
    fund = LedgerFund.query.first()
    if not fund:
        fund = LedgerFund(total_balance=0)
        db.session.add(fund)
    return fund


def create_ledger_transaction(desc, amount, trans_type, invoice_url="", user_id=None):
    transaction = LedgerTransaction(
        desc=desc,
        amount=amount,
        type=trans_type,
        invoice_url=invoice_url,
        user_id=user_id,
    )
    db.session.add(transaction)

    fund = get_or_create_fund()
    current_balance = float(fund.total_balance or 0)
    if trans_type == "income":
        fund.total_balance = current_balance + amount
    else:
        fund.total_balance = current_balance - amount
    fund.updated_at = datetime.now()

    return transaction, fund


def adjust_inventory(item_name, amount, operate, unit="", remark=""):
    item_name = (item_name or "").strip()
    if not item_name or amount <= 0 or operate not in (1, 2):
        raise ValueError("invalid params")

    item = LedgerInventory.query.filter_by(name=item_name).first()
    if not item:
        item = LedgerInventory(
            name=item_name,
            count="0",
            unit=unit or "",
            quantity=0,
            alert_threshold=0,
        )
        db.session.add(item)

    current_quantity = float(item.quantity or 0)
    if operate == 1:
        item.quantity = current_quantity + amount
    else:
        if current_quantity < amount:
            raise ValueError("insufficient stock")
        item.quantity = current_quantity - amount

    item.count = format_inventory_count(float(item.quantity or 0), item.unit)
    item.updated_at = datetime.now()
    return item


def get_admin_token_from_request():
    token = request.headers.get("X-Admin-Token")
    if token:
        return token

    if request.is_json:
        data = request.get_json(silent=True) or {}
        return data.get("admin_token")

    return request.form.get("admin_token") or request.args.get("admin_token")


def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if get_admin_token_from_request() != ADMIN_TOKEN:
            return jsonify({"status": "error", "message": "unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


def ensure_legacy_schema():
    """Keep old SQLite databases compatible after adding ledger / user columns."""
    inspector = inspect(db.engine)

    # --- ledger_inventory 迁移 ---
    if inspector.has_table("ledger_inventory"):
        columns = {column["name"] for column in inspector.get_columns("ledger_inventory")}
        migrations = {
            "unit": "ALTER TABLE ledger_inventory ADD COLUMN unit VARCHAR(10)",
            "quantity": "ALTER TABLE ledger_inventory ADD COLUMN quantity FLOAT DEFAULT 0",
            "alert_threshold": "ALTER TABLE ledger_inventory ADD COLUMN alert_threshold FLOAT DEFAULT 0",
            "updated_at": "ALTER TABLE ledger_inventory ADD COLUMN updated_at DATETIME",
        }
        for column, sql in migrations.items():
            if column not in columns:
                db.session.execute(text(sql))

    # --- users 迁移：avatar_url / nickname / experience ---
    if inspector.has_table("users"):
        user_cols = {col["name"] for col in inspector.get_columns("users")}
        user_migrations = {
            "avatar_url": "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255) DEFAULT ''",
            "nickname": "ALTER TABLE users ADD COLUMN nickname VARCHAR(50) DEFAULT ''",
            "experience": "ALTER TABLE users ADD COLUMN experience INTEGER DEFAULT 0",
        }
        for col, sql in user_migrations.items():
            if col not in user_cols:
                db.session.execute(text(sql))

    db.session.commit()


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "success",
        "message": "backend running",
        "database": DB_PATH,
    })


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

    # ---- 阳光账本种子数据 ----

    fund = LedgerFund(total_balance=1250.00)
    db.session.add(fund)

    inventory_seed = [
        LedgerInventory(name="幼猫猫粮",   count="5kg",   unit="kg", quantity=5,   alert_threshold=2),
        LedgerInventory(name="成猫猫粮",   count="0.5kg", unit="kg", quantity=0.5, alert_threshold=2),
        LedgerInventory(name="驱虫药",     count="12支",  unit="支", quantity=12,  alert_threshold=3),
        LedgerInventory(name="豆腐猫砂",   count="1袋",   unit="袋", quantity=1,   alert_threshold=2),
        LedgerInventory(name="鸡肉主食罐", count="35罐",  unit="罐", quantity=35,  alert_threshold=10),
        LedgerInventory(name="营养猫条",   count="120支", unit="支", quantity=120, alert_threshold=30),
        LedgerInventory(name="诱捕笼",     count="2个",   unit="个", quantity=2,   alert_threshold=1),
        LedgerInventory(name="外伤碘伏",   count="半瓶",  unit="瓶", quantity=0.5, alert_threshold=1),
    ]
    db.session.add_all(inventory_seed)

    txn_seed = [
        LedgerTransaction(desc="购买成猫猫粮",   amount=150, type="expense",
                          invoice_url="/api/uploads/demo_invoice_1.jpg"),
        LedgerTransaction(desc="张同学爱心捐赠", amount=50,  type="income",
                          invoice_url="/api/uploads/demo_invoice_2.jpg"),
    ]
    db.session.add_all(txn_seed)

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
    new_user = User(username=username, password=hashed_password, nickname=username)

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
        _maybe_add_exp(user_id, 10)  # 认领喂养 +10经验
    elif action == "cancel":
        if current_claimer != user_id:
            return jsonify({"status": "error"}), 403
        setattr(cat, f"{meal}_claimer", "")

    db.session.commit()
    return jsonify(
        {"status": "success", "new_claimer": getattr(cat, f"{meal}_claimer")}
    )

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
                "cat_id": cat.id,
                "time": 1,
                "location": cat.location,
                "desc": cat.character_desc,
                "avatar_url": cat.avatar_url,
                "audit_status": cat.audit_status,
            }
            for cat in cats
        ],
    })

# ===================== 喂养排班历史 API =====================

@app.route("/api/cats/feeding/schedule", methods=["GET"])
def get_feeding_schedule():
    """历史喂养排班：按日期聚合，每日每猫一条，分页10条，倒序"""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    cats = Cat.query.filter_by(audit_status="published").all()

    # 收集所有喂养记录，按 (cat_id, date) 聚合
    daily_map = defaultdict(lambda: {
        "cat": None,
        "date": "",
        "morning_user": "",
        "morning_username": "",
        "noon_user": "",
        "noon_username": "",
        "evening_user": "",
        "evening_username": "",
    })

    for cat in cats:
        records = FeedingRecord.query.filter_by(cat_id=cat.id)\
            .order_by(FeedingRecord.created_at.desc()).all()
        # 按日期分组该猫的记录
        cat_dates = defaultdict(list)
        for r in records:
            date_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
            cat_dates[date_str].append(r)

        for date_str, recs in cat_dates.items():
            key = (cat.id, date_str)
            entry = daily_map[key]
            entry["cat"] = cat
            entry["date"] = date_str
            for rec in recs:
                user = User.query.get(rec.user_id)
                uname = user.username if user else "unknown"
                uid = str(rec.user_id) if rec.user_id else ""
                if rec.time == 1:  # morning
                    entry["morning_user"] = uid
                    entry["morning_username"] = uname
                elif rec.time == 2:  # noon
                    entry["noon_user"] = uid
                    entry["noon_username"] = uname
                elif rec.time == 3:  # evening
                    entry["evening_user"] = uid
                    entry["evening_username"] = uname

    # 也添加没有任何喂养记录的猫和日期
    # 但至少要有认领记录才显示

    # 转换为列表并按日期倒序排序
    schedule_list = []
    admin_id = str(ADMIN_TOKEN)  # admin token as identifier

    for key, entry in daily_map.items():
        cat = entry["cat"]
        if not cat:
            continue
        # 确定每餐的认领者
        ms = cat.morning_claimer or ""
        ns = cat.noon_claimer or ""
        es = cat.evening_claimer or ""

        def claimer_info(claimer_id):
            if not claimer_id:
                return {"user_id": "", "username": "", "status": "none"}
            user = User.query.get(int(claimer_id)) if claimer_id.isdigit() else None
            is_admin_user = user and user.is_admin
            return {
                "user_id": claimer_id,
                "username": user.username if user else claimer_id,
                "status": "admin" if is_admin_user else "claimed",
            }

        schedule_list.append({
            "cat_id": cat.id,
            "cat_name": cat.name,
            "cat_avatar": cat.avatar_url or "",
            "date": entry["date"],
            "morning": {
                "feed_user": entry["morning_username"] or "",
                "feed_user_id": entry["morning_user"] or "",
                "claimer": claimer_info(ms),
            },
            "noon": {
                "feed_user": entry["noon_username"] or "",
                "feed_user_id": entry["noon_user"] or "",
                "claimer": claimer_info(ns),
            },
            "evening": {
                "feed_user": entry["evening_username"] or "",
                "feed_user_id": entry["evening_user"] or "",
                "claimer": claimer_info(es),
            },
        })

    # 按日期倒序
    schedule_list.sort(key=lambda x: x["date"], reverse=True)

    total = len(schedule_list)
    start = (page - 1) * limit
    end = start + limit
    page_data = schedule_list[start:end]

    return jsonify({
        "status": "success",
        "data": page_data,
        "pagination": {"page": page, "limit": limit, "total": total},
    })


# ===================== 用户认领历史 API =====================

@app.route("/api/user/claims", methods=["GET"])
def get_user_claims():
    """获取用户历史上认领过的喂养记录"""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "missing user_id"}), 400

    user_id_str = str(user_id)
    # 查找该用户认领过的猫（claimer字段匹配）
    all_cats = Cat.query.filter_by(audit_status="published").all()
    claimed_records = []

    for cat in all_cats:
        for meal_key, meal_name in [("morning", "早餐"), ("noon", "午餐"), ("evening", "晚餐")]:
            claimer = getattr(cat, f"{meal_key}_claimer") or ""
            if claimer == user_id_str or claimer == str(user_id):
                # 查找该时段是否有实际喂养记录
                time_map = {"morning": 1, "noon": 2, "evening": 3}
                feed_rec = FeedingRecord.query.filter_by(
                    cat_id=cat.id, user_id=user_id, time=time_map[meal_key]
                ).order_by(FeedingRecord.created_at.desc()).first()

                claimed_records.append({
                    "cat_id": cat.id,
                    "cat_name": cat.name,
                    "cat_avatar": cat.avatar_url or "",
                    "meal": meal_key,
                    "meal_name": meal_name,
                    "fed": feed_rec is not None,
                    "food": feed_rec.food if feed_rec else "",
                    "water": feed_rec.water if feed_rec else "",
                    "feed_time": feed_rec.created_at.isoformat() if feed_rec and feed_rec.created_at else "",
                })

    # 按喂养时间倒序
    claimed_records.sort(key=lambda x: x["feed_time"], reverse=True)

    return jsonify({"status": "success", "data": claimed_records})


# ===================== 用户经验/等级 API =====================

@app.route("/api/user/experience", methods=["GET"])
def get_user_experience():
    """获取用户经验值和等级信息"""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "missing user_id"}), 400

    user = User.query.get_or_404(user_id)
    level = user.compute_level()
    exp = user.experience or 0

    # 计算当前等级进度
    thresholds = User.LEVEL_THRESHOLDS
    if level >= 6:
        current_threshold = thresholds[-1]
        next_threshold = current_threshold
        progress = 100
    else:
        current_threshold = thresholds[level - 1] if level > 0 else 0
        next_threshold = thresholds[level] if level < 6 else thresholds[-1]
        if next_threshold > current_threshold:
            progress = int((exp - current_threshold) / (next_threshold - current_threshold) * 100)
        else:
            progress = 100

    colors = User.LEVEL_COLORS

    return jsonify({
        "status": "success",
        "data": {
            "level": level,
            "experience": exp,
            "current_threshold": current_threshold,
            "next_threshold": next_threshold,
            "progress": progress,
            "level_color": colors[level - 1] if 0 < level <= 6 else "#fff",
            "thresholds": thresholds,
            "colors": colors,
        },
    })


# ===================== 经验值增加辅助 =====================

def _maybe_add_exp(user_id, amount):
    """给用户加经验值，如果 user_id 有效"""
    if not user_id:
        return None
    try:
        user = User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None
    if not user or user.is_admin:
        return None
    return user.add_experience(amount)

@app.route("/api/user/profile", methods=["GET", "PUT"])
def handle_user_profile():
    """获取或更新用户个人资料"""
    if request.method == "GET":
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"status": "error", "message": "missing user_id"}), 400
        user = User.query.get_or_404(user_id)
        return jsonify({
            "status": "success",
            "data": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname or user.username,
                "avatar_url": user.avatar_url or "",
            }
        })

    if request.method == "PUT":
        data = request.json or {}
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "missing user_id"}), 400
        user = User.query.get_or_404(int(user_id))
        if "nickname" in data and data["nickname"].strip():
            user.nickname = data["nickname"].strip()
        db.session.commit()
        return jsonify({"status": "success"})


@app.route("/api/user/avatar", methods=["POST"])
def upload_user_avatar():
    """上传用户头像（支持裁剪后的图片）"""
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "missing user_id"}), 400
    user = User.query.get_or_404(int(user_id))

    uploaded_url = save_uploaded_image("image")
    if not uploaded_url:
        return jsonify({"status": "error", "message": "未选择文件"}), 400

    # 删除旧头像文件（仅当是本地文件时）
    if user.avatar_url and "/api/uploads/" in user.avatar_url:
        old_filename = user.avatar_url.rsplit("/", 1)[-1]
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    user.avatar_url = uploaded_url
    db.session.commit()
    return jsonify({"status": "success", "avatar_url": uploaded_url})


@app.route("/api/user/password", methods=["PUT"])
def change_user_password():
    """修改用户密码（需验证原密码）"""
    data = request.json or {}
    user_id = data.get("user_id")
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not all([user_id, old_password, new_password]):
        return jsonify({"status": "error", "message": "缺少必填项：user_id, old_password, new_password"}), 400

    if len(new_password) < 6:
        return jsonify({"status": "error", "message": "新密码至少6位"}), 400

    user = User.query.get_or_404(int(user_id))

    if not check_password_hash(user.password, old_password):
        return jsonify({"status": "error", "message": "原密码错误"}), 403

    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"status": "success", "message": "密码修改成功"})


@app.route("/api/user/account", methods=["DELETE"])
def delete_user_account():
    """注销账号（需验证密码）"""
    data = request.json or {}
    user_id = data.get("user_id")
    password = data.get("password")

    if not all([user_id, password]):
        return jsonify({"status": "error", "message": "缺少必填项：user_id, password"}), 400

    user = User.query.get_or_404(int(user_id))

    if not check_password_hash(user.password, password):
        return jsonify({"status": "error", "message": "密码错误，无法注销"}), 403

    # 删除用户头像文件
    if user.avatar_url and "/api/uploads/" in user.avatar_url:
        old_filename = user.avatar_url.rsplit("/", 1)[-1]
        old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    # 清理关联数据：提报的猫解除关联、喂养记录删除
    Cat.query.filter_by(user_id=user.id).update({"user_id": None})
    user_id_text = str(user.id)
    Cat.query.filter_by(morning_claimer=user_id_text).update({"morning_claimer": ""})
    Cat.query.filter_by(noon_claimer=user_id_text).update({"noon_claimer": ""})
    Cat.query.filter_by(evening_claimer=user_id_text).update({"evening_claimer": ""})
    FeedingRecord.query.filter_by(user_id=user.id).delete()
    LedgerTransaction.query.filter_by(user_id=user.id).update({"user_id": None})

    db.session.delete(user)
    db.session.commit()
    return jsonify({"status": "success", "message": "账号已注销"})


#管理端
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"status": "error", "message": "invalid admin password"}), 401

    return jsonify({"status": "success", "admin_token": ADMIN_TOKEN})


@app.route("/api/admin/pending_cats", methods=["GET"])
@require_admin
def get_pending_cats():
    cats = Cat.query.filter_by(audit_status="pending").all()
    return jsonify({"status": "success", "data": [c.to_dict() for c in cats]})


@app.route("/api/admin/review_cat", methods=["POST"])
@require_admin
def review_cat():
    data = request.json
    cat_id = data.get("cat_id")
    action = data.get("action")
    cat = Cat.query.get_or_404(cat_id)

    if action == "pass":
        cat.audit_status = "published"
        _maybe_add_exp(cat.user_id, 30)  # 审核通过 +30经验
    elif action == "reject":
        db.session.delete(cat)

    db.session.commit()
    return jsonify({"status": "success"})


@app.route("/api/admin/delete_cat", methods=["POST"])
@require_admin
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
@require_admin
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


# 阳光账本 API

# 管理端
@app.route("/api/admin/bank", methods=["POST"])
@require_admin
def admin_bank():
    if request.is_json:
        data = request.get_json() or {}
        try:
            user_id = get_required_int(data, "user_id")
            operate = get_required_int(data, "operate")
            num = get_required_float(data, "num")
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "invalid params"}), 400

        item_name = (data.get("item") or "").strip()
        remark = (data.get("remark") or "").strip()

        try:
            item = adjust_inventory(
                item_name=item_name,
                amount=num,
                operate=operate,
                unit=data.get("unit", ""),
                remark=remark,
            )
        except ValueError as exc:
            message = str(exc)
            status = 400 if message == "insufficient stock" else 400
            return jsonify({"status": "error", "message": message}), status

        if operate == 1:
            _maybe_add_exp(user_id, 20)  # 捐献物资 +20经验

        db.session.commit()

        return jsonify({
            "status": "success",
            "data": item.to_dict(),
            "meta": {
                "user_id": user_id,
                "operate": operate,
                "num": num,
                "remark": remark,
            }
        })

    form = request.form
    try:
        user_id = get_required_int(form, "user_id")
        amount = get_required_float(form, "num")
        record_type = get_required_int(form, "type")
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "invalid params"}), 400

    remark = (form.get("remark") or "").strip()
    if amount <= 0 or record_type not in (1, 2) or not remark:
        return jsonify({"status": "error", "message": "invalid params"}), 400

    invoice_url = save_uploaded_image("image")
    if not invoice_url:
        return jsonify({"status": "error", "message": "invoice image required"}), 400

    trans_type = "income" if record_type == 1 else "expense"
    transaction, fund = create_ledger_transaction(
        desc=remark,
        amount=amount,
        trans_type=trans_type,
        invoice_url=invoice_url,
        user_id=user_id,
    )

    db.session.commit()
    return jsonify({
        "status": "success",
        "data": transaction.to_dict(),
        "total_balance": str(fund.total_balance),
    })


@app.route("/api/admin/ledger/transactions", methods=["POST"])
@require_admin
def admin_add_ledger_transaction():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        desc = (data.get("desc") or data.get("remark") or "").strip()
        invoice_url = data.get("invoice_url") or data.get("invoiceUrl") or ""
        user_id = data.get("user_id")
        try:
            amount = get_required_float(data, "amount")
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "invalid amount"}), 400
        trans_type = data.get("type")
    else:
        form = request.form
        desc = (form.get("desc") or form.get("remark") or "").strip()
        user_id = form.get("user_id")
        try:
            amount = get_required_float(form, "amount")
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "invalid amount"}), 400

        raw_type = form.get("type")
        if raw_type in ("1", 1):
            trans_type = "income"
        elif raw_type in ("2", 2):
            trans_type = "expense"
        else:
            trans_type = raw_type
        invoice_url = save_uploaded_image("image", "file")

    if amount <= 0 or trans_type not in ("income", "expense") or not desc:
        return jsonify({"status": "error", "message": "invalid params"}), 400
    if not invoice_url:
        return jsonify({"status": "error", "message": "invoice image required"}), 400

    try:
        user_id = int(user_id) if user_id not in (None, "") else None
    except (TypeError, ValueError):
        user_id = None

    transaction, fund = create_ledger_transaction(
        desc=desc,
        amount=amount,
        trans_type=trans_type,
        invoice_url=invoice_url,
        user_id=user_id,
    )
    db.session.commit()

    return jsonify({
        "status": "success",
        "data": transaction.to_dict(),
        "total_balance": str(fund.total_balance),
    })


@app.route("/api/admin/ledger/inventory/adjust", methods=["POST"])
@require_admin
def admin_adjust_ledger_inventory():
    data = request.get_json(silent=True) or {}
    try:
        operate = get_required_int(data, "operate")
        amount = get_required_float(data, "num")
        item = adjust_inventory(
            item_name=data.get("item") or data.get("name"),
            amount=amount,
            operate=operate,
            unit=data.get("unit", ""),
            remark=data.get("remark", ""),
        )
    except (TypeError, ValueError) as exc:
        message = str(exc) if str(exc) else "invalid params"
        return jsonify({"status": "error", "message": message}), 400

    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


# 用户端
@app.route("/api/ledger/overview", methods=["GET"])
def ledger_overview():
    #返回余额 + 库存 + 最近10条流水
    fund = LedgerFund.query.first()
    total_balance = str(fund.total_balance) if fund else "0.00"

    inventory = [item.to_dict() for item in LedgerInventory.query.all()]

    recent = [t.to_dict() for t in LedgerTransaction.query
              .order_by(LedgerTransaction.created_at.desc())
              .limit(10).all()]

    return jsonify({
        "status": "success",
        "data": {
            "total_balance": total_balance,
            "inventory": inventory,
            "recent_transactions": recent,
        }
    })


@app.route("/api/ledger/transactions", methods=["GET"])
def ledger_transactions():
    #分页 + 按类型筛选（可选）
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    trans_type = request.args.get("type", "").strip()

    query = LedgerTransaction.query
    if trans_type in ("income", "expense"):
        query = query.filter_by(type=trans_type)

    total = query.count()
    items = (query
             .order_by(LedgerTransaction.created_at.desc())
             .offset((page - 1) * limit)
             .limit(limit)
             .all())

    return jsonify({
        "status": "success",
        "data": [t.to_dict() for t in items],
        "pagination": {"page": page, "limit": limit, "total": total}
    })


@app.route("/api/ledger/transactions", methods=["POST"])
@require_admin
def add_ledger_transaction():
    # 新增收入/支出记录，并更新总余额
    data = request.json
    desc = data.get("desc")
    amount_raw = data.get("amount")
    trans_type = data.get("type")
    invoice_url = data.get("invoice_url", "")
    user_id = data.get("user_id")

    # 参数校验
    if not all([desc, amount_raw is not None, trans_type]):
        return jsonify({"status": "error", "message": "缺少必填项：desc, amount, type"}), 400
    if trans_type not in ("income", "expense"):
        return jsonify({"status": "error", "message": "type 必须为 income 或 expense"}), 400
    try:
        amount = float(amount_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "amount 必须是有效数字"}), 400

    # 写入流水
    txn = LedgerTransaction(
        desc=desc,
        amount=amount,
        type=trans_type,
        invoice_url=invoice_url,
        user_id=user_id
    )
    db.session.add(txn)

    # 更新余额
    fund = LedgerFund.query.first()
    if not fund:
        fund = LedgerFund(total_balance=0)
        db.session.add(fund)
    if trans_type == "income":
        fund.total_balance = float(fund.total_balance or 0) + amount
    else:
        fund.total_balance = float(fund.total_balance or 0) - amount
    fund.updated_at = datetime.now()

    db.session.commit()
    return jsonify({
        "status": "success",
        "data": txn.to_dict(),
        "total_balance": str(fund.total_balance)
    })


@app.route("/api/ledger/inventory", methods=["POST"])
@require_admin
def add_ledger_inventory():
    # 新增物资
    data = request.json
    name = data.get("name")
    count = data.get("count")
    if not name or not count:
        return jsonify({"status": "error", "message": "缺少必填项：name, count"}), 400

    item = LedgerInventory(
        name=name,
        count=count,
        unit=data.get("unit", ""),
        quantity=float(data.get("quantity", 0)),
        alert_threshold=float(data.get("alert_threshold", 0)),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@app.route("/api/ledger/inventory/<int:item_id>", methods=["PUT"])
@require_admin
def update_ledger_inventory(item_id):
    # 更新库存
    item = LedgerInventory.query.get_or_404(item_id)
    data = request.json
    if "name" in data:
        item.name = data["name"]
    if "count" in data:
        item.count = data["count"]
    if "unit" in data:
        item.unit = data["unit"]
    if "quantity" in data:
        item.quantity = float(data["quantity"])
    if "alert_threshold" in data:
        item.alert_threshold = float(data["alert_threshold"])
    item.updated_at = datetime.now()
    db.session.commit()
    return jsonify({"status": "success", "data": item.to_dict()})


@app.route("/api/ledger/inventory/<int:item_id>", methods=["DELETE"])
@require_admin
def delete_ledger_inventory(item_id):
    # 删除物资
    item = LedgerInventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"status": "success"})


# 凭证图片上传

@app.route("/api/ledger/upload_invoice", methods=["POST"])
@require_admin
def upload_invoice():
    uploaded_url = save_uploaded_image("file")
    if not uploaded_url:
        return jsonify({"status": "error", "message": "未选择文件"}), 400
    return jsonify({"status": "success", "url": uploaded_url})


with app.app_context():
    db.create_all()
    ensure_legacy_schema()


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
