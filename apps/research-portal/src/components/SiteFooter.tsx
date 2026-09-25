import { REFERENCE_PAPER, REPO_URL } from "@/content/site";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface-muted">
      <div className="mx-auto max-w-5xl space-y-2 px-4 py-6 text-sm text-ink-muted sm:px-6">
        <p>
          Independent reproduction and extension of{" "}
          <a className="underline" href={`https://doi.org/${REFERENCE_PAPER.doi}`}>
            doi:{REFERENCE_PAPER.doi}
          </a>
          . Not affiliated with the reference authors.
        </p>
        <p>
          Research metrics come only from provenance-checked result files. Streaming demonstrations are labeled separately.{" "}
          <a className="underline" href={REPO_URL}>
            Source on GitHub
          </a>
        </p>
      </div>
    </footer>
  );
}
