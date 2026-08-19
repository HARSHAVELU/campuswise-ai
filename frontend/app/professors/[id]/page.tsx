import Link from "next/link";
import { notFound } from "next/navigation";
import { apiGet, ApiError } from "@/lib/api";
import { GradeDistributionChart } from "@/components/GradeDistributionChart";
import type { GradeDistributionResponse, ProfessorRead } from "@/types/api";

export default async function ProfessorDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let professor: ProfessorRead;
  try {
    professor = await apiGet<ProfessorRead>(`/professors/${id}`);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
      notFound();
    }
    throw err;
  }

  let grades: GradeDistributionResponse | null = null;
  try {
    grades = await apiGet<GradeDistributionResponse>(`/professors/${id}/grades`);
  } catch {
    grades = null;
  }

  const rating = professor.rating;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <Link href="/professors" className="text-sm text-brand hover:underline">
        ← Back to professor search
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-slate-900">{professor.name}</h1>
      <p className="mt-1 text-sm text-slate-500">
        {professor.title ?? "Faculty"}
        {professor.department ? ` · ${professor.department.name}` : ""}
      </p>

      {rating ? (
        <div className="mt-6 grid grid-cols-2 gap-4 rounded-lg bg-slate-50 p-4 sm:grid-cols-4">
          <Stat label="Overall Rating" value={`${rating.overall_rating.toFixed(1)} / 5`} />
          <Stat
            label="Teaching"
            value={rating.teaching_rating !== null ? `${rating.teaching_rating.toFixed(1)} / 5` : "—"}
          />
          <Stat
            label="Difficulty"
            value={rating.difficulty_rating !== null ? `${rating.difficulty_rating.toFixed(1)} / 5` : "—"}
          />
          <Stat
            label="Would Take Again"
            value={rating.would_take_again_pct !== null ? `${rating.would_take_again_pct.toFixed(0)}%` : "—"}
          />
        </div>
      ) : (
        <p className="mt-6 text-sm text-slate-500">No aggregate rating data is available.</p>
      )}
      {rating && (
        <p className="mt-2 text-xs text-slate-400">
          Based on {rating.num_ratings} student-reported ratings. Source: {rating.source_type.replace("_", " ")}.
        </p>
      )}

      <h2 className="mt-10 text-lg font-semibold text-slate-900">Historical Grade Distribution</h2>
      <p className="mt-1 text-sm text-slate-500">Across all recorded courses and terms.</p>
      <div className="mt-3">
        {grades ? (
          <GradeDistributionChart stats={grades} />
        ) : (
          <p className="text-sm text-slate-500">Grade history is not available for this professor.</p>
        )}
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}
