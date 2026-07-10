import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { ChartMode } from "@/components/charts/leaderboard/types";

export type CorpusFilter = "29-task corpus" | "26-task corpus" | "all";

export type LeaderboardControlsProps = {
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
    <div className="control-bar" aria-label="Run plot controls">
      <div className="control-groups">
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
          <ToggleGroupItem value="failures" aria-label="Show failures">
            Failures
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
      <div className="leaderboard-meta">
        <span>
          <strong>{taskLabel}</strong> · <strong>{modelCount} models</strong>
        </span>
        <Badge variant="muted">Runs {visibleRunCount}/{totalRunCount}</Badge>
      </div>
    </div>
  );
}
