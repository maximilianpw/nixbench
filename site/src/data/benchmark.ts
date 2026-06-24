export type AgentKind = "codex" | "claude";

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
  current?: boolean;
};

export type TaskResult = {
  task: string;
  area: string;
  codex: "pass" | "fail";
  claude: "pass" | "fail";
  codexSeconds: number;
  claudeSeconds: number;
  readout: string;
  outcome: "mutual-pass" | "mutual-fail" | "codex-only" | "claude-only";
  timeout?: "codex" | "claude";
};

export const heroStats = [
  ["tasks", "24"],
  ["areas", "9"],
  ["evaluators", "24"],
  ["scored runs", "3"],
] as const;

export const leaderboardRuns: LeaderboardRun[] = [
  {
    id: "codex-current",
    agent: "Codex CLI",
    kind: "codex",
    corpus: "expanded corpus",
    runId: "20260624T102722Z",
    marker: "C",
    passRate: 91,
    score: 1000,
    maxScore: 1100,
    agentTimeSeconds: 943,
    agentTimeLabel: "15m 43s",
    failed: 1,
    current: true,
  },
  {
    id: "codex-baseline",
    agent: "Codex CLI",
    kind: "codex",
    corpus: "ten-task baseline",
    runId: "20260623T082404Z",
    marker: "C",
    passRate: 50,
    score: 500,
    maxScore: 1000,
    agentTimeSeconds: 1148,
    agentTimeLabel: "19m 08s",
    failed: 5,
  },
  {
    id: "claude-baseline",
    agent: "Claude CLI",
    kind: "claude",
    corpus: "ten-task baseline",
    runId: "20260623T093109Z",
    marker: "A",
    passRate: 50,
    score: 500,
    maxScore: 1000,
    agentTimeSeconds: 829,
    agentTimeLabel: "13m 49s",
    failed: 5,
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
  ["Codex score", "500"],
  ["Claude score", "500"],
  ["Pass split", "5-5"],
  ["Timeouts", "1-0"],
] as const;

export const verdicts = [
  {
    label: "Score",
    value: "exact tie",
    description: "Both runs landed at 500/1000 with five passes and five failures.",
  },
  {
    label: "Time",
    value: "Claude -319.7s",
    description: "Claude completed the corpus in 13m 49s versus Codex at 19m 08s.",
  },
  {
    label: "Split tasks",
    value: "1 each",
    description: "Codex alone passed package-stdenv-cli; Claude alone passed purity-wrapper-derivation.",
  },
];

export const baselineRunCards = [
  {
    kind: "codex" as const,
    agent: "Codex CLI",
    runId: "20260623T082404Z",
    score: "500",
    maxScore: "1000",
    metrics: [
      ["Passed", "5"],
      ["Failed", "5"],
      ["Timeouts", "1"],
      ["Agent time", "19m 08s"],
    ],
  },
  {
    kind: "claude" as const,
    agent: "Claude CLI",
    runId: "20260623T093109Z-b488de64",
    score: "500",
    maxScore: "1000",
    metrics: [
      ["Passed", "5"],
      ["Failed", "5"],
      ["Timeouts", "0"],
      ["Agent time", "13m 49s"],
    ],
  },
];

export const taskResults: TaskResult[] = [
  {
    task: "debug-infinite-recursion",
    area: "Debugging",
    codex: "pass",
    claude: "pass",
    codexSeconds: 67.7,
    claudeSeconds: 58.6,
    outcome: "mutual-pass",
    readout: "Both repaired the recursive attrset; Claude was 9.1s faster.",
  },
  {
    task: "devshell-tooling-contract",
    area: "Dev shells",
    codex: "pass",
    claude: "pass",
    codexSeconds: 78.2,
    claudeSeconds: 72.5,
    outcome: "mutual-pass",
    readout: "Both satisfied the shell contract with similar timing.",
  },
  {
    task: "fetcher-source-pin",
    area: "Fetchers",
    codex: "pass",
    claude: "pass",
    codexSeconds: 93,
    claudeSeconds: 43.6,
    outcome: "mutual-pass",
    readout: "Both pinned the source; Claude finished less than half the time.",
  },
  {
    task: "flake-per-system-outputs",
    area: "Flakes",
    codex: "fail",
    claude: "fail",
    codexSeconds: 240,
    claudeSeconds: 119.6,
    outcome: "mutual-fail",
    timeout: "codex",
    readout: "Both missed app metadata; Codex also hit the 240s timeout.",
  },
  {
    task: "lang-attrsets-normalize",
    area: "Nix language",
    codex: "fail",
    claude: "fail",
    codexSeconds: 65.4,
    claudeSeconds: 94.6,
    outcome: "mutual-fail",
    readout: "Both filtered disabled packages too early.",
  },
  {
    task: "module-service-options",
    area: "Modules",
    codex: "fail",
    claude: "fail",
    codexSeconds: 125.3,
    claudeSeconds: 121.9,
    outcome: "mutual-fail",
    readout: "Both reached for helpers absent from the evaluator fake lib.",
  },
  {
    task: "overlay-override-package",
    area: "Overlays",
    codex: "pass",
    claude: "pass",
    codexSeconds: 47.9,
    claudeSeconds: 37.3,
    outcome: "mutual-pass",
    readout: "Both preserved the override shape and metadata.",
  },
  {
    task: "package-python-application",
    area: "Packaging",
    codex: "fail",
    claude: "fail",
    codexSeconds: 73.9,
    claudeSeconds: 169,
    outcome: "mutual-fail",
    readout: "Both selected mit where the evaluator expected asl20.",
  },
  {
    task: "package-stdenv-cli",
    area: "Packaging",
    codex: "pass",
    claude: "fail",
    codexSeconds: 176.6,
    claudeSeconds: 43.5,
    outcome: "codex-only",
    readout: "Codex solved it; Claude returned a function where a set was expected.",
  },
  {
    task: "purity-wrapper-derivation",
    area: "Purity",
    codex: "fail",
    claude: "pass",
    codexSeconds: 180.3,
    claudeSeconds: 68.1,
    outcome: "claude-only",
    readout: "Claude solved it; Codex used unavailable lib.getExe.",
  },
];

export const failureNotes = [
  {
    kicker: "flake",
    title: "Metadata shape",
    description: "Both runs missed required app metadata on the flake task while satisfying the visible structure.",
  },
  {
    kicker: "lib",
    title: "Unavailable helpers",
    description: "Codex used escapeShellArgs and getExe; Claude used concatStringsSep. The fake evaluator library intentionally rejected them.",
  },
  {
    kicker: "license",
    title: "Wrong plausible values",
    description: "Both models chose mit for the Python package where the hidden evaluator expected asl20.",
  },
  {
    kicker: "shape",
    title: "Function versus set",
    description: "Claude's package-stdenv-cli output returned a function where the evaluator expected a package set.",
  },
];

export function formatMinutes(seconds: number) {
  return Math.round((seconds / 60) * 10) / 10;
}
