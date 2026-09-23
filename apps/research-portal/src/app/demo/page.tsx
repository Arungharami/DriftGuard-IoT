import { PageHeader } from "@/components/ui";
import { ModelDemo } from "@/components/ModelDemo";
export default function Page() { return <><PageHeader title="Live Model Demo" lede="The inference connection is prepared. An approved model and authorized service are required before predictions can be served." /><ModelDemo /></>; }
