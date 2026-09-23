import { PageHeader } from "@/components/ui";
import { ResultsExplorer } from "@/components/ResultsExplorer";
import { resultsIndex } from "@/lib/results";
export default function Page() { return <><PageHeader title="Model Comparison" lede="Compare verified baselines using the same evaluation conditions." /><ResultsExplorer results={resultsIndex.results} /><p className="mt-8 text-ink-muted">Real-data findings remain blocked. Synthetic software checks are documented separately and never enter these charts.</p></>; }
