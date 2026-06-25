from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import io
import csv
from sqlalchemy import create_engine, or_, desc, func, extract
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Category, Item, Favorite, Announcement, Purchase, Review
from datetime import datetime, timedelta
import secrets
import jwt
from jwt import PyJWTError
import random
from decimal import Decimal
import shutil
import os

# ==================== 1. 数据库配置 ====================
# ==================== 1. 数据库配置 ====================
# 使用 MySQL 数据库，连接地址为 localhost:3306
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/agricultural_sale"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="校园二手交易平台 - 前后端分离API")

@app.on_event("startup")
def init_default_data():
    """在服务启动时自动初始化外键依赖数据（例如默认的分类），避免前端发布时报 500 外键约束错误引发跨域异常"""
    db = SessionLocal()
    # 初始化默认分类（仅第一次运行时创建）
    if db.query(Category).count() == 0:
        for name in ["蔬菜", "水果", "肉类", "蛋奶", "谷物"]:
            db.add(Category(name=name))
        db.commit()
    # 自动创建管理员账号（admin/123456）
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", password="123456", role="admin"))
        db.commit()
    db.close()

# 挂载静态文件目录用来响应上传的图片
os.makedirs(os.path.join(os.path.dirname(__file__), "uploads"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "uploads")), name="uploads")

