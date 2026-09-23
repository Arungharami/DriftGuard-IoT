import type { Metadata } from "next";

import { Card, PageHeader, Section } from "@/components/ui";
import { RESEARCH_QUESTIONS } from "@/content/site";

export const metadata: Metadata = { title: "Research" };

export default function ResearchPage() {
  return (
    <>
      <PageHeader
        title="Research"
        lede="Scientific positioning, research questions, and the separation between reproduction and extension."
      />
      <Section title="Two tracks">
        <div className="grid gap-4 sm:grid-cols-2">
          <Card title="Reproduction track">
            <p>
              Leakage-safe re-implementation of Decision Tree, Random Forest, Bagging, DT/RF/MLP
              Stacking and LightGBM on TON_IoT, WUSTL-IIOT-2021 and Edge-IIoTset, with every
              hyperparameter, seed, source hash and software version recorded.
            </p>
          </Card>
          <Card title="Extension track">
            <p>
              A separately evaluated drift monitor (unsupervised feature drift, kept distinct
              from supervised performance drift) and an experimental adaptation policy choosing
              among retain, recalibrate and retrain, compared with no adaptation and periodic
              retraining.
            </p>
          </Card>
        </div>
      </Section>
      <Section title="Research questions">
        <dl className="space-y-3">
          {RESEARCH_QUESTIONS.map((q) => (
            <div key={q.id} className="rounded-lg border border-line p-4">
              <dt className="font-mono text-sm text-accent">{q.id}</dt>
              <dd className="mt-1">{q.text}</dd>
            </div>
          ))}
        </dl>
      </Section>
    </>
  );
}
