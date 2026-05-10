import {
  BarChart3,
  BrainCircuit,
  Database,
  History,
  Network,
  Radar,
  Workflow
} from "lucide-react";

export const stages = [
  {
    id: "data-pipeline",
    label: "Data Pre-Processing",
    kicker: "01",
    Icon: Database
  },
  {
    id: "methodology",
    label: "Dynamic Taxonomy Construction",
    kicker: "02",
    Icon: Workflow
  },
  {
    id: "nlp",
    label: "Live NLP Inference",
    kicker: "03",
    Icon: BrainCircuit
  },
  {
    id: "case-study",
    label: "Case Study",
    kicker: "04",
    Icon: History
  },
  {
    id: "taxonomy",
    label: "Dynamic Taxonomy",
    kicker: "05",
    Icon: Radar
  },
  {
    id: "graph",
    label: "Spatio-Temporal Graph",
    kicker: "06",
    Icon: Network
  },
  {
    id: "portfolio",
    label: "Backtester",
    kicker: "07",
    Icon: BarChart3
  }
] as const;

export type StageId = (typeof stages)[number]["id"];
