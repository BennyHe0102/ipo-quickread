export const dynamic = "force-dynamic";

type Filing = {
  cik?: string; company_name?: string; form?: string; accession?: string;
  filing_date?: string; filing_url?: string; doc_primary_url?: string; status?: string;
};

async function fetchFilings(): Promise<Filing[]> {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
  const res = await fetch(`${base}/filings`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export default async function EmbedPage() {
  const data = await fetchFilings();
  return (
    <main className="min-h-screen bg-white text-gray-900 p-6">
      <h1 className="text-2xl font-bold mb-4">IPO QuickRead — Embedded</h1>
      {data.length === 0 ? (
        <div className="text-gray-500">暂无数据</div>
      ) : (
        <ul className="space-y-3">
          {data.map((f, i) => (
            <li key={`${f.accession}-${i}`} className="border rounded-xl p-4">
              <div className="font-semibold">{f.company_name || "Unknown Company"}</div>
              <div className="text-sm">Form: {f.form} · Accession: {f.accession}</div>
              <div className="text-sm">Date: {f.filing_date}</div>
              <div className="text-sm">
                Primary Doc: <a className="underline" href={f.doc_primary_url || "#"} target="_blank">{f.doc_primary_url || "N/A"}</a>
              </div>
              <div className="text-xs text-gray-500">Status: {f.status}</div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
