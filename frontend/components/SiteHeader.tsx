import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-bold text-brand">
          CampusWise AI
        </Link>
        <nav className="flex gap-6 text-sm font-medium text-slate-600">
          <Link href="/courses" className="hover:text-brand">
            Courses
          </Link>
          <Link href="/professors" className="hover:text-brand">
            Professors
          </Link>
          <Link href="/schedule" className="hover:text-brand">
            Schedule Builder
          </Link>
        </nav>
      </div>
    </header>
  );
}
