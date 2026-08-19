import type { GradeDistributionResponse } from "@/types/api";

const BUCKET_ORDER = [
  "a_plus", "a", "a_minus",
  "b_plus", "b", "b_minus",
  "c_plus", "c", "c_minus",
  "d_plus", "d", "d_minus",
  "f",
];

const BUCKET_LABELS: Record<string, string> = {
  a_plus: "A+", a: "A", a_minus: "A-",
  b_plus: "B+", b: "B", b_minus: "B-",
  c_plus: "C+", c: "C", c_minus: "C-",
  d_plus: "D+", d: "D", d_minus: "D-",
  f: "F",
};

export function GradeDistributionChart({ stats }: { stats: GradeDistributionResponse }) {
  if (stats.total_students === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
        No historical grade data is available for this professor/course combination.
      </div>
    );
  }

  const maxCount = Math.max(...BUCKET_ORDER.map((b) => stats.bucket_counts[b] ?? 0), 1);

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 rounded-lg bg-slate-50 p-4 text-center sm:grid-cols-5">
        <Stat label="Mean GPA" value={stats.mean_gpa?.toFixed(2) ?? "—"} />
        <Stat label="A-range" value={pct(stats.a_range_pct)} />
        <Stat label="B-range" value={pct(stats.b_range_pct)} />
        <Stat label="C-range" value={pct(stats.c_range_pct)} />
        <Stat label="D/F-range" value={pct(stats.d_or_f_range_pct)} />
      </div>

      <div className="mt-4 flex items-end gap-1.5" style={{ height: 160 }}>
        {BUCKET_ORDER.map((bucket) => {
          const count = stats.bucket_counts[bucket] ?? 0;
          const heightPct = (count / maxCount) * 100;
          return (
            <div key={bucket} className="flex flex-1 flex-col items-center gap-1">
              <div className="flex h-full w-full items-end">
                <div
                  className="w-full rounded-t bg-brand-light"
                  style={{ height: `${heightPct}%` }}
                  title={`${BUCKET_LABELS[bucket]}: ${count} students`}
                />
              </div>
              <span className="text-[10px] text-slate-500">{BUCKET_LABELS[bucket]}</span>
            </div>
          );
        })}
      </div>

      <p className="mt-4 text-xs text-slate-500">
        Based on {stats.total_students} recorded students across {stats.num_terms} term
        {stats.num_terms === 1 ? "" : "s"}
        {stats.withdrawal_pct !== null ? ` (${stats.withdrawal_pct}% withdrawal rate)` : ""}.{" "}
        {stats.disclaimer}
      </p>
    </div>
  );
}

function pct(value: number | null): string {
  return value === null ? "—" : `${value}%`;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-lg font-semibold text-slate-900">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}
