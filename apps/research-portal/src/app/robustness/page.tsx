import { PageHeader, Card } from "@/components/ui";
import Link from "next/link";
export default function Page() { return <>
<PageHeader title={"Defensive Robustness"} lede={"Offline sensitivity measurements with explicit bounds and no traffic-generation tools."} />
<div className="grid gap-5 md:grid-cols-2"><Card title={"Bounded measurement noise"}><p>{"The package allows aggregate-only random perturbations of reviewed independent continuous measurements, bounded by training IQR. It does not optimize evasion or export modified traffic."}</p></Card>
<Card title={"Unknown attacks"}><p>{"Held-out attack families must be excluded from training and threshold calibration. Unknown recall is evaluated jointly with known-class false rejection."}</p></Card>
<Card title={"Evidence status"}><p>{"Real-data robustness and unknown-family results are blocked by dataset and physical-schema validation. Synthetic outliers are only software tests."}</p></Card>
</div><p className="mt-6"><Link className="text-accent underline" href="/experiments">Inspect recorded evidence and blockers</Link></p></>; }
