import { PageHeader } from "@/components/ui";
import { ModelDemo } from "@/components/ModelDemo";
import { StreamingDemo } from "@/components/StreamingDemo";
export default function Page() {
  return <>
    <PageHeader title="Live Streaming Demo" lede="Follow the MQTT inference pipeline, inspect its evidence, and distinguish observed software behavior from validated research." />
    <StreamingDemo />
    <section aria-label="Approved model query" className="mt-10 space-y-4">
      <h2 className="text-xl font-semibold">Query an approved research model</h2>
      <ModelDemo />
    </section>
  </>;
}
