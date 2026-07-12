import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { ChartMode } from "@/components/charts/leaderboard/types";

export type CorpusFilter = "29-task corpus" | "26-task corpus" | "all";
export type RunView = "best" | "all";

export type LeaderboardControlsProps = {
  view: RunView;
  onViewChange: (view: RunView) => void;
  mode: ChartMode;
  onModeChange: (mode: ChartMode) => void;
  corpus: CorpusFilter;
  onCorpusChange: (corpus: CorpusFilter) => void;
  modelCount: number;
  taskLabel: string;
  visibleRunCount: number;
  totalRunCount: number;
};

export function LeaderboardControls({
  view,
  onViewChange,
  mode,
  onModeChange,
  corpus,
  onCorpusChange,
  modelCount,
  taskLabel,
  visibleRunCount,
  totalRunCount,
}: LeaderboardControlsProps) {
  return (
    <div className="control-bar" role="group" aria-label="Run plot controls">
      <div className="control-groups">
        <ToggleGroup
          type="single"
          value={view}
          onValueChange={(value) => {
            if (value) onViewChange(value as RunView);
          }}
          aria-label="Run density"
          className="run-view-toggle"
        >
          <ToggleGroupItem value="best" aria-label="Show the best recorded row per model">
            Best models
          </ToggleGroupItem>
          <ToggleGroupItem value="all" aria-label="Show every recorded effort level">
            All effort levels
          </ToggleGroupItem>
        </ToggleGroup>
        <ToggleGroup
          type="single"
          value={corpus}
          onValueChange={(value) => {
            if (value) onCorpusChange(value as CorpusFilter);
          }}
          aria-label="Corpus size"
        >
          <ToggleGroupItem value="29-task corpus" aria-label="Show current 29-task corpus">
            29 current
          </ToggleGroupItem>
          <ToggleGroupItem value="26-task corpus" aria-label="Show historical 26-task corpus">
            26 historical
          </ToggleGroupItem>
          <ToggleGroupItem value="all" aria-label="Show all corpus sizes">
            All
          </ToggleGroupItem>
        </ToggleGroup>
        <ToggleGroup
          type="single"
          value={mode}
          onValueChange={(value) => {
            if (value) onModeChange(value as ChartMode);
          }}
          aria-label="Chart metric"
        >
          <ToggleGroupItem value="score" aria-label="Show score">
            Score
          </ToggleGroupItem>
          <ToggleGroupItem value="time" aria-label="Show agent time">
            Agent time
          </ToggleGroupItem>
          <ToggleGroupItem
            value="failures"
            aria-label={corpus === "all" ? "Filter to one corpus to compare failure counts" : "Show failures"}
            disabled={corpus === "all"}
            title={corpus === "all" ? "Failure counts require one corpus denominator" : undefined}
          >
            Failures
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
      <div className="leaderboard-meta">
        <span>
          <strong>{taskLabel}</strong> · <strong>{modelCount} models</strong>
        </span>
        <Badge variant="muted">Rows {visibleRunCount}/{totalRunCount}</Badge>
      </div>
    </div>
  );
}
