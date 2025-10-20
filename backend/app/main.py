from fastapi import FastAPI, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from dotenv import load_dotenv

# 读取 .env
load_dotenv()

# 优先用环境变量，没配就用本地 SQLite 文件
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Filing(Base):
    __tablename__ = "filings"
    id = Column(Integer, primary_key=True, index=True)
    cik = Column(String(20), index=True)
    company_name = Column(String(255), index=True)
    form = Column(String(20), index=True)
    accession = Column(String(50), unique=True, index=True)
    filing_date = Column(Date)
    filing_url = Column(Text)
    doc_primary_url = Column(Text)
    status = Column(String(30), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="IPO QuickRead API", version="0.1.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 初期方便联调，先全放开；上线再收紧到你的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    db_kind = DATABASE_URL.split(":")[0]
    return {"ok": True, "time_utc": datetime.utcnow().isoformat(), "db": db_kind}

class FilingOut(BaseModel):
    # 让 Pydantic 从 ORM 对象读取属性
    model_config = ConfigDict(from_attributes=True)

    cik: Optional[str] = None
    company_name: Optional[str] = None
    form: Optional[str] = None
    accession: Optional[str] = None
    filing_date: Optional[date] = None  # ← 关键：用 date 类型
    filing_url: Optional[str] = None
    doc_primary_url: Optional[str] = None
    status: Optional[str] = None

@app.get("/filings", response_model=List[FilingOut])
def list_filings(
    form: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Filing)
    if form:
        forms = [f.strip() for f in form.split(",")]
        q = q.filter(Filing.form.in_(forms))
    if days:
        since = date.today() - timedelta(days=days)
        q = q.filter(Filing.filing_date >= since)
    return q.order_by(Filing.created_at.desc()).limit(200).all()


@app.post("/ingest", status_code=202)
def ingest(
    accession: Optional[str] = None,
    sec_url: Optional[str] = None,
    upload_id: Optional[str] = None,
    cik: Optional[str] = None,
):
    return {"message": "accepted", "note": "解析器尚未接入，此接口仅占位。"}
