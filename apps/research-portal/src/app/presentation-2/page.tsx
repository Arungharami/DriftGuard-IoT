import type { Metadata } from "next";
import { IoTCourseExperience } from "@/components/IoTCourseExperience";

export const metadata: Metadata = {
  title: "Presentation 2 | DriftGuard-IoT",
  description: "CNT 6167 DriftGuard-IoT course presentation by Arun Kumar Gharami and Ankith Gajam. Explore slides, video status, diagrams, method, evaluation, mind map, and academic resources."
};

export default function PresentationTwoPage() {
  return <IoTCourseExperience />;
}
