import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">Page not found</h1>
      <p className="text-ink-muted">
        <Link href="/" className="underline">
          Return home
        </Link>
      </p>
    </div>
  );
}
