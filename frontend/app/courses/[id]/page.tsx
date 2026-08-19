import Link from "next/link";
import { notFound } from "next/navigation";
import { apiGet, ApiError } from "@/lib/api";
import type { CourseRead, SectionRead } from "@/types/api";

function formatTime(time: string): string {
  const parts = time.split(":").map(Number);
  const hours = parts[0] ?? 0;
  const minutes = parts[1] ?? 0;
  const period = hours >= 12 ? "PM" : "AM";
  const displayHour = hours % 12 === 0 ? 12 : hours % 12;
  return `${displayHour}:${minutes.toString().padStart(2, "0")} ${period}`;
}

const DAY_ABBREV: Record<string, string> = {
  monday: "Mon", tuesday: "Tue", wednesday: "Wed",
  thursday: "Thu", friday: "Fri", saturday: "Sat", sunday: "Sun",
};

export default async function CourseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let course: CourseRead;
  try {
    course = await apiGet<CourseRead>(`/courses/${id}`);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
      notFound();
    }
    throw err;
  }

  let sections: SectionRead[] = [];
  try {
    sections = await apiGet<SectionRead[]>("/sections", { course_id: id, limit: 50 });
  } catch {
    sections = [];
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <Link href="/courses" className="text-sm text-brand hover:underline">
        ← Back to course search
      </Link>

      <div className="mt-4 flex items-baseline justify-between">
        <h1 className="text-2xl font-bold text-slate-900">
          {course.code} — {course.title}
        </h1>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        {course.department.name} · {course.credit_hours} credit hours · {course.level}
      </p>

      {course.topics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {course.topics.map((t) => (
            <span key={t.topic} className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-brand">
              {t.topic}
            </span>
          ))}
        </div>
      )}

      {course.description && <p className="mt-4 text-slate-700">{course.description}</p>}

      <h2 className="mt-10 text-lg font-semibold text-slate-900">Sections</h2>
      {sections.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No sections available for this course.</p>
      ) : (
        <div className="mt-3 divide-y divide-slate-200 rounded-lg border border-slate-200">
          {sections.map((section) => (
            <div key={section.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-900">
                    Section {section.section_number}
                  </span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs uppercase text-slate-600">
                    {section.delivery_mode.replace("_", " ")}
                  </span>
                  <span className="text-xs text-slate-400">{section.term.name}</span>
                </div>
                <div className="mt-1 text-sm text-slate-600">
                  {section.meetings.length > 0
                    ? section.meetings
                        .map((m) => `${DAY_ABBREV[m.day_of_week]} ${formatTime(m.start_time)}–${formatTime(m.end_time)}`)
                        .join(", ")
                    : "No scheduled meeting times"}
                </div>
                <div className="mt-1 text-sm text-slate-500">
                  {section.professor ? (
                    <Link href={`/professors/${section.professor.id}`} className="text-brand hover:underline">
                      {section.professor.name}
                    </Link>
                  ) : (
                    "Professor TBD"
                  )}
                </div>
              </div>
              <div className="text-right text-sm text-slate-500">
                {section.seats_available} / {section.seats_total} seats open
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
