from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求，方便前端开发
app.json.ensure_ascii = False

# 模拟数据库里的猫咪数据 (Mock Data)
# 包含了我们在任务书中讨论过的 TNR 状态和健康追踪字段
MOCK_CATS_DB = [
    {
        "id": 1,
        "name": "大橘",
        "color": "橘色",
        "gender": "公",
        "is_neutered": True,  # 是否绝育 (已剪耳)
        "health_status": "健康",  # 健康状态
        "vaccine_status": "已接种",  # 疫苗状态
        "location": "三教楼下",  # 常见活动区域
        "avatar_url": "https://example.com/cat1.jpg",  # 头像占位符
    },
    {
        "id": 2,
        "name": "踏雪",
        "color": "黑白",
        "gender": "母",
        "is_neutered": False,  # 待 TNR
        "health_status": "右腿有轻微擦伤",  # 待医疗救助
        "vaccine_status": "未接种",
        "location": "二食堂后门",
        "avatar_url": "https://example.com/cat2.jpg",
    },
]


# 接口：获取所有流浪猫列表
@app.route("/api/cats", methods=["GET"])
def get_cats():
    return jsonify(
        {"status": "success", "message": "获取猫咪列表成功", "data": MOCK_CATS_DB}
    )


# 接口：根据 ID 获取单只猫咪详细信息
@app.route("/api/cats/<int:cat_id>", methods=["GET"])
def get_cat_detail(cat_id):
    # 用生成器表达式在列表里查找对应 ID 的猫咪
    cat = next((c for c in MOCK_CATS_DB if c["id"] == cat_id), None)

    if cat:
        return jsonify({"status": "success", "data": cat})
    else:
        return jsonify({"status": "error", "message": "未找到该猫咪"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
