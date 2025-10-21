import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE!;

type Filing = {
  accession: string;
  company_name: string;
  form: string;
  filing_date: string;
};

async function getRecent() {
  const r = await fetch(`${API}/filings?days=7`, { cache: "no-store" });
  return r.json();
}

export default async function Home() {
  const data = await getRecent();
  const list: Filing[] = Array.isArray(data) ? data : (data?.items ?? []);

  return (
    <main className="p-6">
      <h1 className="text-xl font-bold mb-4">最近文件</h1>
      <ul className="space-y-2">
        {list.map((f) => (
          <li key={f.accession} className="border rounded p-3">
            <div>{f.company_name} · {f.form} · {f.filing_date}</div>
            <Link className="text-blue-600 underline" href={`/embed?acc=${f.accession}`}>
              查看
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}