# ==================== 跨域请求配置 (CORS) ====================
# 允许前端 Vue 服务器跨域访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据交互模型 (Pydantic Schema) ====================
# 用于 API 请求参数的类型校验
class BuyRequest(BaseModel):
    delivery_address: str = ""
    phone: str = ""
    quantity: int = 1


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# ==================== 4. 订单管理模块 ====================
# 购买、付款、发货、确认收货、售后
@app.post("/api/items/{item_id}/buy")
def buy_item(item_id: int, buy_req: BuyRequest = None, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    buyer = get_current_user(authorization=authorization, db=db)
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item or item.status != 1: raise HTTPException(status_code=400, detail="商品已下架或已售罄")
    if item.stock <= 0: raise HTTPException(status_code=400, detail="库存为零，无法购买")
    qty = buy_req.quantity if buy_req and buy_req.quantity else 1
    if qty < 1: qty = 1
    if item.stock < qty: raise HTTPException(status_code=400, detail="库存不足")
    item.stock -= qty
    if item.stock == 0: item.status = 2
    purchase = Purchase(buyer_id=buyer.id, seller_id=item.user_id, item_id=item_id,
        item_title=item.title, price=item.price, quantity=qty,
        delivery_address=buy_req.delivery_address if buy_req else "",
        phone=buy_req.phone if buy_req else "",
        payment_status="unpaid", logistics_status="pending")
    db.add(purchase); db.commit()
    return {"message": "购买成功，请前往“我的订单”进行付款", "purchase_id": purchase.id}

    delivery_address: str = ""
    phone: str = ""
    quantity: int = 1

# ==================== 2. 数据交互 Schema ====================
class ItemCreate(BaseModel):
    title: str
    description: str
    price: float
    origin: str = ""
    specification: str = ""
    stock: int = 0
    min_stock: int = 0
    category_id: int
    user_id: int
    images: str = "[]" # 接收前端传来的多图JSON结构

class UserAuth(BaseModel):
    username: str
    password: str
    confirm_password: str = ""
    role: str = "consumer"
    phone: str = ""
    address: str = ""

class BatchUpdateStatusRequest(BaseModel):
    item_ids: List[int]
    status: int

# 引入 JWT 进行会话管理
# ==================== JWT 用户认证 ====================
# 用于用户登录状态维护，Token 有效期 7 天
SECRET_KEY = "agricultural_sale_secret_2026"
ALGORITHM = "HS256"

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        payload = jwt.decode(authorization, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的用户凭证")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="凭证已过期或无效，请重新登录")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="无效的用户凭证")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user

# ==================== 身份验证与权限接口 ====================
# ==================== 2. 用户管理模块 ====================
# 注册、登录、权限验证
@app.post("/api/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    # 数据库为空时第一个注册用户自动成为管理员
    is_admin = db.query(User).count() == 0
    new_user = User(username=user.username, password=user.password, role="admin" if is_admin else user.role)
    db.add(new_user)
    db.commit()
    return {"message": "注册成功，请登录"}

@app.post("/api/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户未注册")
    if db_user.password != user.password:
        raise HTTPException(status_code=400, detail="密码错误")
    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    # 生成真实的 JWT token
    payload = {
        "user_id": db_user.id,
        "username": db_user.username,
        "role": db_user.role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "message": "登录成功", 
        "token": token, 
        "user_id": db_user.id, 
        "username": db_user.username,
        "role": db_user.role
    }

@app.post("/api/upload")
def upload_image(file: UploadFile = File(...)):
    """加分项：多图上传"""
    filename = f"{secrets.token_hex(8)}_{file.filename}"
    full_path = os.path.join(os.path.dirname(__file__), "uploads", filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    return {"url": f"http://localhost:8000/uploads/{filename}"}
@app.get("/api/items")
def get_items(
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    """分页查询物品、多条件组合筛选、模糊搜索"""
    query = db.query(Item).filter(Item.status == 1)
    
    if keyword:
        query = query.filter(or_(Item.title.contains(keyword), Item.description.contains(keyword)))
    if category_id:
        query = query.filter(Item.category_id == category_id)
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    if start_date:
        query = query.filter(Item.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Item.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        
    total = query.count()
    items = query.order_by(desc(Item.created_at)).offset((page - 1) * size).limit(size).all()
    
    import json as _json
    result_items = []
    # 优化：批量查询评价统计，避免 N+1 问题
    item_ids = [i.id for i in items]
    review_stats = {}
    if item_ids:
        review_rows = db.query(Review.item_id, func.avg(Review.rating), func.count(Review.id)).filter(
            Review.item_id.in_(item_ids), Review.deleted_by_admin != True
        ).group_by(Review.item_id).all()
        review_stats = {r[0]: (r[1] or 0, r[2]) for r in review_rows}
    for i in items:
        # 计算史低
        try:
            history = _json.loads(i.price_history) if i.price_history else []
        except:
            history = []
        if not history:
            history = [{"price": i.price}]
        lowest = min(h["price"] for h in history)
        is_lowest = i.price <= lowest
        result_items.append({
            "id": i.id, "title": i.title, "price": i.price, "views": i.views, "images": i.images,
            "created_at": i.created_at.strftime("%Y-%m-%d"),
            "category_name": i.category.name if i.category else "默认",
            "owner_name": i.owner.username if i.owner else "未知",
            "avg_rating": review_stats.get(i.id, (0, 0))[0],
        "review_count": review_stats.get(i.id, (0, 0))[1],
        "is_lowest": is_lowest,
            "lowest_price": lowest
        })
    return {
        "total": total,
        "items": result_items
    }

# ==========================================
# 获取单个商品详情接口
# 重点逻辑：我们在获取详情时，通常会给商品的 views(浏览量) 加 1。
# 但是为了防止卖家自己刷浏览量，或者管理员巡查时增加浏览量影响真实数据，
# 我们在这里加入了 Token 解析：如果解析出当前看商品的人是本人或者管理员，
# should_increment 就会被拦截设为 False。
# ==========================================
@app.get("/api/items/{item_id}")
def get_item_detail(item_id: int, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """物品详情，含浏览量防刷拦截机制"""
    token = authorization
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item: raise HTTPException(status_code=404)
    
    # 增加浏览量逻辑：如果不是作者本人且不是管理员，则增加浏览量
    should_increment = True
    if token:
        try:
            import jwt
            payload = jwt.decode(token, "agricultural_sale_secret_2026", algorithms=["HS256"])
            user_id = payload.get("user_id")
            user = db.query(User).filter(User.id == user_id).first()
            if user and (user.role == 'admin' or user.id == int(item.user_id)):
                should_increment = False
        except Exception as e:
            print("Token decode failed:", e)
            
    if should_increment:
        item.views += 1
        db.commit()
    else:
        db.refresh(item)
    
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "status": item.status,
        "origin": item.origin,
        "specification": item.specification,
        "stock": item.stock,
        "views": item.views,
        "images": item.images,
        "created_at": item.created_at.isoformat(),
        "user_id": item.user_id,
        "category_name": item.category.name if item.category else "默认",
        "owner_name": item.owner.username if item.owner else "未知"
    }

@app.put("/api/items/batch-status")
def batch_update_status(req: BatchUpdateStatusRequest, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """批量修改商品状态（管理员可操作所有，普通用户只能操作自己的商品）"""
    # 权限验证：已验证登录即可，管理员可操作所有，普通用户只能操作自己的商品
    user = get_current_user(authorization=authorization, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="无效的用户凭证")
    if user.role == "admin":
        target_items = db.query(Item).filter(Item.id.in_(req.item_ids))
    else:
        target_items = db.query(Item).filter(Item.id.in_(req.item_ids), Item.user_id == user.id)
        if target_items.count() != len(req.item_ids):
            raise HTTPException(status_code=403, detail="只能操作自己发布的商品")
    target_items.update({"status": req.status}, synchronize_session=False)
    db.commit()
    return {"message": "批量更新状态成功"}

# ==================== 3. 商品管理模块 ====================
# 商品的增删改查、上下架、多条件检索
@app.post("/api/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """物品发布"""
    new_item = Item(**item.dict())
    import json
    from datetime import datetime
    new_item.price_history = json.dumps([{"price": new_item.price, "date": datetime.now().strftime("%m-%d %H:%M")}])
    db.add(new_item)
    db.commit()
    return {"message": "发布成功"}

# ==========================================
# 核心技术亮点：真实价格趋势追踪 (编辑物品接口)
# 作用：商品被重新编辑修改价格时，将价格走势记录进数据库，方便前端画出真实的历史【价格走势折线图】
# 逻辑：
# 1. 对比 `old_price` 和 前端传来的新修改由于的区别。
# 2. 如果发生了变动，就把之前的价格、加上当前的新价格，打包成 JSON 格式，比如：
# [{"price": 100, "date": "05-18 10:00"}, {"price": 80, "date": "05-18 12:00"}]
# 3. 把这串 JSON 存进数据库的 price_history 字段里。
# ==========================================
@app.put("/api/items/{item_id}")
def edit_item(item_id: int, item_data: ItemCreate, db: Session = Depends(get_db)):
    """物品编辑 - 带调价记录机制"""
    item = db.query(Item).filter(Item.id == item_id).first()
    old_price = item.price
    for key, value in item_data.dict().items():
        setattr(item, key, value)
        
    if old_price != item.price:
        import json
        from datetime import datetime
        try:
            history = json.loads(item.price_history) if item.price_history else []
        except:
            history = []
            
        if not history:
            history.append({"price": old_price, "date": item.created_at.strftime("%m-%d %H:%M")})
            
        history.append({"price": item.price, "date": datetime.now().strftime("%m-%d %H:%M")})
        item.price_history = json.dumps(history)
        
    db.commit()
    return {"message": "修改成功"}

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item: raise HTTPException(status_code=404, detail='商品不存在')
    if current_user.role != 'admin' and item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='无权操作')
    db.delete(item)
    db.commit()
    return {'message': '删除成功'}
@app.post("/api/favorites")
def toggle_favorite(user_id: int, item_id: int, db: Session = Depends(get_db)):
    """收藏与取消收藏"""
    fav = db.query(Favorite).filter_by(user_id=user_id, item_id=item_id).first()
    if fav:
        db.delete(fav)
        msg = "取消收藏"
    else:
        db.add(Favorite(user_id=user_id, item_id=item_id))
        msg = "收藏成功"
    db.commit()
    return {"message": msg}


@app.get('/api/items/{item_id}/compare')
def compare_price(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item: return {'avg_price': 0, 'min_price': 0}
    category_items = db.query(Item).filter(Item.category_id == item.category_id, Item.status == 1).all()
    if not category_items:
        return {'avg_price': item.price, 'min_price': item.price}
    prices = [i.price for i in category_items]
    return {'avg_price': round(sum(prices)/len(prices), 2), 'min_price': min(prices)}

@app.get('/api/users/{user_id}/favorites')
def get_my_favorites(user_id: int, db: Session = Depends(get_db)):
    """我的收藏列表（附带史低标识）"""
    import json
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    result = []
    for f in favs:
        item = f.item
        item_data = {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "price": item.price,
            "status": item.status,
            "views": item.views,
            "images": item.images,
            "category_id": item.category_id,
            "user_id": item.user_id,
            "created_at": str(item.created_at),
        }
        # 解析 price_history，计算历史最低价
        try:
            history = json.loads(item.price_history) if item.price_history else []
        except:
            history = []
        if not history:
            history = [{"price": item.price, "date": item.created_at.strftime("%m-%d %H:%M")}]
        lowest = min(h["price"] for h in history)
        item_data["is_lowest"] = item.price <= lowest
        item_data["lowest_price"] = lowest
        result.append(item_data)
    return result

@app.get("/api/users/{user_id}/items")
def get_my_publishes(user_id: int, keyword: str = "", origin: str = "", category_id: int = 0, min_price: float = 0, max_price: float = 0, db: Session = Depends(get_db)):
    """我的发布列表（支持多条件检索）"""
    query = db.query(Item).filter(Item.user_id == user_id)
    if keyword:
        query = query.filter(Item.title.contains(keyword))
    if origin:
        query = query.filter(Item.origin.contains(origin))
    if category_id:
        query = query.filter(Item.category_id == category_id)
    if min_price > 0:
        query = query.filter(Item.price >= min_price)
    if max_price > 0:
        query = query.filter(Item.price <= max_price)
    items = query.order_by(desc(Item.created_at)).all()
    return [{
        "id": i.id, "title": i.title, "price": i.price,
        "origin": i.origin or "", "specification": i.specification or "",
        "stock": i.stock or 0, "min_stock": i.min_stock or 0,
        "status": i.status, "views": i.views,
        "images": i.images, "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S") if i.created_at else "",
        "category_id": i.category_id, "user_id": i.user_id,
        "description": i.description or ""
    } for i in items]

@app.get("/api/users/{user_id}/purchases")
def get_my_purchases(user_id: int, db: Session = Depends(get_db)):
    """我的购买列表"""
    purchases = db.query(Purchase).filter(Purchase.buyer_id == user_id).order_by(desc(Purchase.created_at)).all()
    return [{

        "id": p.id,

        "item_id": p.item_id,

        "item_title": p.item_title,

        "price": p.price,

        "quantity": p.quantity or 1,

        "seller_name": p.seller.username if p.seller else "未知",

        "delivery_address": p.delivery_address or "",

        "phone": p.phone or "",

        "payment_status": p.payment_status or "unpaid",

        "logistics_status": p.logistics_status or "pending",

        "logistics_company": p.logistics_company or "",

        "tracking_number": p.tracking_number or "",
        "can_review": p.logistics_status=="completed",
        "reviewed": db.query(Review).filter(Review.purchase_id==p.id).count()>0,

        "after_sales_reason": p.after_sales_reason or "",
        "after_sales_desc": p.after_sales_desc or "",
        "created_at": p.created_at.isoformat()

    } for p in purchases]

@app.get("/api/hot-items")
def get_hot_items(db: Session = Depends(get_db)):
    """加分项：热门商品排行 - 仅显示上架商品"""
    items = db.query(Item).filter(Item.status == 1).order_by(desc(Item.views)).limit(5).all()
    return [{'id': i.id, 'title': i.title, 'price': i.price, 'views': i.views, 'created_at': i.created_at.strftime('%Y-%m-%d') if i.created_at else ''} for i in items]

@app.get("/api/price-trends")
def get_price_trends(db: Session = Depends(get_db)):
    """价格趋势展示 (全局按分类统计平均价格) - 仅统计上架商品"""
    trends = db.query(
        Category.name, 
        func.avg(Item.price).label("avg_price")
    ).join(Item, Category.id == Item.category_id).filter(Item.status == 1).group_by(Category.name).all()
    
    return [{"category_name": t[0], "avg_price": round(t[1] or 0, 2)} for t in trends]

@app.get("/api/price-trends/{category_name}")
def get_category_price_trend(category_name: str, db: Session = Depends(get_db)):
    """类别下随时间变化的折线图价格趋势 - 仅统计上架商品"""
    # 按日期(年-月-日)分组统计平均价格
    items = db.query(
        func.date(Item.created_at).label('date'),
        func.avg(Item.price).label('avg_price')
    ).join(Category, Category.id == Item.category_id)\
     .filter(Category.name == category_name, Item.status == 1)\
     .group_by('date').order_by('date').all()
    
    # 将日期转为字符串，价格保留两位小数
    return [{"date": str(i[0]), "avg_price": round(i[1] or 0, 2)} for i in items]

from fastapi.responses import StreamingResponse
import io

@app.get("/api/export-items")
def export_items(db: Session = Depends(get_db)):
    """加分项：数据导出 (CSV)"""
    items = db.query(Item).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "标题", "描述", "价格", "状态", "浏览量", "发布时间"])
    for item in items:
        writer.writerow([item.id, item.title, item.description, item.price, item.status, item.views, item.created_at.strftime("%Y-%m-%d %H:%M:%S")])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=items_export.csv"}
    )

class CategoryCreate(BaseModel):
    name: str

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    cats = db.query(Category).all()
    return [{'id': c.id, 'name': c.name} for c in cats]

@app.post("/api/categories")
def create_category(data: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：添加分类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    db.add(Category(name=data.name))
    db.commit()
    return {"message": "分类添加成功"}

@app.delete("/api/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：删除分类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404)
    db.delete(cat)
    db.commit()
    return {"message": "分类删除成功"}

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    images: str = "[]"

@app.get("/api/announcements")
def get_announcements(db: Session = Depends(get_db)):
    """获取所有公告(公开)"""
    anns = db.query(Announcement).order_by(desc(Announcement.created_at)).all()
    return [{'id': a.id, 'title': a.title, 'content': a.content, 'images': a.images, 'created_at': a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else ''} for a in anns]

@app.post("/api/announcements")
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：发布公告"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    ann = Announcement(title=data.title, content=data.content, images=data.images)
    db.add(ann)
    db.commit()
    return {"message": "公告发布成功"}

@app.delete("/api/announcements/{ann_id}")
def delete_announcement(ann_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：删除公告"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404)
    db.delete(ann)
    db.commit()
    return {"message": "公告删除成功"}

@app.get("/api/me/{user_id}")
def get_my_info(user_id: int, db: Session = Depends(get_db)):
    """同步刷新用户余额"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404)
    return {"username": user.username, "balance": round(user.balance,2), "role": user.role}

# ====================  数据库 JOIN 查询演示 ====================
@app.get("/api/demo/join-query")
def demo_join_query(db: Session = Depends(get_db)):
    """演示：使用 LEFT JOIN 一次性获取商品及其评价统计"""
    results = db.query(
        Item.id, Item.title, Item.price, Item.stock, Item.status,
        func.coalesce(func.avg(Review.rating), 0).label("avg_rating"),
        func.count(Review.id).label("review_count"),
        Category.name.label("category_name"),
        User.username.label("seller_name")
    ).join(Category, Item.category_id == Category.id
    ).join(User, Item.user_id == User.id
    ).outerjoin(Review, Review.item_id == Item.id
    ).group_by(Item.id
    ).limit(20).all()
    return [{
        "id": r.id, "title": r.title, "price": r.price,
        "stock": r.stock, "status": r.status,
        "avg_rating": float(r.avg_rating), "review_count": r.review_count,
        "category": r.category_name, "seller": r.seller_name
    } for r in results]

# ==================== 7. 管理员模块 ====================
# 分类管理、商品强制下架、账号管理
@app.get("/api/admin/all-items")
def admin_get_all_items(db: Session = Depends(get_db)):
    """管理员：强制查看与管理所有商品"""
    items = db.query(Item).order_by(desc(Item.created_at)).all()
    return [{"id": i.id, "title": i.title, "price": i.price, "status": i.status, "owner_name": i.owner.username if i.owner else "未知"} for i in items]

@app.get("/api/admin/users")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：获取所有用户"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    return [{"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active} for u in db.query(User).all()]

@app.put("/api/admin/users/{user_id}/toggle-status")
def toggle_user_status(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：禁用或解禁账号"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role == 'admin':
        raise HTTPException(status_code=400, detail="不能禁用管理员账号")
    
    user.is_active = not user.is_active
    db.commit()
    return {"message": "操作成功", "is_active": user.is_active}


from openai import OpenAI


# ==================== AI 与 拓展接口 ====================

class AIChatRequest(BaseModel):
    message: str
    item_id: Optional[int] = None

QWEN_API_KEY = "sk-e0f1f3e585924840987d3197ac716c17"
client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

@app.post("/api/ai/chat")
def ai_chat(req: AIChatRequest, db: Session = Depends(get_db)):
    """接入 通义千问API，开启联网搜索实现全网比价"""
    try:
        sys_prompt = """你是农产品电商平台的高级智能导购与“全网比价专家”。你的职责不仅是推销，还要客观地帮用户做决策。已开启实时联网搜索，能获取各大农产品平台的最新价格。
规则：
1. 用户问价格/比价时，**必须联网搜索当前真实的市场价格**，禁止编造或使用旧知识。
2. 将全网均价与本平台的【当前商品】进行对比，帮用户算一笔账（差价多少）。
3. 如果当前商品性价比极高，极力推荐购买；如果本商品较贵，教用户一些选购农产品的“选购建议”。
4. 表现得像一个技术极客+专业客服，语气自然，字数控制在100字左右。"""
        
        if req.item_id:
            item = db.query(Item).filter(Item.id == req.item_id).first()
            if item:
                sys_prompt += f"\n\n【当前正在浏览的商品信息】商品名称：{item.title}，售价：{item.price}元，卖家描述：{item.description}。请根据此信息进行比价和推销。"
                
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": req.message}
            ],
            stream=False,
            max_tokens=300,
            extra_body={"enable_search": True}  # 开启全网实时比价
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        print("千问API Error:", e)
        return {"reply": "哎呀，我的大脑暂时短路啦，可能是网络原因或者API调用失败了。"}

# ===================== 价格走势接口=====================
@app.get("/api/items/{item_id}/price-trend")
def get_price_trend(item_id: int, db: Session = Depends(get_db)):
    """真实获取商品的历史改价记录"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    import json
    try:
        history = json.loads(item.price_history) if item.price_history else []
    except:
        history = []
        
    # 如果商品刚上架没改过价格，history是空的，把创建时间和初始价格作为唯一点
    if not history:
        history = [{"price": item.price, "date": item.created_at.strftime("%m-%d %H:%M")}]
        
    return history




# ========== 付款操作 ==========
# 买家支付订单，商家余额增加
@app.put("/api/purchases/{purchase_id}/pay")
def pay_purchase(purchase_id: int, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    buyer = get_current_user(authorization=authorization, db=db)
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.buyer_id == buyer.id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    if purchase.payment_status != "unpaid": raise HTTPException(status_code=400, detail="已付款")
    purchase.payment_status = "paid"
    purchase.logistics_status = "pending_shipment"
    db.commit()
    return {"message": "付款成功，等待发货"}

# ========== 确认收货 ==========
# 买家确认收到商品，订单变为已完成
@app.put("/api/purchases/{purchase_id}/confirm-received")
def confirm_received(purchase_id: int, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    buyer = get_current_user(authorization=authorization, db=db)
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.buyer_id == buyer.id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    if purchase.logistics_status != "shipped": raise HTTPException(status_code=400, detail="未发货")
    purchase.logistics_status = "completed"
    if purchase.payment_status == "paid":
        seller = db.query(User).filter(User.id == purchase.seller_id).first()
        if seller: seller.balance += purchase.price * (purchase.quantity or 1)
    db.commit()
    return {"message": "已确认收货"}

# ========== 卖家评价管理 ==========
# 商家查看自己商品的评价列表
@app.get("/api/seller/reviews")
def get_seller_reviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    my_items = db.query(Item.id).filter(Item.user_id == current_user.id).subquery()
    reviews = db.query(Review).filter(Review.item_id.in_(my_items)).order_by(desc(Review.created_at)).all()
    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "item_id": r.item_id,
            "item_title": r.item.title if r.item else "",
            "username": r.user.username if r.user else "匿名",
            "rating": r.rating,
            "comment": r.comment,
            "response": r.response or "",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return result

# ========== 单品销售统计 ==========
# 用于商品后台的销售饼图，前5+其他
@app.get("/api/merchant/item-sales/{user_id}")
def get_merchant_item_sales(user_id: int, db: Session = Depends(get_db)):
    """商家单品销售统计（用于饼图）"""
    items = db.query(Item).filter(Item.user_id == user_id).all()
    result = []
    for item in items:
        total_qty = db.query(func.coalesce(func.sum(Purchase.quantity), 0)).filter(
            Purchase.item_id == item.id,
            Purchase.seller_id == user_id
        ).scalar() or 0
        if isinstance(total_qty, Decimal): total_qty = float(total_qty)
        revenue = (item.price or 0) * total_qty
        result.append({"item_id": item.id, "title": item.title[:18], "total_revenue": round(revenue, 2)})
    result.sort(key=lambda x: x["total_revenue"], reverse=True)
    return result

# ==================== 6. 统计分析模块 ====================
# 商家销量统计、单品销售饼图
@app.get("/api/merchant/stats/{user_id}")
def get_merchant_stats(user_id: int, db: Session = Depends(get_db)):
    """商家销售统计"""
    total_products = db.query(Item).filter(Item.user_id == user_id).count()
    active_products = db.query(Item).filter(Item.user_id == user_id, Item.status == 1).count()
    sold_products = db.query(Item).filter(Item.user_id == user_id, Item.status == 2).count()
    sales_data = db.query(Purchase).filter(Purchase.seller_id == user_id).all()
    total_orders = len(sales_data)
    total_revenue = sum((s.price or 0) * (s.quantity or 1) for s in sales_data)
    pending_shipment = sum(1 for s in sales_data if s.logistics_status == "pending_shipment")
    shipped = sum(1 for s in sales_data if s.logistics_status == "shipped")
    completed = sum(1 for s in sales_data if s.logistics_status == "completed")
    # Category breakdown
    cat_stats = db.query(Category.name, func.count(Item.id)).join(Item, Category.id == Item.category_id).filter(Item.user_id == user_id).group_by(Category.name).all()
    return {
        "total_products": total_products,
        "active_products": active_products,
        "sold_products": sold_products,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "pending_shipment": pending_shipment,
        "shipped": shipped,
        "completed": completed,
        "category_stats": [{"name": n, "count": cnt} for n, cnt in cat_stats]
    }

@app.get("/api/orders/stats")
def get_order_stats(db: Session = Depends(get_db)):
    return {
        "total_orders": db.query(Purchase).count(),
        "total_revenue": db.query(func.sum(Purchase.price * Purchase.quantity)).scalar() or 0,
        "pending_orders": db.query(Purchase).filter(Purchase.logistics_status == "pending").count(),
        "pending_shipment": db.query(Purchase).filter(Purchase.logistics_status == "pending_shipment").count(),
        "shipped_orders": db.query(Purchase).filter(Purchase.logistics_status == "shipped").count(),
        "completed_orders": db.query(Purchase).filter(Purchase.logistics_status == "completed").count(),
        "total_users": db.query(User).count(),
        "total_products": db.query(Item).filter(Item.status == 1).count()
    }

# ========== 销售记录 ==========
# 商家查看卖出订单，含物流、售后信息
@app.get("/api/users/{user_id}/sales")
def get_sales(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看")
    sales = db.query(Purchase).filter(Purchase.seller_id == user_id).order_by(desc(Purchase.created_at)).all()
    return [{
        "id": p.id, "item_id": p.item_id,
        "item_title": p.item_title, "price": p.price,
        "quantity": p.quantity or 1,
        "buyer_name": p.buyer.username if p.buyer else "未知",
        "delivery_address": p.delivery_address or "",
        "phone": p.phone or "",
        "logistics_status": p.logistics_status or "pending",
        "logistics_company": p.logistics_company or "",
        "tracking_number": p.tracking_number or "",
        "can_review": p.logistics_status=="completed",
        "reviewed": db.query(Review).filter(Review.purchase_id==p.id).count()>0,
        "after_sales_reason": p.after_sales_reason or "",
        "after_sales_desc": p.after_sales_desc or "",
        "created_at": p.created_at.isoformat()
    } for p in sales]

# ========== Schema ==========
class ReviewCreate(BaseModel):
    item_id: int
    purchase_id: int
    rating: int = 5
    comment: str = ""

class ReviewResponse(BaseModel):
    response: str = ""

class LogisticsUpdate(BaseModel):
    logistics_status: str = ""
    logistics_company: str = ""
    tracking_number: str = ""

# ========== 评价统计 ==========
# 计算商品的平均评分、评价数量
@app.get("/api/reviews/stats/{item_id}")
def get_review_stats(item_id: int, db: Session = Depends(get_db)):
    reviews_list = db.query(Review).filter(Review.item_id == item_id, Review.deleted_by_admin != True).all()
    total = len(reviews_list)
    avg_rating = round(sum(r.rating for r in reviews_list) / total, 1) if total > 0 else 0
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews_list:
        distribution[r.rating] = distribution.get(r.rating, 0) + 1
    return {"avg_rating": avg_rating, "total": total, "distribution": distribution}


# ==================== 5. 评价反馈模块 ====================
# 评分、留言、商家回复、管理员强制删除
@app.get("/api/reviews/{item_id}")
def get_item_reviews(item_id: int, db: Session = Depends(get_db)):
    reviews=db.query(Review).filter(Review.item_id==item_id,Review.deleted_by_admin!=True).order_by(desc(Review.created_at)).all()
    return [{"id":r.id,"user_id":r.user_id,"username":r.user.username if r.user else "匿名","rating":r.rating,"comment":r.comment,"response":r.response or "","created_at":r.created_at.strftime("%Y-%m-%d %H:%M")}for r in reviews]

@app.post("/api/reviews")
def create_review(data:ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase=db.query(Purchase).filter(Purchase.id==data.purchase_id,Purchase.buyer_id==current_user.id).first()
    if not purchase: raise HTTPException(status_code=400,detail="未找到订单")
    existing=db.query(Review).filter(Review.purchase_id==data.purchase_id,Review.deleted_by_admin!=True).first()
    if existing: raise HTTPException(status_code=400,detail="已评价")
    admin_del=db.query(Review).filter(Review.purchase_id==data.purchase_id,Review.deleted_by_admin==True).first()
    if admin_del: raise HTTPException(status_code=400,detail="该评价已被管理员删除")
    db.add(Review(user_id=current_user.id,item_id=data.item_id,purchase_id=data.purchase_id,rating=data.rating,comment=data.comment));db.commit()
    return {"message": "评价成功"}

@app.post("/api/reviews/{review_id}/response")
def respond_review(review_id:int,data:ReviewResponse,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    review=db.query(Review).filter(Review.id==review_id).first()
    if not review: raise HTTPException(status_code=404,detail="评价不存在")
    item=db.query(Item).filter(Item.id==review.item_id,Item.user_id==current_user.id).first()
    if not item and current_user.role!="admin": raise HTTPException(status_code=403,detail="无权回复")
    review.response=data.response;review.responded_at=datetime.now();db.commit()
    return {"message": "回复成功"}

# ========== 物流更新 ==========
# 商家确认发货时填写物流信息，同一运单号不能重复
@app.put("/api/purchases/{purchase_id}/logistics")
def update_logistics(purchase_id:int,data:LogisticsUpdate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    purchase=db.query(Purchase).filter(Purchase.id==purchase_id).first()
    if not purchase: raise HTTPException(status_code=404,detail="订单不存在")
    item=db.query(Item).filter(Item.id==purchase.item_id,Item.user_id==current_user.id).first()
    if not item and current_user.role!="admin": raise HTTPException(status_code=403,detail="无权操作")
    purchase.logistics_status=data.logistics_status
    if data.logistics_company: purchase.logistics_company=data.logistics_company
    if data.tracking_number and data.logistics_company:
        exist=db.query(Purchase).filter(Purchase.logistics_company==data.logistics_company,Purchase.tracking_number==data.tracking_number,Purchase.id!=purchase_id).first()
        if exist: raise HTTPException(status_code=400,detail="该运单号已存在")
    if data.tracking_number: purchase.tracking_number=data.tracking_number
    db.commit()
    return {"message": "物流更新成功"}

# ========== 库存管理 ==========
# 商家在编辑商品时修改库存数量
@app.put("/api/items/{item_id}/stock")
def update_stock(item_id: int, stock: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user.id).first()
    if not item and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作")
    if not item: raise HTTPException(status_code=404, detail="商品不存在")
    item.stock = stock; db.commit()
    return {"message": "库存更新成功", "stock": item.stock}

# ========== 售后处理 ==========
# 商家处理售后申请，处理后订单恢复完成
@app.put("/api/purchases/{purchase_id}/process-after-sales")
def process_after_sales(purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    item = db.query(Item).filter(Item.id == purchase.item_id, Item.user_id == current_user.id).first()
    if not item and current_user.role != "admin": raise HTTPException(status_code=403, detail="无权操作")
    if purchase.logistics_status != "after_sales": raise HTTPException(status_code=400, detail="订单不在售后状态")
    purchase.logistics_status = "completed"
    db.commit()
    return {"message": "售后已处理，订单已完成"}

@app.post("/api/purchases/{purchase_id}/after-sales")
def after_sales(purchase_id: int, reason: str = "", description: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.buyer_id == current_user.id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    purchase.after_sales_reason = reason
    purchase.after_sales_desc = description
    purchase.logistics_status = "after_sales"
    db.commit()
    return {"message": "售后申请已提交"}

# ========== 评价删除 ==========
# 管理员强制删除违规评价，删除后隐藏不显示
@app.delete("/api/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作")
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review: raise HTTPException(status_code=404, detail="评价不存在")
    review.deleted_by_admin=True;review.comment="评价已被管理员删除";db.commit()
    return {"message": "已将评价隐藏"}

# ========== 评价自删除 ==========
# 买家可删除自己的评价，删除后可重新评价
@app.delete("/api/reviews/{review_id}/self")
def self_delete_review(review_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    review=db.query(Review).filter(Review.id==review_id,Review.user_id==current_user.id).first()
    if not review: raise HTTPException(status_code=404,detail="评价不存在")
    db.delete(review);db.commit()
    return {"message": "已删除，可重新评价"}

# ========== 回复删除 ==========
# 商家可删除自己的回复
@app.delete("/api/reviews/{review_id}/response")
def delete_reply(review_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    review=db.query(Review).filter(Review.id==review_id).first()
    if not review: raise HTTPException(status_code=404,detail="评价不存在")
    item=db.query(Item).filter(Item.id==review.item_id,Item.user_id==current_user.id).first()
    if not item and current_user.role!="admin": raise HTTPException(status_code=403,detail="无权操作")
    review.response="";review.responded_at=None;db.commit()
    return {"message": "回复已删除"}
