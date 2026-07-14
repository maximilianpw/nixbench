import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

export type CorpusFilter = "29-task corpus" | "26-task corpus";

export type LeaderboardControlsProps = {
  corpus: CorpusFilter;
  onCorpusChange: (corpus: CorpusFilter) => void;
  modelCount: number;
  configurationCount: number;
  trialCount: number;
  replicatedConfigurationCount: number;
};

export function LeaderboardControls({
  corpus,
  onCorpusChange,
  modelCount,
  configurationCount,
  trialCount,
  replicatedConfigurationCount,
}: LeaderboardControlsProps) {
  return (
    <div className="control-bar evidence-control-bar" role="group" aria-label="Evidence plot controls">
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
      <div className="leaderboard-meta" aria-label="Visible evidence summary">
        <span>
          <strong>{modelCount}</strong> models · <strong>{configurationCount}</strong> configurations
        </span>
        <Badge variant="default">
          {trialCount} {trialCount === 1 ? "trial" : "trials"}
        </Badge>
        <Badge variant="muted">
          {replicatedConfigurationCount}/{configurationCount} replicated
        </Badge>
      </div>
    </div>
  );
}
