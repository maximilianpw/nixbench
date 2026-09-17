import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { TaskScaleMode } from "@/components/charts/leaderboard/chart-scale";
import type { ModelKey } from "@/data/benchmark";

export type CorpusFilter = "29-task corpus" | "26-task corpus";
export type EvidenceView = "summary" | "trials";
export type ModelFilter = ModelKey | "all";
export type EvidenceFilter = "all" | "repeated";
export type LeaderboardControlsProps = {
  corpus: CorpusFilter; onCorpusChange: (corpus: CorpusFilter) => void;
  view: EvidenceView; onViewChange: (view: EvidenceView) => void;
  taskScaleMode: TaskScaleMode; onTaskScaleModeChange: (mode: TaskScaleMode) => void;
  modelFilter: ModelFilter; onModelFilterChange: (value: string) => void;
  modelOptions: Array<{ value: ModelKey; label: string }>;
  evidenceFilter: EvidenceFilter; onEvidenceFilterChange: (filter: EvidenceFilter) => void;
  modelCount: number; configurationCount: number; trialCount: number; replicatedConfigurationCount: number;
};

const labelClass = "font-mono text-[0.68rem] font-semibold uppercase tracking-wider text-muted-foreground";
const fieldClass = "min-h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground focus-visible:ring-2 focus-visible:ring-ring";

export function LeaderboardControls(props: LeaderboardControlsProps) {
  const { corpus, onCorpusChange, view, onViewChange, taskScaleMode, onTaskScaleModeChange, modelFilter, onModelFilterChange, modelOptions, evidenceFilter, onEvidenceFilterChange, modelCount, configurationCount, trialCount, replicatedConfigurationCount } = props;
  return (
    <div className="rounded-lg border bg-card p-4 sm:p-5" role="group" aria-label="Evidence plot controls">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <div className="grid content-start gap-2"><span className={labelClass}>Corpus</span><ToggleGroup type="single" value={corpus} onValueChange={(value) => value && onCorpusChange(value as CorpusFilter)} aria-label="Corpus size"><ToggleGroupItem value="29-task corpus">29 current</ToggleGroupItem><ToggleGroupItem value="26-task corpus">26 historical</ToggleGroupItem></ToggleGroup></div>
        <label className="grid content-start gap-2"><span className={labelClass}>Model</span><select className={fieldClass} value={modelFilter} onChange={(event) => onModelFilterChange(event.currentTarget.value)}><option value="all">All models</option>{modelOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
        <label className="grid content-start gap-2"><span className={labelClass}>Evidence</span><select className={fieldClass} value={evidenceFilter} onChange={(event) => onEvidenceFilterChange(event.currentTarget.value === "repeated" ? "repeated" : "all")}><option value="all">All results</option><option value="repeated">Repeated runs only</option></select></label>
        <div className="grid content-start gap-2"><span className={labelClass}>Runs</span><ToggleGroup type="single" value={view} onValueChange={(value) => value && onViewChange(value as EvidenceView)} aria-label="Run detail"><ToggleGroupItem value="summary">Averages</ToggleGroupItem><ToggleGroupItem value="trials">Individual</ToggleGroupItem></ToggleGroup></div>
        <div className="grid content-start gap-2"><span className={labelClass}>Task axis</span><ToggleGroup type="single" value={taskScaleMode} onValueChange={(value) => value && onTaskScaleModeChange(value as TaskScaleMode)} aria-label="Task axis scale"><ToggleGroupItem value="full">Zero</ToggleGroupItem><ToggleGroupItem value="focused">Zoom</ToggleGroupItem></ToggleGroup></div>
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-2 border-t pt-4 text-sm text-muted-foreground" aria-label="Visible evidence summary">
        <span className="mr-auto"><strong className="text-foreground">{modelCount}</strong> models · <strong className="text-foreground">{configurationCount}</strong> configurations · <strong className="text-foreground">{trialCount}</strong> runs</span>
        <Badge>{view === "summary" ? `${configurationCount} averages shown` : `${trialCount} runs shown`}</Badge>
        <Badge variant="muted">{replicatedConfigurationCount}/{configurationCount} repeated</Badge>
      </div>
    </div>
  );
}
