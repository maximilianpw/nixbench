export type AgentKind = "codex" | "claude";
export type RunStatus = "complete";
export type TaskStatus = "pass" | "fail";
export type ModelKey = "gpt55" | "gpt54" | "gpt54Mini" | "claudeOpus48";
export type ReasoningEffort = "low" | "medium" | "high" | "xhigh";

export type LeaderboardRun = {
  id: string;
  agent: string;
  kind: AgentKind;
  corpus: string;
  runId: string;
  marker: string;
  series?: ModelKey;
  effort?: ReasoningEffort;
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
  current?: boolean;
  ranked?: boolean;
};

export type ResultColumn = {
  key: ModelKey;
  label: string;
  shortLabel: string;
};

export type TaskRunCell = {
  status: TaskStatus;
  seconds?: number;
};

export type TaskResult = {
  task: string;
  area: string;
  results: Record<ModelKey, TaskRunCell>;
};

export const resultColumns: ResultColumn[] = [
  { key: "gpt55", label: "GPT-5.5", shortLabel: "5.5" },
  { key: "gpt54", label: "GPT-5.4", shortLabel: "5.4" },
  { key: "gpt54Mini", label: "GPT-5.4 mini", shortLabel: "mini" },
  { key: "claudeOpus48", label: "Claude Opus 4.8", shortLabel: "opus" },
];

export const heroStats = [
  ["tasks", "26"],
  ["areas", "9"],
  ["evaluators", "26"],
  ["scored runs", "15"],
] as const;

export const leaderboardRuns: LeaderboardRun[] = [
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
    current: true,
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
  ["15", "medium repairs across flakes, containers, issue reports, overlays, and packaging"],
  ["4", "hard tasks for modules, overlays, and Python/CUDA package inputs"],
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

export const resultStats = [
  ["Highest score", "2200"],
  ["Highest pass count", "22/26"],
  ["Full runs", "15"],
  ["Shortest 22/26 run", "28m 16s"],
] as const;

export const verdicts = [
  {
    label: "Highest score",
    value: "22/26",
    description: "Two rows reached 2200/2600: GPT-5.4 at high effort and GPT-5.5 at xhigh effort.",
  },
  {
    label: "Range",
    value: "19-22 passes",
    description: "The fifteen completed rows span four pass-count values across the full 26-task corpus.",
  },
  {
    label: "Effort",
    value: "Model-specific",
    description: "GPT-5.4 increased from low through high effort; GPT-5.4 mini reached 21/26 at low, medium, and high effort.",
  },
];

export const modelRunCards = leaderboardRuns.map((run) => ({
  kind: run.kind,
  agent: run.effort ? `${run.agent} (${run.effort})` : run.agent,
  runId: run.runId,
  score: String(run.score),
  maxScore: String(run.maxScore),
  status: run.status,
  metrics: [
    ["Passed", String(run.completedTasks - run.failed)],
    ["Failed", String(run.failed)],
    ["Timeouts", String(run.timeouts)],
    ["Agent time", run.agentTimeLabel],
  ] satisfies [string, string][],
}));

export const taskResults: TaskResult[] = [
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
    task: "string-escaping-systemd",
    area: "Nix language",
    results: {
      gpt55: { status: "pass", seconds: 231.92 },
      gpt54: { status: "pass", seconds: 83.086 },
      gpt54Mini: { status: "fail", seconds: 122.819 },
      claudeOpus48: { status: "fail", seconds: 111.591 },
    },
  },
];

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

export function formatMinutes(seconds: number) {
  return Math.round((seconds / 60) * 10) / 10;
}
