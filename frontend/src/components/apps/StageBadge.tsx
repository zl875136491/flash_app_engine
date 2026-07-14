import type { Stage } from "@/lib/api";
import { STAGE_LABEL } from "@/lib/task-utils";
import { cn } from "@/lib/utils";

const tone: Record<Stage, string> = {
  Received: "bg-muted text-muted-foreground",
  Analyzing: "bg-secondary text-secondary-foreground",
  Coding: "bg-secondary text-secondary-foreground",
  Building: "bg-accent/30 text-accent-foreground",
  Verifying: "bg-accent/30 text-accent-foreground",
  Success: "bg-primary/15 text-primary",
  Failed: "bg-destructive/15 text-destructive",
  Stopped: "bg-muted text-muted-foreground",
};

export function StageBadge({ stage }: { stage: Stage }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tone[stage],
      )}
    >
      {STAGE_LABEL[stage]}
    </span>
  );
}
