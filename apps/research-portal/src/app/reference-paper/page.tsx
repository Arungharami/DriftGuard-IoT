import { PageHeader, Card } from "@/components/ui";
import Link from "next/link";
export default function Page() { return <>
<PageHeader title={"Reference Paper"} lede={"A verified baseline methodology, kept separate from the leakage-safe primary protocol."} />
<div className="grid gap-5 md:grid-cols-2"><Card title={"Source"}><p>{"Ismail, Dandan and Qushou, IEEE Access 13 (2025), 73468\u201373485. DOI: 10.1109/ACCESS.2025.3554083. Bibliographic metadata is verified against Crossref; protocol discrepancies are documented in the repository."}</p></Card>
<Card title={"Reproduction boundary"}><p>{"Paper-faithful preprocessing applies selection and resampling before the split. It is retained as a labeled reproduction protocol and cannot support leakage-safe primary findings."}</p></Card>
</div><p className="mt-6"><Link className="text-accent underline" href="/experiments">Inspect recorded evidence and blockers</Link></p></>; }
