import Link from "next/link";
import type { ProfessorRead } from "@/types/api";

export function ProfessorCard({ professor }: { professor: ProfessorRead }) {
  return (
    <Link
      href={`/professors/${professor.id}`}
      className="block rounded-lg border border-slate-200 p-4 hover:border-brand hover:shadow-sm"
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-semibold text-slate-900">{professor.name}</span>
        {professor.department && (
          <span className="text-xs uppercase tracking-wide text-slate-400">
            {professor.department.code}
          </span>
        )}
      </div>
      {professor.title && <p className="text-sm text-slate-500">{professor.title}</p>}
      {professor.rating && (
        <div className="mt-2 flex gap-4 text-sm text-slate-700">
          <span>⭐ {professor.rating.overall_rating.toFixed(1)} / 5</span>
          {professor.rating.difficulty_rating !== null && (
            <span>Difficulty: {professor.rating.difficulty_rating.toFixed(1)} / 5</span>
          )}
          {professor.rating.would_take_again_pct !== null && (
            <span>Would take again: {professor.rating.would_take_again_pct.toFixed(0)}%</span>
          )}
        </div>
      )}
    </Link>
  );
}
