# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from dotenv import load_dotenv

# 读取 .env（本地开发用；在 Render 上用环境变量）
load_dotenv()

# === 数据库连接（兼容 Postgres 与 SQLite） ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# 自动把 postgres URL 改成 SQLAlchemy + psycopg3 的写法
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# === ORM 定义 ===
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

def seed_demo(db: Session):
    """没有数据时，塞一条 Demo 记录，确保前端首页有东西可点。"""
    exists = db.query(Filing).filter(Filing.accession == "000-000-000").first()
    if not exists:
        db.add(Filing(
            cik="0000000000",
            company_name="Demo Company",
            form="S-1",
            accession="000-000-000",
            filing_date=date.today(),
            filing_url="https://www.sec.gov/ixviewer/doc",
            doc_primary_url="https://www.sec.gov/Archives/edgar/",
            status="ready",
        ))
        db.commit()

# === FastAPI 应用 ===
app = FastAPI(title="IPO QuickRead API", version="0.1.0")

# CORS：允许本地与 Vercel 生产域名
DEFAULT_CORS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ipo-quickread.vercel.app",
    "https://*.vercel.app",
]
# 可通过环境变量追加，逗号分隔
EXTRA = os.getenv("CORS_ORIGINS", "")
if EXTRA:
    DEFAULT_CORS += [o.strip() for o in EXTRA.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    with SessionLocal() as db:
        seed_demo(db)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 健康检查
@app.get("/healthz")
def healthz():
    db_kind = DATABASE_URL.split(":")[0]
    return {"ok": True, "time_utc": datetime.utcnow().isoformat(), "db": db_kind}

@app.get("/health")
def health():
    return {"ok": True}

# === 出参模型 ===
class FilingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cik: Optional[str] = None
    company_name: Optional[str] = None
    form: Optional[str] = None
    accession: Optional[str] = None
    filing_date: Optional[date] = None
    filing_url: Optional[str] = None
    doc_primary_url: Optional[str] = None
    status: Optional[str] = None

# === 路由 ===
@app.get("/filings", response_model=List[FilingOut])
def list_filings(
    form: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Filing)
    if form:
        forms = [f.strip() for f in form.split(",") if f.strip()]
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
    # 先占位，后续接入解析/抓取任务
    return {"message": "accepted", "note": "parser not wired yet"}

# —— QuickRead 示例：只给 Demo acc 返回数据 ——
@app.get("/quickread/{accession}")
def get_quickread(accession: str):
    if accession != "000-000-000":
        raise HTTPException(status_code=404, detail="not ready")

    return {
        "business_model": {
            "one_liner": "我们是一家做IPO示例的公司，用来测试页面展示。",
            "segments": ["示例A", "示例B"],
            "revenue_drivers": ["订阅收入", "一次性服务费"],
            "page_refs": [1],
        },
        "risk_top5": [
            {"title": "客户集中度高", "detail": "前五大客户占比高", "page_refs": [12]},
            {"title": "监管不确定性", "detail": "行业受监管影响", "page_refs": [15]},
            {"title": "毛利率波动", "detail": "新业务初期毛利不稳定", "page_refs": [18]},
            {"title": "募资用途执行风险", "detail": "扩张进度不确定", "page_refs": [20]},
            {"title": "依赖关键供应商", "detail": "更换成本高", "page_refs": [22]},
        ],
        "use_of_proceeds": [
            {"purpose": "研发", "amount_usd": 5_000_000, "percent": 40, "note": "", "page_refs": [25]},
            {"purpose": "市场与销售", "amount_usd": 4_000_000, "percent": 32, "note": "", "page_refs": [26]},
            {"purpose": "营运资金", "amount_usd": 3_000_000, "percent": 24, "note": "", "page_refs": [27]},
        ],
        "offering_terms": {
            "price_range": "$8–$10",
            "shares_offered": 10_000_000,
            "greenshoe": 1_500_000,
            "underwriters": ["Goldman Sachs", "Morgan Stanley"],
            "float_shares": 30_000_000,
            "page_refs": [30],
        },
        "financials": {
            "periods": [
                {
                    "period": "FY2023",
                    "revenue": 120_000_000,
                    "gross_margin": 0.45,
                    "op_income": -3_000_000,
                    "net_income": -4_500_000,
                    "cfo": 2_000_000,
                    "cash": 25_000_000,
                    "debt": 5_000_000,
                }
            ],
            "page_refs": [40],
        },
        "valuation": {
            "ps_low": 2.5,
            "ps_high": 3.0,
            "method": "同行可比PS",
            "assumptions": "TTM收入约$1.2亿",
            "page_refs": [50],
        },
        "meta": {"warnings": [], "extraction_score": 95},
    }

# 本地开发可直接运行：python -m app.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
