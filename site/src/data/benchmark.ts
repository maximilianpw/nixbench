import generatedTrialRows from "@/data/benchmark-trials.json";

export type AgentKind = "codex" | "claude";
export type RunStatus = "complete";
export type TaskStatus = "pass" | "fail";
export type ModelKey =
  | "gpt55"
  | "gpt54"
  | "gpt54Mini"
  | "claudeOpus48"
  | "gpt56Sol"
  | "gpt56Terra"
  | "gpt56Luna";
export type ReasoningEffort = "low" | "medium" | "high" | "xhigh" | "max" | "ultra";

export type LeaderboardRun = {
  id: string;
  configurationId?: string;
  agent: string;
  model?: string;
  kind: AgentKind;
  corpus: string;
  runId: string;
  studyId?: string;
  agentVersion?: string;
  corpusRevision?: string;
  host?: string;
  network?: string;
  platform?: string;
  system?: string;
  agentTimeoutSeconds?: number;
  marker: string;
  series?: ModelKey;
  effort?: ReasoningEffort;
  trial?: number;
  provenance?: "trial" | "composite";
  passRate: number;
  score: number;
  maxScore: number;
  agentTimeSeconds: number;
  agentTimeLabel: string;
  failed: number;
  timeouts: number;
  completedTasks: number;
  totalTasks: number;
  status: RunStatus;
};

export type Estimate = {
  n: number;
  mean: number;
  min: number;
  max: number;
  standardDeviation?: number;
  ci95Low?: number;
  ci95High?: number;
  ci95Margin?: number;
};

export type LeaderboardAggregate = {
  id: string;
  agent: string;
  kind: AgentKind;
  corpus: string;
  marker: string;
  series?: ModelKey;
  effort?: ReasoningEffort;
  taskCount: number;
  trialCount: number;
  trials: LeaderboardRun[];
  passedTasks: Estimate;
  scoreRate: Estimate;
  agentSecondsPerTask: Estimate;
  agentTimeSeconds: Estimate;
  totalTimeouts: number;
  provenance: "trial" | "composite";
};

export type ResultColumn = {
  key: ModelKey;
  label: string;
  shortLabel: string;
  corpus: "26-task corpus" | "29-task corpus";
  effort: "xhigh" | "default";
  runId: string;
};

export type TaskRunCell = {
  status: TaskStatus;
  seconds?: number;
};

export type TaskResult = {
  task: string;
  area: string;
  results: Partial<Record<ModelKey, TaskRunCell>>;
};

export const currentCorpusTaskCount = 29;
export const currentCorpusLabel = `${currentCorpusTaskCount}-task corpus`;

export const resultColumns: ResultColumn[] = [
  {
    key: "gpt55",
    label: "GPT-5.5",
    shortLabel: "5.5",
    corpus: "26-task corpus",
    effort: "xhigh",
    runId: "20260624T182835Z-4ad8b555 (+2)",
  },
  {
    key: "gpt54",
    label: "GPT-5.4",
    shortLabel: "5.4",
    corpus: "26-task corpus",
    effort: "xhigh",
    runId: "20260624T190640Z-fa04a19c (+2)",
  },
  {
    key: "gpt54Mini",
    label: "GPT-5.4 mini",
    shortLabel: "mini",
    corpus: "26-task corpus",
    effort: "xhigh",
    runId: "20260624T194359Z-268b0abe (+2)",
  },
  {
    key: "claudeOpus48",
    label: "Claude Opus 4.8",
    shortLabel: "opus",
    corpus: "26-task corpus",
    effort: "default",
    runId: "20260624T202141Z-881ef1e9 (+2)",
  },
  {
    key: "gpt56Sol",
    label: "GPT-5.6 Sol",
    shortLabel: "sol",
    corpus: "29-task corpus",
    effort: "xhigh",
    runId: "20260709T175817Z-cb86c575",
  },
  {
    key: "gpt56Terra",
    label: "GPT-5.6 Terra",
    shortLabel: "terra",
    corpus: "29-task corpus",
    effort: "xhigh",
    runId: "20260709T175820Z-36a5f2f2",
  },
  {
    key: "gpt56Luna",
    label: "GPT-5.6 Luna",
    shortLabel: "luna",
    corpus: "29-task corpus",
    effort: "xhigh",
    runId: "20260709T175826Z-b8e5f041",
  },
];

