import { ScheduleBuilder } from "@/components/ScheduleBuilder";

export default function SchedulePage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Schedule Builder</h1>
      <p className="mt-1 text-sm text-slate-500">
        Describe what you want your semester to look like, and we&apos;ll generate a few
        different ways to build it.
      </p>

      <div className="mt-6">
        <ScheduleBuilder />
      </div>
    </main>
  );
}
