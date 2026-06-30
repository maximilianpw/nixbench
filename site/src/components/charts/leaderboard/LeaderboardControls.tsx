import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { leaderboardRuns, resultColumns } from "@/data/benchmark";
import type { ChartMode } from "@/components/charts/leaderboard/types";

export type LeaderboardControlsProps = {
  mode: ChartMode;
  onModeChange: (mode: ChartMode) => void;
};

export function LeaderboardControls({ mode, onModeChange }: LeaderboardControlsProps) {
  const totalTasks = leaderboardRuns[0]?.totalTasks ?? 0;

  return (
    <div className="control-bar" aria-label="Run plot controls">
      <div className="control-groups">
        <ToggleGroup type="single" value="v0.2" aria-label="Corpus version">
          <ToggleGroupItem value="v0.2" aria-label="Corpus v0.2">
            v0.2
          </ToggleGroupItem>
          <ToggleGroupItem value="v0.1" aria-label="Corpus v0.1">
            v0.1
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
          <strong>{totalTasks} tasks</strong> · <strong>{resultColumns.length} models</strong>
        </span>
        <Button variant="secondary" size="sm" type="button">
          Runs <span>({leaderboardRuns.length}/{leaderboardRuns.length})</span>
        </Button>
      </div>
    </div>
  );
}
