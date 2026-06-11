"""
P0优先级 API 测试文件
无需等待前端，直接测试后端逻辑是否可行
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_response(title, resp):
    """格式化打印响应"""
    print(f"\n{'='*60}")
    print(f"【{title}】")
    print(f"{'='*60}")
    print(f"状态码: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(resp.text)

def test_p0_apis():
    print("🚀 开始测试P0优先级API")
    
    # 1️⃣ 初始化数据库
    print("\n\n【第1步】初始化数据库...")
    resp = requests.get(f"{BASE_URL}/api/init_db")
    print_response("初始化数据库", resp)
    
    # 2️⃣ 注册用户
    print("\n\n【第2步】注册测试用户...")
    resp = requests.post(f"{BASE_URL}/api/register", json={
        "username": "test_user_001",
        "password": "123456"
    })
    print_response("注册用户", resp)
    user_id = resp.json().get("user_id")
    print(f"✅ 获得用户ID: {user_id}")
    
    # 3️⃣ 测试 P0-API-1: GET /api/cats - 搜索筛选
    print("\n\n【第3步】测试P0-API-1: 获取猫咪列表 (支持搜索筛选)...")
    
    print("\n  3.1) 获取全部已发布猫咪")
    resp = requests.get(f"{BASE_URL}/api/cats")
    print_response("获取全部猫咪", resp)
    
    print("\n  3.2) 按名字搜索 (search=大橘)")
    resp = requests.get(f"{BASE_URL}/api/cats?search=大橘")
    print_response("搜索大橘", resp)
    
    print("\n  3.3) 按性别筛选 (gender=公)")
    resp = requests.get(f"{BASE_URL}/api/cats?gender=公")
    print_response("筛选公猫", resp)
    
    print("\n  3.4) 按毛色筛选 (color=橘猫)")
    resp = requests.get(f"{BASE_URL}/api/cats?color=橘猫")
    print_response("筛选橘猫", resp)
    
    print("\n  3.5) 综合搜索+筛选+分页 (search=三食堂&gender=公&page=1&limit=5)")
    resp = requests.get(f"{BASE_URL}/api/cats?search=三食堂&gender=公&page=1&limit=5")
    print_response("综合查询", resp)
    
    # 4️⃣ 测试 P0-API-2: GET /api/cats/{id} - 猫咪详情
    print("\n\n【第4步】测试P0-API-2: 获取单只猫咪详情...")
    resp = requests.get(f"{BASE_URL}/api/cats/1")
    print_response("获取猫咪详情(ID=1)", resp)
    
    # 5️⃣ 测试 P0-API-3: GET /api/cats/pending_count - 待审核数量
    print("\n\n【第5步】测试P0-API-3: 获取待审核猫咪数量...")
    resp = requests.get(f"{BASE_URL}/api/cats/pending_count")
    print_response("获取待审核数量(用于红点)", resp)
    
    # 6️⃣ 测试 P0-API-4: POST /api/cats/feeding - 投喂打卡
    print("\n\n【第6步】测试P0-API-4: 记录投喂打卡...")
    resp = requests.post(f"{BASE_URL}/api/cats/feeding", json={
        "user_id": user_id,
        "cat_id": 1,
        "time": 1,  # 早餐
        "food": "猫粮",
        "water": "是"
    })
    print_response("投喂打卡记录", resp)
    
    # 再打一条
    resp = requests.post(f"{BASE_URL}/api/cats/feeding", json={
        "user_id": user_id,
        "cat_id": 1,
        "time": 2,  # 午餐
        "food": "罐头",
        "water": "否"
    })
    print_response("再投喂一条(午餐)", resp)
    
    # 7️⃣ 测试 P0-API-5: GET /api/cats/{id}/feeding - 投喂时间线
    print("\n\n【第7步】测试P0-API-5: 获取投喂时间线...")
    resp = requests.get(f"{BASE_URL}/api/cats/1/feeding")
    print_response("获取猫咪1的投喂时间线", resp)
    
    # 8️⃣ 测试过滤：GET /api/cats/feeding - 获取投喂记录列表
    print("\n\n【第8步】额外: 获取投喂记录列表 (支持按猫咪/用户ID筛选)...")
    
    print("\n  8.1) 获取全部投喂记录")
    resp = requests.get(f"{BASE_URL}/api/cats/feeding")
    print_response("全部投喂记录", resp)
    
    print("\n  8.2) 获取用户的投喂记录 (user_id=1)")
    resp = requests.get(f"{BASE_URL}/api/cats/feeding?user_id={user_id}")
    print_response(f"用户{user_id}的投喂记录", resp)
    
    print("\n  8.3) 获取猫咪的投喂记录 (cat_id=1)")
    resp = requests.get(f"{BASE_URL}/api/cats/feeding?cat_id=1")
    print_response("猫咪1的投喂记录", resp)

    print("\n\n" + "="*60)
    print("✅ P0 优先级 API 测试完成！")
    print("="*60)

if __name__ == "__main__":
    test_p0_apis()
