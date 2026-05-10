"use client";

import { useEffect } from "react";
import { CaseStudy } from "@/components/CaseStudy";
import { DataPipelineSection } from "@/components/modules/data-pipeline/DataPipelineSection";
import { MethodologySection } from "@/components/modules/methodology/MethodologySection";
import { NLPEngineSection } from "@/components/modules/nlp-engine/NLPEngineSection";
import { PortfolioBacktesterSection } from "@/components/modules/portfolio-backtester/PortfolioBacktesterSection";
import { STGATGraphSection } from "@/components/modules/st-gat-graph/STGATGraphSection";
import { TaxonomyExplorerSection } from "@/components/modules/taxonomy-explorer/TaxonomyExplorerSection";
import { StageNav } from "@/components/shell/StageNav";
import { stages, type StageId } from "@/lib/constants/stages";
import { useDashboardStore } from "@/stores/useDashboardStore";

export function AppFrame() {
  const setActiveStage = useDashboardStore((state) => state.setActiveStage);

  useEffect(() => {
    const sectionElements = stages
      .map((stage) => document.getElementById(stage.id))
      .filter((element): element is HTMLElement => Boolean(element));

    const syncActiveStage = () => {
      const viewportMidpoint = window.innerHeight / 2;
      const centeredSection = sectionElements.find((element) => {
        const rect = element.getBoundingClientRect();
        return rect.top <= viewportMidpoint && rect.bottom >= viewportMidpoint;
      });

      if (centeredSection?.id) {
        setActiveStage(centeredSection.id as StageId);
        return;
      }

      const nearestSection = sectionElements
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            element,
            distance: Math.abs(rect.top + rect.height / 2 - viewportMidpoint)
          };
        })
        .sort((a, b) => a.distance - b.distance)[0]?.element;

      if (nearestSection?.id) {
        setActiveStage(nearestSection.id as StageId);
      }
    };

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          syncActiveStage();
        }
      },
      {
        rootMargin: "-50% 0px -50% 0px",
        threshold: 0
      }
    );

    let frame = 0;
    const queueSync = () => {
      if (frame) {
        return;
      }
      frame = window.requestAnimationFrame(() => {
        frame = 0;
        syncActiveStage();
      });
    };

    sectionElements.forEach((element) => observer.observe(element));
    syncActiveStage();
    window.addEventListener("scroll", queueSync, { passive: true });
    window.addEventListener("resize", queueSync);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", queueSync);
      window.removeEventListener("resize", queueSync);
      if (frame) {
        window.cancelAnimationFrame(frame);
      }
    };
  }, [setActiveStage]);

  return (
    <div className="min-h-screen bg-mercury-abyss">
      <StageNav />
      <main>
        <DataPipelineSection />
        <MethodologySection />
        <NLPEngineSection />
        <CaseStudy />
        <TaxonomyExplorerSection />
        <STGATGraphSection />
        <PortfolioBacktesterSection />
      </main>
    </div>
  );
}
