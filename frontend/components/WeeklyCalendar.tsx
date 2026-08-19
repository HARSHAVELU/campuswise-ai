import type { SectionRead } from "@/types/api";

const DAYS: { key: string; label: string }[] = [
  { key: "monday", label: "Mon" },
  { key: "tuesday", label: "Tue" },
  { key: "wednesday", label: "Wed" },
  { key: "thursday", label: "Thu" },
  { key: "friday", label: "Fri" },
];

const DAY_START_MINUTES = 8 * 60; // 8 AM
const DAY_END_MINUTES = 21 * 60; // 9 PM
const TOTAL_MINUTES = DAY_END_MINUTES - DAY_START_MINUTES;

const BLOCK_COLORS = [
  "bg-blue-100 border-blue-300 text-blue-900",
  "bg-emerald-100 border-emerald-300 text-emerald-900",
  "bg-amber-100 border-amber-300 text-amber-900",
  "bg-purple-100 border-purple-300 text-purple-900",
  "bg-rose-100 border-rose-300 text-rose-900",
  "bg-cyan-100 border-cyan-300 text-cyan-900",
];

function timeToMinutes(time: string): number {
  const parts = time.split(":").map(Number);
  return (parts[0] ?? 0) * 60 + (parts[1] ?? 0);
}

function formatTime(time: string): string {
  const parts = time.split(":").map(Number);
  const hours = parts[0] ?? 0;
  const minutes = parts[1] ?? 0;
  const period = hours >= 12 ? "PM" : "AM";
  const displayHour = hours % 12 === 0 ? 12 : hours % 12;
  return `${displayHour}:${minutes.toString().padStart(2, "0")} ${period}`;
}

export function WeeklyCalendar({ sections }: { sections: SectionRead[] }) {
  const hourMarks = Array.from(
    { length: Math.floor(TOTAL_MINUTES / 60) + 1 },
    (_, i) => DAY_START_MINUTES + i * 60,
  );

  const asyncSections = sections.filter((s) => s.meetings.length === 0);

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <div className="grid min-w-[600px] grid-cols-[60px_repeat(5,1fr)]">
          <div className="border-b border-r border-slate-200 bg-slate-50" />
          {DAYS.map((day) => (
            <div
              key={day.key}
              className="border-b border-r border-slate-200 bg-slate-50 py-2 text-center text-xs font-semibold uppercase text-slate-500 last:border-r-0"
            >
              {day.label}
            </div>
          ))}

          <div className="relative border-r border-slate-200" style={{ height: TOTAL_MINUTES }}>
            {hourMarks.map((minutes) => (
              <div
                key={minutes}
                className="absolute right-1 -translate-y-2 text-[10px] text-slate-400"
                style={{ top: minutes - DAY_START_MINUTES }}
              >
                {formatTime(`${Math.floor(minutes / 60)}:00`)}
              </div>
            ))}
          </div>

          {DAYS.map((day) => (
            <div
              key={day.key}
              className="relative border-r border-slate-100 last:border-r-0"
              style={{ height: TOTAL_MINUTES }}
            >
              {hourMarks.map((minutes) => (
                <div
                  key={minutes}
                  className="absolute w-full border-t border-slate-100"
                  style={{ top: minutes - DAY_START_MINUTES }}
                />
              ))}
              {sections.map((section, sectionIdx) =>
                section.meetings
                  .filter((m) => m.day_of_week === day.key)
                  .map((meeting, meetingIdx) => {
                    const start = timeToMinutes(meeting.start_time);
                    const end = timeToMinutes(meeting.end_time);
                    const color = BLOCK_COLORS[sectionIdx % BLOCK_COLORS.length];
                    return (
                      <div
                        key={`${section.id}-${meetingIdx}`}
                        className={`absolute left-0.5 right-0.5 overflow-hidden rounded border px-1 py-0.5 text-[11px] leading-tight ${color}`}
                        style={{
                          top: Math.max(0, start - DAY_START_MINUTES),
                          height: Math.max(20, end - start),
                        }}
                        title={`${section.course.code} ${formatTime(meeting.start_time)}–${formatTime(meeting.end_time)}`}
                      >
                        <div className="font-semibold">{section.course.code}</div>
                        <div>
                          {formatTime(meeting.start_time)}–{formatTime(meeting.end_time)}
                        </div>
                      </div>
                    );
                  }),
              )}
            </div>
          ))}
        </div>
      </div>

      {asyncSections.length > 0 && (
        <div className="mt-3 text-sm text-slate-600">
          <span className="font-medium">Online / async (no fixed meeting time):</span>{" "}
          {asyncSections.map((s) => s.course.code).join(", ")}
        </div>
      )}
    </div>
  );
}
