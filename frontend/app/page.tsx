import Link from "next/link";
import { apiGet } from "@/lib/api";

async function getBackendHealth(): Promise<{ status: string } | null> {
  try {
    return await apiGet<{ status: string }>("/health");
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const health = await getBackendHealth();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="flex flex-col items-center gap-4">
        <h1 className="text-4xl font-bold text-brand">CampusWise AI</h1>
        <p className="max-w-xl text-lg text-slate-600">
          AI-Powered Course, Professor &amp; Semester Planning Assistant
        </p>
      </div>

      <div className="flex gap-4">
        <Link
          href="/courses"
          className="rounded-md bg-brand px-5 py-2.5 text-white hover:bg-brand-light"
        >
          Search Courses
        </Link>
        <Link
          href="/professors"
          className="rounded-md border border-brand px-5 py-2.5 text-brand hover:bg-blue-50"
        >
          Search Professors
        </Link>
      </div>

      <div className="rounded-lg border border-slate-200 px-4 py-2 text-sm">
        Backend status:{" "}
        <span className={health?.status === "ok" ? "text-green-600" : "text-red-600"}>
          {health?.status === "ok" ? "connected" : "unavailable"}
        </span>
      </div>
    </main>
  );
}
