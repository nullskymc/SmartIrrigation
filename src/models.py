"""
数据库模型模块 - 定义数据库表结构
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from src.smart_irrigation.config import config
from src.smart_irrigation.exceptions import DatabaseError

# 创建基类
Base = declarative_base()

class BaseModel(object):
    """所有模型的基类"""
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensorData(Base, BaseModel):
    """传感器数据表"""
    sensor_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    soil_moisture = Column(Float)
    temperature = Column(Float)
    light_intensity = Column(Float)
    rainfall = Column(Float)
    raw_data = Column(JSON)  # 存储原始传感器数据
    
    def __repr__(self):
        return f"<SensorData(id={self.id}, sensor_id='{self.sensor_id}', timestamp='{self.timestamp}')>"


class WeatherData(Base, BaseModel):
    """天气数据表"""
    location = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    condition = Column(String(100))
    precipitation = Column(Float)
    forecast_data = Column(JSON)  # 存储预测数据
    
    def __repr__(self):
        return f"<WeatherData(id={self.id}, location='{self.location}', timestamp='{self.timestamp}')>"


class IrrigationLog(Base, BaseModel):
    """灌溉日志表"""
    event = Column(String(50), nullable=False)  # start, stop, failed
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_planned_seconds = Column(Integer)
    duration_actual_seconds = Column(Integer)
    status = Column(String(50))  # completed, failed, aborted
    message = Column(Text)
    
    def __repr__(self):
        return f"<IrrigationLog(id={self.id}, event='{self.event}', status='{self.status}')>"


class User(Base, BaseModel):
    """用户表"""
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


# 创建数据库引擎和会话工厂
try:
    engine = create_engine(config.get_db_uri())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    raise DatabaseError(f"数据库连接错误: {e}")


def get_db():
    """
    获取数据库会话
    使用方法:
    ```
    db = next(get_db())
    try:
        # 使用db进行操作
        db.commit()
    finally:
        db.close()
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    """
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        raise DatabaseError(f"数据库初始化错误: {e}")


# 通用的CRUD操作
def create_item(db, model, **kwargs):
    """创建记录"""
    db_item = model(**kwargs)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db, model, id):
    """通过ID获取记录"""
    return db.query(model).filter(model.id == id).first()


def get_items(db, model, skip=0, limit=100, **filters):
    """获取多条记录"""
    query = db.query(model)
    for field, value in filters.items():
        if hasattr(model, field):
            query = query.filter(getattr(model, field) == value)
    return query.offset(skip).limit(limit).all()


def update_item(db, model, id, **kwargs):
    """更新记录"""
    db_item = get_item(db, model, id)
    if db_item:
        for key, value in kwargs.items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item


def delete_item(db, model, id):
    """删除记录"""
    db_item = get_item(db, model, id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item