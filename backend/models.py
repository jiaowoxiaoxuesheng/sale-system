from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, Index, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ==================== 用户表（用户管理模块）====================
# 角色：consumer（消费者）、farmer（农户商家）、admin（系统管理员）
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="consumer")
    phone = Column(String(20), default="")
    address = Column(String(200), default="")
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    items = relationship('Item', back_populates='owner', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    purchases = relationship('Purchase', back_populates='buyer', cascade='all, delete-orphan', foreign_keys='Purchase.buyer_id')
    reviews = relationship('Review', back_populates='user', cascade='all, delete-orphan')

# ==================== 分类表（商品管理模块）====================
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    items = relationship('Item', back_populates='category')

# ==================== 商品表（商品管理模块）====================
# status: 1=售卖中, 2=已售出, 3=已下架
# stock: 当前库存数量
# origin: 产地（支持多条件检索）
# specification: 规格（如 1kg）
# price_history: JSON格式的调价记录
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    origin = Column(String(100), default="")
    specification = Column(String(100), default="")
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)  # 补货界限
    status = Column(Integer, default=1)
    views = Column(Integer, default=0)
    images = Column(String(1000), default="[]")
    price_history = Column(String(2000), default="[]")
    
    
    
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))

    __table_args__ = (
        Index("ix_item_user_status", "user_id", "status"),
        Index("ix_item_category_status", "category_id", "status"),
        CheckConstraint("price >= 0", name="ck_item_price"),
        CheckConstraint("stock >= 0", name="ck_item_stock"),
        CheckConstraint("status IN (1, 2, 3)", name="ck_item_status"),
    )
    owner = relationship('User', back_populates='items')
    category = relationship('Category', back_populates='items')
    favorited_by = relationship('Favorite', back_populates='item', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='item', cascade='all, delete-orphan')

# ==================== 收藏表====================
class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'))
    
    
    
    created_at = Column(DateTime, default=datetime.now)
    user = relationship('User', back_populates='favorites')
    item = relationship('Item', back_populates='favorited_by')

# ==================== 公告表====================
class Announcement(Base):
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text)
    images = Column(String(1000), default="[]")
    
    
    
    created_at = Column(DateTime, default=datetime.now)

# ==================== 订单表（订单管理模块）====================
# logistics_status: pending=待付款, pending_shipment=待发货, shipped=已发货, completed=已完成, after_sales=售后
# payment_status: unpaid=未付款, paid=已付款
# after_sales_reason: 售后申请原因
class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    seller_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL'))
    item_title = Column(String(100))
    price = Column(Float)
    quantity = Column(Integer, default=1)
    delivery_address = Column(String(200), default="")
    phone = Column(String(20), default="")
    logistics_status = Column(String(20), default="pending")
    logistics_company = Column(String(50), default="")
    tracking_number = Column(String(50), default="")
    payment_status = Column(String(20), default="unpaid")
    after_sales_reason = Column(String(200), default="")
    after_sales_desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("ix_purchase_seller_status", "seller_id", "logistics_status"),
        Index("ix_purchase_buyer_status", "buyer_id", "logistics_status"),
        CheckConstraint("quantity > 0", name="ck_purchase_quantity"),
    )
    buyer = relationship('User', back_populates='purchases', foreign_keys=[buyer_id])
    seller = relationship('User', foreign_keys=[seller_id])
    item = relationship('Item', foreign_keys=[item_id])

# ==================== 评价表（评价反馈模块）====================
# rating: 1-5星评分
# response: 商家回复内容
# deleted_by_admin: 管理员是否强制删除
class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'))
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'))
    rating = Column(Integer, default=5)
    comment = Column(Text)
    response = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    deleted_by_admin = Column(Boolean, default=False)
    responded_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_review_item", "item_id"),
        Index("ix_review_user", "user_id"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
    )
    user = relationship('User', back_populates='reviews')
    item = relationship('Item', back_populates='reviews')
