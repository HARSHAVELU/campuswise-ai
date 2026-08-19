import Link from "next/link";
import type { CourseSummary } from "@/types/api";

export function CourseCard({ course }: { course: CourseSummary }) {
  return (
    <Link
      href={`/courses/${course.id}`}
      className="block rounded-lg border border-slate-200 p-4 hover:border-brand hover:shadow-sm"
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-semibold text-slate-900">{course.code}</span>
        <span className="text-xs uppercase tracking-wide text-slate-400">
          {course.department.code} · {course.credit_hours} cr · {course.level}
        </span>
      </div>
      <h3 className="mt-1 text-base font-medium text-slate-800">{course.title}</h3>
      {course.topics.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {course.topics.map((t) => (
            <span
              key={t.topic}
              className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-brand"
            >
              {t.topic}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
