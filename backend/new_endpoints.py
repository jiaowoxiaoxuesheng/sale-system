
# ========== 新 Schema 类 ==========
class ReviewCreate(BaseModel):
    item_id: int
    purchase_id: int
    rating: int = 5
    comment: str = ''

class ReviewResponse(BaseModel):
    response: str

class LogisticsUpdate(BaseModel):
    logistics_status: str
    logistics_company: str = ''
    tracking_number: str = ''

class UserUpdate(BaseModel):
    phone: str = ''
    address: str = ''

class AfterSalesRequest(BaseModel):
    reason: str = ''
    description: str = ''

class PaymentUpdate(BaseModel):
    payment_status: str
# ========== 评价反馈接口 ==========
@app.get("/api/reviews/{item_id}")
def get_item_reviews(item_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.item_id == item_id).order_by(desc(Review.created_at)).all()
    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username if r.user else "匿名",
            "rating": r.rating,
            "comment": r.comment,
            "response": r.response or "",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "responded_at": r.responded_at.strftime("%Y-%m-%d %H:%M") if r.responded_at else ""
        })
    return result

@app.get("/api/reviews/stats/{item_id}")
def get_item_review_stats(item_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.item_id == item_id).all()
    if not reviews:
        return {"avg_rating": 0, "total": 0, "distribution": {1:0, 2:0, 3:0, 4:0, 5:0}}
    ratings = [r.rating for r in reviews]
    dist = {1:0, 2:0, 3:0, 4:0, 5:0}
    for r in ratings: dist[r] = dist.get(r, 0) + 1
    return {
        "avg_rating": round(sum(ratings) / len(ratings), 1),
        "total": len(reviews),
        "distribution": dist
    }

@app.post("/api/reviews")
def create_review(data: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == data.purchase_id, Purchase.buyer_id == current_user.id).first()
    if not purchase: raise HTTPException(status_code=400, detail="未找到该订单或您不是买家")
    existing = db.query(Review).filter(Review.purchase_id == data.purchase_id).first()
    if existing: raise HTTPException(status_code=400, detail="该订单已经评价过了")
    review = Review(user_id=current_user.id, item_id=data.item_id, purchase_id=data.purchase_id, rating=data.rating, comment=data.comment)
    db.add(review); db.commit()
    return {"message": "评价发布成功"}

@app.post("/api/reviews/{review_id}/response")
def respond_review(review_id: int, data: ReviewResponse, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review: raise HTTPException(status_code=404, detail="评价不存在")
    item = db.query(Item).filter(Item.id == review.item_id, Item.user_id == current_user.id).first()
    if not item and current_user.role != "admin": raise HTTPException(status_code=403, detail="只有该商品的商家或管理员可以回复")
    review.response = data.response
    review.responded_at = datetime.now()
    db.commit()
    return {"message": "回复成功"}

# ========== 物流跟踪 ==========
@app.put("/api/purchases/{purchase_id}/logistics")
def update_logistics(purchase_id: int, data: LogisticsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    item = db.query(Item).filter(Item.id == purchase.item_id, Item.user_id == current_user.id).first()
    if not item and current_user.role != "admin": raise HTTPException(status_code=403, detail="只有该商品的商家可以操作")
    purchase.logistics_status = data.logistics_status
    if data.logistics_company: purchase.logistics_company = data.logistics_company
    if data.tracking_number: purchase.tracking_number = data.tracking_number
    db.commit()
    return {"message": "物流信息更新成功"}

@app.get("/api/purchases/{purchase_id}/logistics")
def get_logistics(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    return {
        "logistics_status": purchase.logistics_status,
        "logistics_company": purchase.logistics_company,
        "tracking_number": purchase.tracking_number,
        "delivery_address": purchase.delivery_address,
        "phone": purchase.phone
    }

# ========== 支付状态 ==========
@app.put("/api/purchases/{purchase_id}/payment")
def update_payment(purchase_id: int, data: PaymentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    purchase.payment_status = data.payment_status
    db.commit()
    return {"message": "支付状态更新成功"}

# ========== 库存管理 ==========
@app.put("/api/items/{item_id}/stock")
def update_stock(item_id: int, stock: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id, Item.user_id == current_user.id).first()
    if not item and current_user.role != "admin": raise HTTPException(status_code=403, detail="无权操作")
    if not item: raise HTTPException(status_code=404, detail="商品不存在")
    item.stock = stock; db.commit()
    return {"message": "库存更新成功", "stock": item.stock}

# ========== 个人信息 ==========
@app.put("/api/user/profile")
def update_profile(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.phone = data.phone
    current_user.address = data.address
    db.commit()
    return {"message": "个人信息更新成功"}

# ========== 商家销售订单 ==========
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
        "created_at": p.created_at.isoformat()
    } for p in sales]

# ========== 订单售后 ==========
@app.post("/api/purchases/{purchase_id}/after-sales")
def after_sales(purchase_id: int, data: AfterSalesRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.buyer_id == current_user.id).first()
    if not purchase: raise HTTPException(status_code=404, detail="订单不存在")
    purchase.after_sales_reason = data.reason
    purchase.after_sales_desc = data.description
    purchase.logistics_status = "after_sales"
    db.commit()
    return {"message": "售后申请提交成功"}