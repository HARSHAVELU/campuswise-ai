"use client";

import { useState } from "react";
import { apiPost, ApiClientError } from "@/lib/api-client";
import { WeeklyCalendar } from "@/components/WeeklyCalendar";
import type { ScheduleGenerateResponse, ScheduleResult } from "@/types/api";

const STRATEGY_ORDER = [
  "best_overall",
  "best_professors",
  "fewest_campus_days",
  "best_grades",
  "online_heavy",
];

export function ScheduleBuilder() {
  const [query, setQuery] = useState("");
  const [minCredits, setMinCredits] = useState(12);
  const [maxCredits, setMaxCredits] = useState(15);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScheduleGenerateResponse | null>(null);
  const [activeStrategy, setActiveStrategy] = useState<string>("best_overall");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<ScheduleGenerateResponse>("/schedule/generate", {
        query,
        min_credits: minCredits,
        max_credits: maxCredits,
      });
      setResult(response);
      const firstAvailable = STRATEGY_ORDER.find((s) => response.schedules[s]);
      setActiveStrategy(firstAvailable ?? "best_overall");
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? `We couldn't generate a schedule right now. (${err.message})`
          : "We couldn't reach the schedule builder service.",
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const activeSchedule: ScheduleResult | null | undefined = result?.schedules[activeStrategy];

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[240px]">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            What do you want your semester to look like?
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. no Friday classes, prefer online, good professors"
            className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Min credits</label>
          <input
            type="number"
            value={minCredits}
            min={1}
            max={30}
            onChange={(e) => setMinCredits(Number(e.target.value))}
            className="w-24 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Max credits</label>
          <input
            type="number"
            value={maxCredits}
            min={1}
            max={30}
            onChange={(e) => setMaxCredits(Number(e.target.value))}
            className="w-24 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-brand px-5 py-2 text-sm font-medium text-white hover:bg-brand-light disabled:opacity-50"
        >
          {loading ? "Building..." : "Build Schedule"}
        </button>
      </form>

      {error && (
        <p className="mt-6 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</p>
      )}

      {result && !error && (
        <div className="mt-8">
          {result.notes.length > 0 && (
            <ul className="mb-4 space-y-1 rounded-md bg-amber-50 p-3 text-xs text-amber-800">
              {result.notes.map((note, i) => (
                <li key={i}>• {note}</li>
              ))}
            </ul>
          )}

          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
            {STRATEGY_ORDER.map((strategyKey) => {
              const schedule = result.schedules[strategyKey];
              const isActive = strategyKey === activeStrategy;
              return (
                <button
                  key={strategyKey}
                  onClick={() => setActiveStrategy(strategyKey)}
                  disabled={!schedule}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                    isActive
                      ? "bg-brand text-white"
                      : schedule
                        ? "bg-slate-100 text-slate-700 hover:bg-slate-200"
                        : "cursor-not-allowed bg-slate-50 text-slate-300"
                  }`}
                >
                  {schedule?.label ?? strategyKey.replace(/_/g, " ")}
                  {!schedule && " (infeasible)"}
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            {activeSchedule ? (
              <>
                <div className="mb-4 flex flex-wrap gap-6 text-sm text-slate-600">
                  <span>
                    <strong className="text-slate-900">{activeSchedule.total_credits}</strong> credits
                  </span>
                  <span>
                    <strong className="text-slate-900">{activeSchedule.campus_days.length}</strong> campus
                    day(s){" "}
                    {activeSchedule.campus_days.length > 0 &&
                      `(${activeSchedule.campus_days.map((d) => d.slice(0, 3)).join(", ")})`}
                  </span>
                  <span>
                    Average fit score:{" "}
                    <strong className="text-slate-900">{activeSchedule.average_fit_score}</strong>/100
                  </span>
                </div>
                <WeeklyCalendar sections={activeSchedule.sections} />
                <ul className="mt-4 divide-y divide-slate-100 rounded-lg border border-slate-200">
                  {activeSchedule.sections.map((section) => (
                    <li key={section.id} className="flex items-center justify-between p-3 text-sm">
                      <span>
                        <strong>{section.course.code}</strong> — {section.course.title}
                        {section.professor && ` · ${section.professor.name}`}
                      </span>
                      <span className="text-xs uppercase text-slate-400">
                        {section.delivery_mode.replace("_", " ")}
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="text-sm text-slate-500">
                No feasible schedule was found for this strategy with your current requirements.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
