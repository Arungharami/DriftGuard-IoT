import { PageHeader, Card } from "@/components/ui";
import Link from "next/link";
export default function Page() { return <>
<PageHeader title={"Cross-Domain Evaluation"} lede={"Transfer must preserve physical meaning across independently acquired datasets."} />
<div className="grid gap-5 md:grid-cols-2"><Card title={"No verified real pair yet"}><p>{"Edge packet fields, Argus flows and Zeek flows cannot be aligned by name alone. Every mapping needs documented units, direction, aggregation and label semantics."}</p></Card>
<Card title={"Isolation"}><p>{"Source training fits preprocessing and models. Target data cannot tune parameters or confidence thresholds. Capture groups and feature duplicates are checked across partitions."}</p></Card>
</div><p className="mt-6"><Link className="text-accent underline" href="/experiments">Inspect recorded evidence and blockers</Link></p></>; }
