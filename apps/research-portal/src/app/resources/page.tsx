import { PageHeader, Card } from "@/components/ui";
import Link from "next/link";
export default function Page() { return <>
<PageHeader title={"Resource Benchmark"} lede={"Measure the full pipeline and state the hardware and input workload."} />
<div className="grid gap-5 md:grid-cols-2"><Card title={"Measurement protocol"}><p>{"Warm batch latency percentiles, throughput, CPU time, model bytes and fresh-process high-water RSS are available. Model load time is separate from warm prediction."}</p></Card>
<Card title={"Interpretation"}><p>{"Schema-only synthetic timing validates instrumentation. It cannot establish edge-device performance or latency under operational traffic. No real edge benchmark has been recorded."}</p></Card>
</div><p className="mt-6"><Link className="text-accent underline" href="/experiments">Inspect recorded evidence and blockers</Link></p></>; }
