import { PageHeader, Card } from "@/components/ui";
import Link from "next/link";
export default function Page() { return <>
<PageHeader title={"Our Contribution"} lede={"A research platform designed to make assumptions, evidence and failure states inspectable."} />
<div className="grid gap-5 md:grid-cols-2"><Card title={"Scientific question"}><p>{"Does delayed-label drift-triggered adaptation improve generalization relative to frozen and periodic models under equivalent budgets? This question remains open until valid real-data experiments run."}</p></Card>
<Card title={"Prior work"}><p>{"Adaptive LightGBM and ADWIN-based approaches already exist. DriftGuard does not claim novelty solely from multiple datasets, an ensemble of tools, or a connected portal."}</p></Card>
<Card title={"Implemented foundation"}><p>{"Versioned provenance, license gates, resumable campaigns, delayed-label controls, source-only preprocessing and explicit blocked results form the reproducibility foundation."}</p></Card>
</div><p className="mt-6"><Link className="text-accent underline" href="/experiments">Inspect recorded evidence and blockers</Link></p></>; }