const originalLeaderboardRuns: LeaderboardRun[] = [
  {
    id: "gpt-56-sol-low",
    agent: "GPT-5.6 Sol via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T080546Z-b5d84e84",
    marker: "SL",
    series: "gpt56Sol",
    effort: "low",
    passRate: 72,
    score: 2100,
    maxScore: 2900,
    agentTimeSeconds: 1135.973,
    agentTimeLabel: "18m 56s",
    failed: 8,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-sol-medium",
    agent: "GPT-5.6 Sol via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T082452Z-0d42d5d1",
    marker: "SM",
    series: "gpt56Sol",
    effort: "medium",
    passRate: 76,
    score: 2200,
    maxScore: 2900,
    agentTimeSeconds: 1644.116,
    agentTimeLabel: "27m 24s",
    failed: 7,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-sol-high",
    agent: "GPT-5.6 Sol via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T085227Z-8ce3793d",
    marker: "SH",
    series: "gpt56Sol",
    effort: "high",
    passRate: 76,
    score: 2200,
    maxScore: 2900,
    agentTimeSeconds: 1814.83,
    agentTimeLabel: "30m 15s",
    failed: 7,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-sol-xhigh",
    agent: "GPT-5.6 Sol via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260709T175817Z-cb86c575",
    marker: "SX",
    series: "gpt56Sol",
    effort: "xhigh",
    passRate: 72,
    score: 2100,
    maxScore: 2900,
    agentTimeSeconds: 1591.807,
    agentTimeLabel: "26m 32s",
    failed: 8,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-sol-max",
    agent: "GPT-5.6 Sol via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T152810Z-214936aa",
    marker: "S+",
    series: "gpt56Sol",
    effort: "max",
    passRate: 76,
    score: 2200,
    maxScore: 2900,
    agentTimeSeconds: 2873.506,
    agentTimeLabel: "47m 54s",
    failed: 7,
    timeouts: 2,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-terra-low",
    agent: "GPT-5.6 Terra via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T080604Z-36ff1ac9",
    marker: "TL",
    series: "gpt56Terra",
    effort: "low",
    passRate: 69,
    score: 2000,
    maxScore: 2900,
    agentTimeSeconds: 1789.752,
    agentTimeLabel: "29m 50s",
    failed: 9,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-terra-medium",
    agent: "GPT-5.6 Terra via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T083607Z-086ef952",
    marker: "TM",
    series: "gpt56Terra",
    effort: "medium",
    passRate: 72,
    score: 2100,
    maxScore: 2900,
    agentTimeSeconds: 1993.794,
    agentTimeLabel: "33m 14s",
    failed: 8,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-terra-high",
    agent: "GPT-5.6 Terra via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T152820Z-20a86451",
    marker: "TH",
    series: "gpt56Terra",
    effort: "high",
    passRate: 72,
    score: 2100,
    maxScore: 2900,
    agentTimeSeconds: 1634.302,
    agentTimeLabel: "27m 14s",
    failed: 8,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-terra-xhigh",
    agent: "GPT-5.6 Terra via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260709T175820Z-36a5f2f2",
    marker: "TX",
    series: "gpt56Terra",
    effort: "xhigh",
    passRate: 66,
    score: 1900,
    maxScore: 2900,
    agentTimeSeconds: 1222.205,
    agentTimeLabel: "20m 22s",
    failed: 10,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-luna-low",
    agent: "GPT-5.6 Luna via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T080607Z-d15bf2ca",
    marker: "LL",
    series: "gpt56Luna",
    effort: "low",
    passRate: 76,
    score: 2200,
    maxScore: 2900,
    agentTimeSeconds: 970.472,
    agentTimeLabel: "16m 10s",
    failed: 7,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-luna-medium",
    agent: "GPT-5.6 Luna via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T082225Z-8be54afa",
    marker: "LM",
    series: "gpt56Luna",
    effort: "medium",
    passRate: 69,
    score: 2000,
    maxScore: 2900,
    agentTimeSeconds: 1190.721,
    agentTimeLabel: "19m 51s",
    failed: 9,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-luna-high",
    agent: "GPT-5.6 Luna via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T084224Z-5fdc40c6",
    marker: "LH",
    series: "gpt56Luna",
    effort: "high",
    passRate: 72,
    score: 2100,
    maxScore: 2900,
    agentTimeSeconds: 1637.606,
    agentTimeLabel: "27m 18s",
    failed: 8,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-luna-xhigh",
    agent: "GPT-5.6 Luna via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260709T175826Z-b8e5f041",
    marker: "LX",
    series: "gpt56Luna",
    effort: "xhigh",
    passRate: 66,
    score: 1900,
    maxScore: 2900,
    agentTimeSeconds: 1427.246,
    agentTimeLabel: "23m 47s",
    failed: 10,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-56-luna-max",
    agent: "GPT-5.6 Luna via Codex CLI",
    kind: "codex",
    corpus: "29-task corpus",
    runId: "20260710T152845Z-c0067294",
    marker: "L+",
    series: "gpt56Luna",
    effort: "max",
    passRate: 76,
    score: 2200,
    maxScore: 2900,
    agentTimeSeconds: 2419.857,
    agentTimeLabel: "40m 20s",
    failed: 7,
    timeouts: 0,
    completedTasks: 29,
    totalTasks: 29,
    status: "complete",
  },
  {
    id: "gpt-55-low",
    agent: "GPT-5.5 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T072711Z-e484ea0f",
    marker: "5L",
    series: "gpt55",
    effort: "low",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 1164.896,
    agentTimeLabel: "19m 25s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-55-medium",
    agent: "GPT-5.5 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T073226Z-3fce189c",
    marker: "5M",
    series: "gpt55",
    effort: "medium",
    passRate: 73,
    score: 1900,
    maxScore: 2600,
    agentTimeSeconds: 1335.219,
    agentTimeLabel: "22m 15s",
    failed: 7,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-55-high",
    agent: "GPT-5.5 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T073227Z-167ae812",
    marker: "5H",
    series: "gpt55",
    effort: "high",
    passRate: 73,
    score: 1900,
    maxScore: 2600,
    agentTimeSeconds: 1558.943,
    agentTimeLabel: "25m 59s",
    failed: 7,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-55-xhigh",
    agent: "GPT-5.5 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260624T182835Z-4ad8b555 (+2)",
    marker: "5X",
    series: "gpt55",
    effort: "xhigh",
    passRate: 85,
    score: 2200,
    maxScore: 2600,
    agentTimeSeconds: 2462.828,
    agentTimeLabel: "41m 03s",
    failed: 4,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-low",
    agent: "GPT-5.4 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T073231Z-84de082a",
    marker: "4L",
    series: "gpt54",
    effort: "low",
    passRate: 77,
    score: 2000,
    maxScore: 2600,
    agentTimeSeconds: 1064.8,
    agentTimeLabel: "17m 45s",
    failed: 6,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-medium",
    agent: "GPT-5.4 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T073227Z-76c2964d",
    marker: "4M",
    series: "gpt54",
    effort: "medium",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 1254.766,
    agentTimeLabel: "20m 55s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-high",
    agent: "GPT-5.4 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260625T073228Z-a5a4a383",
    marker: "4H",
    series: "gpt54",
    effort: "high",
    passRate: 85,
    score: 2200,
    maxScore: 2600,
    agentTimeSeconds: 1696.457,
    agentTimeLabel: "28m 16s",
    failed: 4,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-xhigh",
    agent: "GPT-5.4 via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260624T190640Z-fa04a19c (+2)",
    marker: "4X",
    series: "gpt54",
    effort: "xhigh",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 2402.024,
    agentTimeLabel: "40m 02s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-mini-low",
    agent: "GPT-5.4 mini via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260627T154139Z-a762c204",
    marker: "ML",
    series: "gpt54Mini",
    effort: "low",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 830.799,
    agentTimeLabel: "13m 51s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-mini-medium",
    agent: "GPT-5.4 mini via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260627T154149Z-11277553",
    marker: "MM",
    series: "gpt54Mini",
    effort: "medium",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 1079.313,
    agentTimeLabel: "17m 59s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-mini-high",
    agent: "GPT-5.4 mini via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260627T154205Z-4e04ba57",
    marker: "MH",
    series: "gpt54Mini",
    effort: "high",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 1745.33,
    agentTimeLabel: "29m 05s",
    failed: 5,
    timeouts: 1,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "gpt-54-mini-xhigh",
    agent: "GPT-5.4 mini via Codex CLI",
    kind: "codex",
    corpus: "26-task corpus",
    runId: "20260624T194359Z-268b0abe (+2)",
    marker: "MX",
    series: "gpt54Mini",
    effort: "xhigh",
    passRate: 73,
    score: 1900,
    maxScore: 2600,
    agentTimeSeconds: 2386.295,
    agentTimeLabel: "39m 46s",
    failed: 7,
    timeouts: 3,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "claude-opus-48-low",
    agent: "Claude Opus 4.8",
    kind: "claude",
    corpus: "26-task corpus",
    runId: "20260627T214634Z-4e66a550",
    marker: "OL",
    series: "claudeOpus48",
    effort: "low",
    passRate: 73,
    score: 1900,
    maxScore: 2600,
    agentTimeSeconds: 541.667,
    agentTimeLabel: "9m 02s",
    failed: 7,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "claude-opus-48-high",
    agent: "Claude Opus 4.8",
    kind: "claude",
    corpus: "26-task corpus",
    runId: "20260628T071803Z-ca820a9b",
    marker: "OH",
    series: "claudeOpus48",
    effort: "high",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 777.507,
    agentTimeLabel: "12m 58s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
  {
    id: "claude-opus-48-xhigh",
    agent: "Claude Opus 4.8",
    kind: "claude",
    corpus: "26-task corpus",
    runId: "20260628T154937Z-ed26a81d",
    marker: "OX",
    series: "claudeOpus48",
    effort: "xhigh",
    passRate: 81,
    score: 2100,
    maxScore: 2600,
    agentTimeSeconds: 1323.047,
    agentTimeLabel: "22m 03s",
    failed: 5,
    timeouts: 0,
    completedTasks: 26,
    totalTasks: 26,
    status: "complete",
  },
];

const generatedLeaderboardRuns = generatedTrialRows as LeaderboardRun[];
const generatedCorpora = new Set(generatedLeaderboardRuns.map((run) => run.corpus));

export const leaderboardRuns: LeaderboardRun[] = [
  ...originalLeaderboardRuns.filter((run) => !generatedCorpora.has(run.corpus)),
  ...generatedLeaderboardRuns,
];

export const taskExamples = [
  {
    title: "Respect NixOS, Home Manager, and nix-darwin boundaries",
    description: "Keep module outputs separated instead of leaking options across systems.",
    area: "modules",
    difficulty: "hard",
  },
  {
    title: "Patch Python CUDA package inputs",
    description: "Repair Python/CUDA packaging without falling back to generic Linux path guesses.",
    area: "packages",
    difficulty: "hard",
  },
  {
    title: "Compose module paths from arguments",
    description: "Build paths with Nix values while avoiding string interpolation traps.",
    area: "nix-language",
    difficulty: "medium",
  },
  {
    title: "Debug network symptoms without false leads",
    description: "Explain the observed NixOS service behavior without chasing a plausible but wrong network diagnosis.",
    area: "debugging",
    difficulty: "medium",
  },
  {
    title: "Manage home files declaratively",
    description: "Use Home Manager file and XDG options rather than imperative setup.",
    area: "modules",
    difficulty: "easy",
  },
  {
    title: "Pin a GitHub source fetcher",
    description: "Preserve the fixed-output fetcher contract with a commit pin and SRI hash.",
    area: "fetchers",
    difficulty: "easy",
  },
];

export const difficultyDistribution = [
  ["7", "easy tasks for syntax, lookup, stale options, and small contracts"],
  ["16", "medium repairs across flakes, containers, issue reports, overlays, packaging, and shell integration"],
  ["6", "hard tasks for modules, overlays, portals, Rust purity, and Python/CUDA package inputs"],
] as const;

export const methodSteps = [
  ["copy", "Starter files and the prompt enter a clean temporary workdir."],
  ["edit", "The agent reads NIXBENCH_PROMPT.md and modifies only local files."],
  ["check", "A hidden shell evaluator scores the final tree after the agent exits."],
  ["record", "Logs, timing, score JSON, and the final diff are written under results/."],
] as const;

export const explainerCards = [
  {
    kicker: "contamination",
    title: "Original repair tasks",
    description: "Tasks are written for this corpus rather than lifted from merged patches, which keeps the answer out of the visible prompt.",
  },
  {
    kicker: "scope",
    title: "Nix-specific failure surfaces",
    description: "The corpus covers flakes, modules, overlays, derivations, fetchers, Home Manager, shell escaping, and package contracts.",
  },
  {
    kicker: "verification",
    title: "Hand-written checks",
    description: "Each task has a shell evaluator that checks behavior with small fake package sets and libraries instead of relying on LLM judging.",
  },
  {
    kicker: "artifacts",
    title: "Diff-backed runs",
    description: "Every run records logs, timings, pass state, score JSON, and the final diff so failures can be inspected after the benchmark ends.",
  },
];

const baseTaskResults: TaskResult[] = [
  {
    task: "container-native-vs-oci",
    area: "Modules",
    results: {
      gpt55: { status: "fail", seconds: 53.014 },
      gpt54: { status: "fail", seconds: 48.331 },
      gpt54Mini: { status: "fail", seconds: 75.941 },
      claudeOpus48: { status: "fail", seconds: 27.818 },
    },
  },
  {
    task: "debug-infinite-recursion",
    area: "Debugging",
    results: {
      gpt55: { status: "pass", seconds: 62.837 },
      gpt54: { status: "pass", seconds: 42.717 },
      gpt54Mini: { status: "pass", seconds: 37.893 },
      claudeOpus48: { status: "pass", seconds: 53.997 },
    },
  },
  {
    task: "debug-network-false-lead",
    area: "Debugging",
    results: {
      gpt55: { status: "fail", seconds: 212.943 },
      gpt54: { status: "fail", seconds: 193.1 },
      gpt54Mini: { status: "fail", seconds: 240.011 },
      claudeOpus48: { status: "fail", seconds: 182.497 },
    },
  },
  {
    task: "devshell-tooling-contract",
    area: "Dev shells",
    results: {
      gpt55: { status: "pass", seconds: 46.855 },
      gpt54: { status: "pass", seconds: 131.105 },
      gpt54Mini: { status: "pass", seconds: 53.211 },
      claudeOpus48: { status: "pass", seconds: 39.024 },
    },
  },
  {
    task: "fetcher-source-pin",
    area: "Fetchers",
    results: {
      gpt55: { status: "pass", seconds: 96.78 },
      gpt54: { status: "pass", seconds: 138.408 },
      gpt54Mini: { status: "pass", seconds: 106.969 },
      claudeOpus48: { status: "pass", seconds: 36.918 },
    },
  },
  {
    task: "fhs-binary-wrapper",
    area: "Packaging",
    results: {
      gpt55: { status: "pass", seconds: 97.981 },
      gpt54: { status: "pass", seconds: 68.456 },
      gpt54Mini: { status: "pass", seconds: 142.69 },
      claudeOpus48: { status: "pass", seconds: 47.062 },
    },
  },
  {
    task: "flake-input-package-selection",
    area: "Flakes",
    results: {
      gpt55: { status: "pass", seconds: 29.27 },
      gpt54: { status: "pass", seconds: 63.853 },
      gpt54Mini: { status: "pass", seconds: 24.384 },
      claudeOpus48: { status: "pass", seconds: 21.655 },
    },
  },
  {
    task: "flake-per-system-outputs",
    area: "Flakes",
    results: {
      gpt55: { status: "pass", seconds: 212.351 },
      gpt54: { status: "pass", seconds: 184.692 },
      gpt54Mini: { status: "fail", seconds: 240.006 },
      claudeOpus48: { status: "pass", seconds: 74.898 },
    },
  },
  {
    task: "home-manager-extra-special-args",
    area: "Flakes",
    results: {
      gpt55: { status: "pass", seconds: 135.451 },
      gpt54: { status: "pass", seconds: 138.396 },
      gpt54Mini: { status: "pass", seconds: 80.458 },
      claudeOpus48: { status: "pass", seconds: 131.881 },
    },
  },
  {
    task: "home-manager-wsl-module-import",
    area: "Modules",
    results: {
      gpt55: { status: "pass", seconds: 39.315 },
      gpt54: { status: "pass", seconds: 77.951 },
      gpt54Mini: { status: "pass", seconds: 44.286 },
      claudeOpus48: { status: "pass", seconds: 36.522 },
    },
  },
  {
    task: "home-manager-xdg-files",
    area: "Modules",
    results: {
      gpt55: { status: "pass", seconds: 45.746 },
      gpt54: { status: "pass", seconds: 49.141 },
      gpt54Mini: { status: "pass", seconds: 56.894 },
      claudeOpus48: { status: "pass", seconds: 33.051 },
    },
  },
  {
    task: "issue-report-quality",
    area: "Debugging",
    results: {
      gpt55: { status: "fail", seconds: 38.789 },
      gpt54: { status: "fail", seconds: 50.178 },
      gpt54Mini: { status: "fail", seconds: 39.132 },
      claudeOpus48: { status: "fail", seconds: 89.338 },
    },
  },
  {
    task: "lang-attrsets-normalize",
    area: "Nix language",
    results: {
      gpt55: { status: "pass", seconds: 87.333 },
      gpt54: { status: "pass", seconds: 79.985 },
      gpt54Mini: { status: "pass", seconds: 74.621 },
      claudeOpus48: { status: "pass", seconds: 67.707 },
    },
  },
  {
    task: "module-path-composition",
    area: "Nix language",
    results: {
      gpt55: { status: "pass", seconds: 98.125 },
      gpt54: { status: "pass", seconds: 51.707 },
      gpt54Mini: { status: "pass", seconds: 49.585 },
      claudeOpus48: { status: "pass", seconds: 38.249 },
    },
  },
  {
    task: "module-service-options",
    area: "Modules",
    results: {
      gpt55: { status: "fail", seconds: 124.782 },
      gpt54: { status: "pass", seconds: 106.574 },
      gpt54Mini: { status: "pass", seconds: 84.646 },
      claudeOpus48: { status: "pass", seconds: 81.239 },
    },
  },
  {
    task: "module-stale-option-migration",
    area: "Modules",
    results: {
      gpt55: { status: "pass", seconds: 41.536 },
      gpt54: { status: "pass", seconds: 37.715 },
      gpt54Mini: { status: "pass", seconds: 63.129 },
      claudeOpus48: { status: "pass", seconds: 29.867 },
    },
  },
  {
    task: "module-system-boundaries",
    area: "Modules",
    results: {
      gpt55: { status: "pass", seconds: 55.574 },
      gpt54: { status: "pass", seconds: 81.811 },
      gpt54Mini: { status: "pass", seconds: 40.781 },
      claudeOpus48: { status: "pass", seconds: 45.304 },
    },
  },
  {
    task: "mutable-config-home-manager",
    area: "Modules",
    results: {
      gpt55: { status: "pass", seconds: 82.836 },
      gpt54: { status: "pass", seconds: 42.759 },
      gpt54Mini: { status: "pass", seconds: 63.323 },
      claudeOpus48: { status: "pass", seconds: 38.208 },
    },
  },
  {
    task: "nushell-command-not-found",
    area: "Modules",
    results: {},
  },
  {
    task: "overlay-module-boundary",
    area: "Overlays",
    results: {
      gpt55: { status: "pass", seconds: 69.118 },
      gpt54: { status: "pass", seconds: 58.39 },
      gpt54Mini: { status: "pass", seconds: 95.757 },
      claudeOpus48: { status: "pass", seconds: 34.2 },
    },
  },
  {
    task: "overlay-override-package",
    area: "Overlays",
    results: {
      gpt55: { status: "pass", seconds: 44.024 },
      gpt54: { status: "pass", seconds: 70.858 },
      gpt54Mini: { status: "pass", seconds: 50.548 },
      claudeOpus48: { status: "pass", seconds: 48.639 },
    },
  },
  {
    task: "package-name-lookup-contract",
    area: "Packaging",
    results: {
      gpt55: { status: "pass", seconds: 51.164 },
      gpt54: { status: "pass", seconds: 53.972 },
      gpt54Mini: { status: "pass", seconds: 26.632 },
      claudeOpus48: { status: "pass", seconds: 36.417 },
    },
  },
  {
    task: "package-python-application",
    area: "Packaging",
    results: {
      gpt55: { status: "pass", seconds: 133.51 },
      gpt54: { status: "fail", seconds: 185.563 },
      gpt54Mini: { status: "fail", seconds: 240.009 },
      claudeOpus48: { status: "pass", seconds: 51.509 },
    },
  },
  {
    task: "package-stdenv-cli",
    area: "Packaging",
    results: {
      gpt55: { status: "pass", seconds: 182.157 },
      gpt54: { status: "fail", seconds: 203.113 },
      gpt54Mini: { status: "fail", seconds: 184.5 },
      claudeOpus48: { status: "fail", seconds: 30.315 },
    },
  },
  {
    task: "purity-wrapper-derivation",
    area: "Purity",
    results: {
      gpt55: { status: "pass", seconds: 145.04 },
      gpt54: { status: "pass", seconds: 107.322 },
      gpt54Mini: { status: "pass", seconds: 79.14 },
      claudeOpus48: { status: "pass", seconds: 100.403 },
    },
  },
  {
    task: "python-cuda-uv2nix-patch",
    area: "Packaging",
    results: {
      gpt55: { status: "pass", seconds: 44.377 },
      gpt54: { status: "pass", seconds: 52.841 },
      gpt54Mini: { status: "pass", seconds: 68.93 },
      claudeOpus48: { status: "pass", seconds: 35.43 },
    },
  },
  {
    task: "rust-no-network-build",
    area: "Packaging",
    results: {},
  },
  {
    task: "string-escaping-systemd",
    area: "Nix language",
    results: {
      gpt55: { status: "pass", seconds: 231.92 },
      gpt54: { status: "pass", seconds: 83.086 },
      gpt54Mini: { status: "fail", seconds: 122.819 },
      claudeOpus48: { status: "fail", seconds: 111.591 },
    },
  },
  {
    task: "xdg-portal-merge",
    area: "Modules",
    results: {},
  },
];

const gpt56TaskResults: Record<string, Partial<Record<ModelKey, TaskRunCell>>> = {
  "container-native-vs-oci": {
    gpt56Sol: { status: "fail", seconds: 41.494 },
    gpt56Terra: { status: "fail", seconds: 32.757 },
    gpt56Luna: { status: "fail", seconds: 26.463 },
  },
  "debug-infinite-recursion": {
    gpt56Sol: { status: "pass", seconds: 40.893 },
    gpt56Terra: { status: "pass", seconds: 43.494 },
    gpt56Luna: { status: "pass", seconds: 47.392 },
  },
  "debug-network-false-lead": {
    gpt56Sol: { status: "fail", seconds: 104.979 },
    gpt56Terra: { status: "fail", seconds: 82.848 },
    gpt56Luna: { status: "fail", seconds: 130.718 },
  },
  "devshell-tooling-contract": {
    gpt56Sol: { status: "pass", seconds: 60.506 },
    gpt56Terra: { status: "pass", seconds: 56.777 },
    gpt56Luna: { status: "pass", seconds: 50.976 },
  },
  "fetcher-source-pin": {
    gpt56Sol: { status: "pass", seconds: 53.76 },
    gpt56Terra: { status: "pass", seconds: 26.074 },
    gpt56Luna: { status: "pass", seconds: 23.014 },
  },
  "fhs-binary-wrapper": {
    gpt56Sol: { status: "pass", seconds: 51.125 },
    gpt56Terra: { status: "pass", seconds: 47.589 },
    gpt56Luna: { status: "pass", seconds: 43.659 },
  },
  "flake-input-package-selection": {
    gpt56Sol: { status: "pass", seconds: 31.338 },
    gpt56Terra: { status: "pass", seconds: 36.829 },
    gpt56Luna: { status: "pass", seconds: 32.13 },
  },
  "flake-per-system-outputs": {
    gpt56Sol: { status: "pass", seconds: 74.092 },
    gpt56Terra: { status: "pass", seconds: 53.902 },
    gpt56Luna: { status: "pass", seconds: 87.568 },
  },
  "home-manager-extra-special-args": {
    gpt56Sol: { status: "pass", seconds: 43.154 },
    gpt56Terra: { status: "pass", seconds: 25.821 },
    gpt56Luna: { status: "pass", seconds: 21.894 },
  },
  "home-manager-wsl-module-import": {
    gpt56Sol: { status: "pass", seconds: 39.71 },
    gpt56Terra: { status: "pass", seconds: 36.565 },
    gpt56Luna: { status: "pass", seconds: 31.609 },
  },
  "home-manager-xdg-files": {
    gpt56Sol: { status: "pass", seconds: 34.339 },
    gpt56Terra: { status: "pass", seconds: 25.873 },
    gpt56Luna: { status: "pass", seconds: 28.093 },
  },
  "issue-report-quality": {
    gpt56Sol: { status: "fail", seconds: 49.075 },
    gpt56Terra: { status: "fail", seconds: 36.825 },
    gpt56Luna: { status: "fail", seconds: 28.739 },
  },
  "lang-attrsets-normalize": {
    gpt56Sol: { status: "pass", seconds: 80.503 },
    gpt56Terra: { status: "pass", seconds: 56.071 },
    gpt56Luna: { status: "pass", seconds: 68.403 },
  },
  "module-path-composition": {
    gpt56Sol: { status: "pass", seconds: 47.125 },
    gpt56Terra: { status: "pass", seconds: 36.09 },
    gpt56Luna: { status: "pass", seconds: 43.837 },
  },
  "module-service-options": {
    gpt56Sol: { status: "fail", seconds: 64.136 },
    gpt56Terra: { status: "fail", seconds: 41.019 },
    gpt56Luna: { status: "fail", seconds: 67.811 },
  },
  "module-stale-option-migration": {
    gpt56Sol: { status: "pass", seconds: 38.259 },
    gpt56Terra: { status: "pass", seconds: 37.329 },
    gpt56Luna: { status: "pass", seconds: 19.692 },
  },
  "module-system-boundaries": {
    gpt56Sol: { status: "pass", seconds: 41.109 },
    gpt56Terra: { status: "pass", seconds: 40.564 },
    gpt56Luna: { status: "pass", seconds: 29.833 },
  },
  "mutable-config-home-manager": {
    gpt56Sol: { status: "pass", seconds: 44.159 },
    gpt56Terra: { status: "pass", seconds: 41.231 },
    gpt56Luna: { status: "fail", seconds: 46.693 },
  },
  "nushell-command-not-found": {
    gpt56Sol: { status: "fail", seconds: 50.434 },
    gpt56Terra: { status: "fail", seconds: 60 },
    gpt56Luna: { status: "fail", seconds: 44.147 },
  },
  "overlay-module-boundary": {
    gpt56Sol: { status: "pass", seconds: 58.426 },
    gpt56Terra: { status: "pass", seconds: 28.979 },
    gpt56Luna: { status: "pass", seconds: 34.202 },
  },
  "overlay-override-package": {
    gpt56Sol: { status: "pass", seconds: 53.936 },
    gpt56Terra: { status: "fail", seconds: 32.809 },
    gpt56Luna: { status: "pass", seconds: 61.16 },
  },
  "package-name-lookup-contract": {
    gpt56Sol: { status: "pass", seconds: 38.986 },
    gpt56Terra: { status: "pass", seconds: 41.348 },
    gpt56Luna: { status: "pass", seconds: 53.941 },
  },
  "package-python-application": {
    gpt56Sol: { status: "pass", seconds: 69.301 },
    gpt56Terra: { status: "fail", seconds: 46.019 },
    gpt56Luna: { status: "fail", seconds: 42.057 },
  },
  "package-stdenv-cli": {
    gpt56Sol: { status: "fail", seconds: 72.615 },
    gpt56Terra: { status: "fail", seconds: 63.282 },
    gpt56Luna: { status: "pass", seconds: 67.383 },
  },
  "purity-wrapper-derivation": {
    gpt56Sol: { status: "pass", seconds: 39.025 },
    gpt56Terra: { status: "pass", seconds: 37.979 },
    gpt56Luna: { status: "fail", seconds: 52.544 },
  },
  "python-cuda-uv2nix-patch": {
    gpt56Sol: { status: "pass", seconds: 51.792 },
    gpt56Terra: { status: "pass", seconds: 34.846 },
    gpt56Luna: { status: "pass", seconds: 32.13 },
  },
  "rust-no-network-build": {
    gpt56Sol: { status: "fail", seconds: 56.469 },
    gpt56Terra: { status: "fail", seconds: 37.749 },
    gpt56Luna: { status: "fail", seconds: 64.052 },
  },
  "string-escaping-systemd": {
    gpt56Sol: { status: "pass", seconds: 70.27 },
    gpt56Terra: { status: "pass", seconds: 43.245 },
    gpt56Luna: { status: "pass", seconds: 110.963 },
  },
  "xdg-portal-merge": {
    gpt56Sol: { status: "fail", seconds: 90.797 },
    gpt56Terra: { status: "fail", seconds: 38.291 },
    gpt56Luna: { status: "fail", seconds: 36.143 },
  },
};

export const taskResults: TaskResult[] = baseTaskResults.map((task) => ({
  ...task,
  results: {
    ...task.results,
    ...gpt56TaskResults[task.task],
  },
}));

export const failureNotes = [
  {
    kicker: "container",
    title: "Native-container outcome",
    description: "The xhigh/default baseline rows did not pass the native NixOS container task; GPT-5.5 low passed it in the effort sweep.",
  },
  {
    kicker: "evidence",
    title: "Debugging and reports",
    description: "The false-lead debugging task and issue-report task were not passed by any row in this set.",
  },
  {
    kicker: "package",
    title: "Packaging variation",
    description: "The Python application and stdenv CLI tasks show different pass patterns across models and effort levels.",
  },
  {
    kicker: "language",
    title: "String escaping",
    description: "GPT-5.5 and GPT-5.4 passed the baseline string-escaping task; GPT-5.4 mini and Claude Opus 4.8 did not.",
  },
];

export function passedTasks(run: LeaderboardRun) {
  return run.completedTasks - run.failed;
}

export function formatDuration(seconds: number) {
  if (seconds >= 60) {
    const minutes = Math.floor(seconds / 60);
    const remainder = Math.round(seconds % 60);
    return remainder === 0 ? `${minutes}m` : `${minutes}m ${remainder}s`;
  }

  return `${Math.round(seconds)}s`;
}

export function formatMinutes(seconds: number) {
  return Math.round((seconds / 60) * 10) / 10;
}

const tCritical95: Record<number, number> = {
  1: 12.706,
  2: 4.303,
  3: 3.182,
  4: 2.776,
  5: 2.571,
  6: 2.447,
  7: 2.365,
  8: 2.306,
  9: 2.262,
  10: 2.228,
  11: 2.201,
  12: 2.179,
  13: 2.16,
  14: 2.145,
  15: 2.131,
  16: 2.12,
  17: 2.11,
  18: 2.101,
  19: 2.093,
  20: 2.086,
  21: 2.08,
  22: 2.074,
  23: 2.069,
  24: 2.064,
  25: 2.06,
  26: 2.056,
  27: 2.052,
  28: 2.048,
  29: 2.045,
  30: 2.042,
};

function estimate95(values: number[], bounds: { lower?: number; upper?: number } = {}): Estimate {
  if (values.length === 0) {
    throw new Error("Cannot estimate an empty benchmark sample.");
  }

  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  if (values.length === 1) {
    return { n: 1, mean, min: values[0], max: values[0] };
  }

  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (values.length - 1);
  const standardDeviation = Math.sqrt(variance);
  const critical = tCritical95[values.length - 1] ?? 1.96;
  const ci95Margin = (critical * standardDeviation) / Math.sqrt(values.length);
  const ci95Low = Math.max(bounds.lower ?? -Infinity, mean - ci95Margin);
  const ci95High = Math.min(bounds.upper ?? Infinity, mean + ci95Margin);

  return {
    n: values.length,
    mean,
    min: Math.min(...values),
    max: Math.max(...values),
    standardDeviation,
    ci95Low,
    ci95High,
    ci95Margin,
  };
}

export function aggregateLeaderboardRuns(runs: LeaderboardRun[]): LeaderboardAggregate[] {
  const groups = new Map<string, LeaderboardRun[]>();

  for (const run of runs) {
    const key = run.configurationId ?? `${run.corpus}:${run.series ?? run.id}:${run.effort ?? "default"}`;
    const group = groups.get(key) ?? [];
    group.push(run);
    groups.set(key, group);
  }

  return [...groups.entries()].map(([id, trials]) => {
    const first = trials[0];
    const taskCount = first.totalTasks;

    return {
      id,
      agent: first.agent,
      kind: first.kind,
      corpus: first.corpus,
      marker: first.marker,
      series: first.series,
      effort: first.effort,
      taskCount,
      trialCount: trials.length,
      trials,
      passedTasks: estimate95(trials.map(passedTasks), { lower: 0, upper: taskCount }),
      scoreRate: estimate95(trials.map((run) => run.score / run.maxScore), { lower: 0, upper: 1 }),
      agentSecondsPerTask: estimate95(
        trials.map((run) => run.agentTimeSeconds / run.totalTasks),
        { lower: 0 },
      ),
      agentTimeSeconds: estimate95(trials.map((run) => run.agentTimeSeconds), { lower: 0 }),
      totalTimeouts: trials.reduce((sum, run) => sum + run.timeouts, 0),
      provenance: trials.some((run) => run.provenance === "composite" || run.runId.includes("(+2)"))
        ? "composite"
        : "trial",
    };
  });
}

function effortLabelFor(aggregates: LeaderboardAggregate[]) {
  const labels = [...new Set(aggregates.map((aggregate) => aggregate.effort ?? "default"))];
  return labels.length > 0 ? labels.join(", ") : "none";
}

export const leaderboardAggregates = aggregateLeaderboardRuns(leaderboardRuns);
export const currentLeaderboardAggregates = leaderboardAggregates.filter(
  (aggregate) => aggregate.corpus === currentCorpusLabel,
);
export const currentEvidenceSummary = {
  configurations: currentLeaderboardAggregates.length,
  trials: currentLeaderboardAggregates.reduce((sum, aggregate) => sum + aggregate.trialCount, 0),
  models: new Set(currentLeaderboardAggregates.map((aggregate) => aggregate.series).filter(Boolean)).size,
  replicatedConfigurations: currentLeaderboardAggregates.filter((aggregate) => aggregate.trialCount > 1).length,
};

export const heroStats = [
  ["tasks", String(currentCorpusTaskCount)],
  ["areas", String(new Set(taskResults.map((task) => task.area)).size)],
  ["evaluators", String(currentCorpusTaskCount)],
  ["current trials", String(currentEvidenceSummary.trials)],
] as const;

export const resultsDateRangeLabel = buildDateRangeLabel(leaderboardRuns.map((run) => run.runId));

export const resultOverviewStats = [
  ["models", String(resultColumns.length)],
  ["configurations", String(leaderboardAggregates.length)],
  ["recorded trials", String(leaderboardRuns.length)],
  ["task rows", String(taskResults.length)],
] as const;

export const modelSummaries = resultColumns.map((column) => {
  const aggregates = leaderboardAggregates.filter(
    (aggregate) => aggregate.series === column.key && aggregate.corpus === column.corpus,
  );
  const trialCount = aggregates.reduce((sum, aggregate) => sum + aggregate.trialCount, 0);
  const totalTimeouts = aggregates.reduce((sum, aggregate) => sum + aggregate.totalTimeouts, 0);
  const taskMeans = aggregates.map((aggregate) => aggregate.passedTasks.mean);
  const secondsPerTask = aggregates.map((aggregate) => aggregate.agentSecondsPerTask.mean);

  return {
    ...column,
    kind: aggregates[0]?.kind,
    configurationCount: aggregates.length,
    trialCount,
    replicatedConfigurationCount: aggregates.filter((aggregate) => aggregate.trialCount > 1).length,
    taskRangeLabel:
      taskMeans.length > 0 ? `${Math.min(...taskMeans).toFixed(1)}–${Math.max(...taskMeans).toFixed(1)}` : "--",
    secondsPerTaskRangeLabel:
      secondsPerTask.length > 0
        ? `${Math.min(...secondsPerTask).toFixed(1)}–${Math.max(...secondsPerTask).toFixed(1)}s`
        : "--",
    effortLabel: effortLabelFor(aggregates),
    timeoutLabel: String(totalTimeouts),
  };
});

export const modelTaskSummaries = resultColumns.map((column) => {
  const cells = taskResults.map((task) => task.results[column.key]).filter((cell): cell is TaskRunCell => Boolean(cell));
  const timedCells = cells.filter((cell) => cell.seconds != null);
  const passed = cells.filter((cell) => cell.status === "pass").length;
  const averageSeconds =
    timedCells.length > 0
      ? timedCells.reduce((sum, cell) => sum + (cell.seconds ?? 0), 0) / timedCells.length
      : undefined;

  return {
    ...column,
    total: cells.length,
    passed,
    failed: cells.length - passed,
    passRate: cells.length > 0 ? Math.round((passed / cells.length) * 100) : 0,
    passLabel: cells.length > 0 ? `${passed}/${cells.length}` : "--",
    averageTimeLabel: averageSeconds == null ? "--" : formatDuration(averageSeconds),
  };
});

function buildDateRangeLabel(runIds: string[]) {
  const dates = runIds
    .map((runId) => runId.match(/^(\d{4})(\d{2})(\d{2})/))
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match) => new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]))))
    .sort((a, b) => a.getTime() - b.getTime());

  if (dates.length === 0) return "No dated runs";
  const first = dates[0];
  const last = dates[dates.length - 1];
  const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  if (first.getUTCFullYear() === last.getUTCFullYear()) {
    if (first.getUTCMonth() === last.getUTCMonth()) {
      return `${months[first.getUTCMonth()]} ${first.getUTCDate()}–${last.getUTCDate()}, ${last.getUTCFullYear()}`;
    }
    return `${months[first.getUTCMonth()]} ${first.getUTCDate()}–${months[last.getUTCMonth()]} ${last.getUTCDate()}, ${last.getUTCFullYear()}`;
  }
  return `${months[first.getUTCMonth()]} ${first.getUTCDate()}, ${first.getUTCFullYear()}–${months[last.getUTCMonth()]} ${last.getUTCDate()}, ${last.getUTCFullYear()}`;
}
