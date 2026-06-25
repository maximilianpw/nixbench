export type AgentKind = "codex" | "claude";
export type RunStatus = "complete";
export type TaskStatus = "pass" | "fail";
export type ModelKey = "gpt55" | "gpt54" | "gpt54Mini" | "claudeOpus48";

export type LeaderboardRun = {
  id: string;
  agent: string;
  kind: AgentKind;
  corpus: string;
  runId: string;
  marker: string;
  passRate: number;
  score: number;
  maxScore: number;
  agentTimeSeconds: number;
  agentTimeLabel: string;
  failed: number;
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
  ["tasks", "24"],
  ["areas", "9"],
  ["evaluators", "24"],
  ["scored runs", "4"],
] as const;

export const leaderboardRuns: LeaderboardRun[] = [
  {
    id: "gpt-55",
    agent: "GPT-5.5 via Codex CLI",
    kind: "codex",
    corpus: "24-task corpus",
    runId: "20260624T182835Z-4ad8b555",
    marker: "5",
    passRate: 83,
    score: 2000,
    maxScore: 2400,
    agentTimeSeconds: 2258.259,
    agentTimeLabel: "37m 38s",
    failed: 4,
    completedTasks: 24,
    totalTasks: 24,
    status: "complete",
    current: true,
  },
  {
    id: "gpt-54",
    agent: "GPT-5.4 via Codex CLI",
    kind: "codex",
    corpus: "24-task corpus",
    runId: "20260624T190640Z-fa04a19c",
    marker: "4",
    passRate: 79,
    score: 1900,
    maxScore: 2400,
    agentTimeSeconds: 2205.238,
    agentTimeLabel: "36m 45s",
    failed: 5,
    completedTasks: 24,
    totalTasks: 24,
    status: "complete",
  },
  {
    id: "gpt-54-mini",
    agent: "GPT-5.4 mini via Codex CLI",
    kind: "codex",
    corpus: "24-task corpus",
    runId: "20260624T194359Z-268b0abe",
    marker: "M",
    passRate: 71,
    score: 1700,
    maxScore: 2400,
    agentTimeSeconds: 2210.08,
    agentTimeLabel: "36m 50s",
    failed: 7,
    completedTasks: 24,
    totalTasks: 24,
    status: "complete",
  },
  {
    id: "claude-opus-48",
    agent: "Claude Opus 4.8",
    kind: "claude",
    corpus: "24-task corpus",
    runId: "20260624T202141Z-881ef1e9",
    marker: "O",
    passRate: 79,
    score: 1900,
    maxScore: 2400,
    agentTimeSeconds: 1357.658,
    agentTimeLabel: "22m 38s",
    failed: 5,
    completedTasks: 24,
    totalTasks: 24,
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
  ["13", "medium repairs across flakes, containers, issue reports, and packaging"],
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
  ["Top full score", "2000"],
  ["Best full pass", "20/24"],
  ["Full runs", "4"],
  ["Runner-up score", "1900"],
] as const;

export const verdicts = [
  {
    label: "Leader",
    value: "GPT-5.5",
    description: "The strongest completed run scored 2000/2400 with 20 passes across the full 24-task corpus.",
  },
  {
    label: "Spread",
    value: "17-20 passes",
    description: "The four completed runs landed within a three-task band while sharing several persistent failures.",
  },
  {
    label: "Runner-up",
    value: "GPT-5.4 + Claude",
    description: "GPT-5.4 and Claude Opus 4.8 both scored 1900/2400, but failed different packaging and language tasks.",
  },
];

export const modelRunCards = [
  {
    kind: "codex" as const,
    agent: "GPT-5.5 via Codex CLI",
    runId: "20260624T182835Z-4ad8b555",
    score: "2000",
    maxScore: "2400",
    status: "complete",
    metrics: [
      ["Passed", "20"],
      ["Failed", "4"],
      ["Timeouts", "0"],
      ["Agent time", "37m 38s"],
    ],
  },
  {
    kind: "codex" as const,
    agent: "GPT-5.4 via Codex CLI",
    runId: "20260624T190640Z-fa04a19c",
    score: "1900",
    maxScore: "2400",
    status: "complete",
    metrics: [
      ["Passed", "19"],
      ["Failed", "5"],
      ["Timeouts", "0"],
      ["Agent time", "36m 45s"],
    ],
  },
  {
    kind: "codex" as const,
    agent: "GPT-5.4 mini via Codex CLI",
    runId: "20260624T194359Z-268b0abe",
    score: "1700",
    maxScore: "2400",
    status: "complete",
    metrics: [
      ["Passed", "17"],
      ["Failed", "7"],
      ["Timeouts", "3"],
      ["Agent time", "36m 50s"],
    ],
  },
  {
    kind: "claude" as const,
    agent: "Claude Opus 4.8",
    runId: "20260624T202141Z-881ef1e9",
    score: "1900",
    maxScore: "2400",
    status: "complete",
    metrics: [
      ["Passed", "19"],
      ["Failed", "5"],
      ["Timeouts", "0"],
      ["Agent time", "22m 38s"],
    ],
  },
];

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
    title: "Shared native-container miss",
    description: "All four runs failed the native NixOS container task, making it the clearest common regression target.",
  },
  {
    kicker: "evidence",
    title: "Debugging stayed brittle",
    description: "Every run missed the false-lead debugging task and the verifiable issue-report task.",
  },
  {
    kicker: "package",
    title: "Packaging split the GPT runs",
    description: "GPT-5.5 solved the Python application and stdenv CLI tasks that both GPT-5.4 variants missed.",
  },
  {
    kicker: "language",
    title: "String escaping split the runners",
    description: "GPT-5.5 and GPT-5.4 passed string escaping, while GPT-5.4 mini and Claude Opus 4.8 failed it.",
  },
];

export function formatMinutes(seconds: number) {
  return Math.round((seconds / 60) * 10) / 10;
}
