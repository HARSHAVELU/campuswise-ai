import { apiGet, ApiError } from "@/lib/api";
import { ProfessorCard } from "@/components/ProfessorCard";
import type { ProfessorRead } from "@/types/api";

async function fetchProfessors(q: string | undefined, minRating: string | undefined) {
  if (q) {
    return apiGet<ProfessorRead[]>("/professors/search", { q });
  }
  return apiGet<ProfessorRead[]>("/professors", { min_rating: minRating, limit: 50 });
}

export default async function ProfessorsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; min_rating?: string }>;
}) {
  const { q, min_rating } = await searchParams;

  let professors: ProfessorRead[] = [];
  let error: string | null = null;
  try {
    professors = await fetchProfessors(q, min_rating);
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Unable to reach the professor search service.";
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Professor Search</h1>
      <p className="mt-1 text-sm text-slate-500">
        Search by name, or filter by minimum overall rating.
      </p>

      <form method="get" className="mt-6 flex flex-wrap gap-3">
        <input
          type="text"
          name="q"
          defaultValue={q ?? ""}
          placeholder="Search by professor name"
          className="flex-1 rounded-md border border-slate-300 px-4 py-2 text-sm focus:border-brand focus:outline-none"
        />
        <select
          name="min_rating"
          defaultValue={min_rating ?? ""}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
        >
          <option value="">Any rating</option>
          <option value="3.5">3.5+</option>
          <option value="4.0">4.0+</option>
          <option value="4.5">4.5+</option>
        </select>
        <button
          type="submit"
          className="rounded-md bg-brand px-5 py-2 text-sm font-medium text-white hover:bg-brand-light"
        >
          Search
        </button>
      </form>

      <div className="mt-8">
        {error && (
          <p className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            We couldn&apos;t load professor results right now. ({error})
          </p>
        )}
        {!error && professors.length === 0 && (
          <p className="text-sm text-slate-500">No professors matched your search.</p>
        )}
        {!error && professors.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {professors.map((professor) => (
              <ProfessorCard key={professor.id} professor={professor} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
