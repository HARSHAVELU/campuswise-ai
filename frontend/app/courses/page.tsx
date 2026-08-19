import { apiGet, ApiError } from "@/lib/api";
import { CourseCard } from "@/components/CourseCard";
import type { CourseSummary } from "@/types/api";

async function fetchCourses(q: string | undefined, departmentCode: string | undefined) {
  if (q) {
    return apiGet<CourseSummary[]>("/courses/search", { q });
  }
  return apiGet<CourseSummary[]>("/courses", { department_code: departmentCode, limit: 50 });
}

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; department?: string }>;
}) {
  const { q, department } = await searchParams;

  let courses: CourseSummary[] = [];
  let error: string | null = null;
  try {
    courses = await fetchCourses(q, department);
  } catch (err) {
    error = err instanceof ApiError ? err.message : "Unable to reach the course search service.";
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Course Search</h1>
      <p className="mt-1 text-sm text-slate-500">
        Search by keyword, topic, or course code. Try &ldquo;python&rdquo; or &ldquo;machine
        learning&rdquo;.
      </p>

      <form method="get" className="mt-6 flex gap-3">
        <input
          type="text"
          name="q"
          defaultValue={q ?? ""}
          placeholder="Search courses (e.g. python, database, calculus)"
          className="flex-1 rounded-md border border-slate-300 px-4 py-2 text-sm focus:border-brand focus:outline-none"
        />
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
            We couldn&apos;t load course results right now. ({error})
          </p>
        )}
        {!error && courses.length === 0 && (
          <p className="text-sm text-slate-500">No courses matched your search.</p>
        )}
        {!error && courses.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
