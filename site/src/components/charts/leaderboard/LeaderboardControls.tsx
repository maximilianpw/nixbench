import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { TaskScaleMode } from "@/components/charts/leaderboard/chart-scale";

export type CorpusFilter = "29-task corpus" | "26-task corpus";
export type EvidenceView = "summary" | "trials";

export type LeaderboardControlsProps = {
  corpus: CorpusFilter;
  onCorpusChange: (corpus: CorpusFilter) => void;
  view: EvidenceView;
  onViewChange: (view: EvidenceView) => void;
  taskScaleMode: TaskScaleMode;
  onTaskScaleModeChange: (mode: TaskScaleMode) => void;
  modelCount: number;
  configurationCount: number;
  trialCount: number;
  replicatedConfigurationCount: number;
};

export function LeaderboardControls({
  corpus,
  onCorpusChange,
  view,
  onViewChange,
  taskScaleMode,
  onTaskScaleModeChange,
  modelCount,
  configurationCount,
  trialCount,
  replicatedConfigurationCount,
}: LeaderboardControlsProps) {
  return (
    <div className="control-bar evidence-control-bar" role="group" aria-label="Evidence plot controls">
      <div className="evidence-control-options">
        <div className="control-groups">
          <span className="control-label">Corpus</span>
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
          </ToggleGroup>
        </div>

        <div className="control-groups">
          <span className="control-label">Evidence</span>
          <ToggleGroup
            type="single"
            value={view}
            onValueChange={(value) => {
              if (value) onViewChange(value as EvidenceView);
            }}
            aria-label="Evidence detail"
          >
            <ToggleGroupItem value="summary" aria-label="Show configuration means and confidence intervals">
              Means
            </ToggleGroupItem>
            <ToggleGroupItem value="trials" aria-label="Show means, confidence intervals, and individual trials">
              All trials
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <div className="control-groups">
          <span className="control-label">Y-axis</span>
          <ToggleGroup
            type="single"
            value={taskScaleMode}
            onValueChange={(value) => {
              if (value) onTaskScaleModeChange(value as TaskScaleMode);
            }}
            aria-label="Task axis scale"
          >
            <ToggleGroupItem value="focused" aria-label="Focus the task axis on the observed evidence range">
              Focused
            </ToggleGroupItem>
            <ToggleGroupItem value="full" aria-label="Show the full task axis from zero">
              Full scale
            </ToggleGroupItem>
          </ToggleGroup>
        </div>
      </div>
      <div className="leaderboard-meta" aria-label="Visible evidence summary">
        <span>
          <strong>{modelCount}</strong> models · <strong>{configurationCount}</strong> configurations ·{" "}
          <strong>{trialCount}</strong> trials
        </span>
        <Badge variant="default">
          {view === "summary" ? `${configurationCount} means shown` : `${trialCount} trials shown`}
        </Badge>
        <Badge variant="muted">
          {replicatedConfigurationCount}/{configurationCount} replicated
        </Badge>
      </div>
    </div>
  );
}
