import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_BASE!;

// Next.js 15 里，searchParams 是 Promise，要先 await
type SP = Record<string, string | string[] | undefined>;

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<SP>;
}) {
  const sp = await searchParams; // 把 Promise 拿到手
  const raw = sp?.acc;
  const acc = Array.isArray(raw) ? raw[0] : raw;

  if (!acc) {
    return (
      <main className="p-6">
        缺少 acc 参数，先回首页选一个吧。
        <div className="mt-2">
          <Link className="text-blue-600 underline" href="/">回到首页</Link>
        </div>
      </main>
    );
  }

  const r = await fetch(`${API}/quickread/${acc}`, { cache: "no-store" });
  if (!r.ok) {
    return (
      <main className="p-6 space-y-3">
        <div>这个 acc 还没有 QuickRead 数据（先回首页看看列表）。</div>
        <Link className="text-blue-600 underline" href="/">回到首页</Link>
      </main>
    );
  }

  const q = await r.json();
  const risks = Array.isArray(q?.risk_top5) ? q.risk_top5 : [];

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-lg font-bold">
        {q?.business_model?.one_liner || "QuickRead"}
      </h1>
      <h2 className="font-semibold">Top 5 风险</h2>
      <ul className="list-disc pl-5">
        {risks.map((item: { title: string }, i: number) => (
          <li key={i}>{item.title}</li>
        ))}
      </ul>
    </main>
  );
}



