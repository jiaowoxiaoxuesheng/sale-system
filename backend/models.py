from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

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

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    items = relationship('Item', back_populates='category')

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    origin = Column(String(100), default="")
    specification = Column(String(100), default="")
    stock = Column(Integer, default=0)
    status = Column(Integer, default=1)
    views = Column(Integer, default=0)
    images = Column(String(1000), default="[]")
    price_history = Column(String(2000), default="[]")
    payment_status = Column(String(20), default="unpaid")
    after_sales_reason = Column(String(200), default="")
    after_sales_desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    owner = relationship('User', back_populates='items')
    category = relationship('Category', back_populates='items')
    favorited_by = relationship('Favorite', back_populates='item', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='item', cascade='all, delete-orphan')

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'))
    payment_status = Column(String(20), default="unpaid")
    after_sales_reason = Column(String(200), default="")
    after_sales_desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    user = relationship('User', back_populates='favorites')
    item = relationship('Item', back_populates='favorited_by')

class Announcement(Base):
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text)
    images = Column(String(1000), default="[]")
    payment_status = Column(String(20), default="unpaid")
    after_sales_reason = Column(String(200), default="")
    after_sales_desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

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
    buyer = relationship('User', back_populates='purchases', foreign_keys=[buyer_id])
    seller = relationship('User', foreign_keys=[seller_id])
    item = relationship('Item', foreign_keys=[item_id])

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'))
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'))
    rating = Column(Integer, default=5)
    comment = Column(Text)
    response = Column(Text, default="")
    payment_status = Column(String(20), default="unpaid")
    after_sales_reason = Column(String(200), default="")
    after_sales_desc = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    deleted_by_admin = Column(Boolean, default=False)
    responded_at = Column(DateTime, nullable=True)
    user = relationship('User', back_populates='reviews')
    item = relationship('Item', back_populates='reviews')
