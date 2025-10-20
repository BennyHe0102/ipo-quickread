from app.main import SessionLocal, Filing
from datetime import date

db = SessionLocal()
db.add(Filing(
    cik="0000000000",
    company_name="Demo Company",
    form="S-1",
    accession="000-000-000",
    filing_date=date.today(),
    filing_url="https://www.sec.gov/ixviewer/doc",
    doc_primary_url="https://www.sec.gov/Archives/edgar/data/...",
    status="demo"
))
db.commit()
db.close()
print("Inserted 1 demo row.")
