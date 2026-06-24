(function () {
  const root = document.documentElement;
  const storedTheme = window.localStorage.getItem("nixbench-theme");
  const initialTheme = storedTheme || "light";

  function setTheme(theme) {
    root.dataset.theme = theme;
    window.localStorage.setItem("nixbench-theme", theme);
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const label = theme === "dark" ? "Switch to light theme" : "Switch to dark theme";
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    });
  }

  setTheme(initialTheme);

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      setTheme(root.dataset.theme === "dark" ? "light" : "dark");
    });
  });

  const plot = document.querySelector("[data-score-plot]");
  const modeButtons = document.querySelectorAll("[data-chart-mode]");
  const axisX = document.querySelector("[data-axis-x]");
  const axisY = document.querySelector("[data-axis-y]");
  const xTicks = document.querySelectorAll(".plot-axis.x");
  const yTicks = document.querySelectorAll(".plot-axis.y");

  const chartModes = {
    score: {
      label: "NixBench pass rate plotted against agent time",
      x: "Agent minutes",
      y: "Pass rate",
      xTicks: ["0m", "5m", "10m", "15m", "20m"],
      yTicks: ["100%", "75%", "50%", "25%"],
    },
    time: {
      label: "NixBench agent time plotted against pass rate",
      x: "Pass rate",
      y: "Agent minutes",
      xTicks: ["0%", "25%", "50%", "75%", "100%"],
      yTicks: ["0m", "5m", "10m", "15m"],
    },
    failures: {
      label: "NixBench failure count plotted against pass rate",
      x: "Failed tasks",
      y: "Pass rate",
      xTicks: ["0", "1", "2", "3", "5"],
      yTicks: ["100%", "75%", "50%", "25%"],
    },
  };

  function setChartMode(mode) {
    if (!plot || !chartModes[mode]) {
      return;
    }

    const config = chartModes[mode];
    plot.dataset.metric = mode;
    plot.setAttribute("aria-label", config.label);
    if (axisX) axisX.textContent = config.x;
    if (axisY) axisY.textContent = config.y;
    xTicks.forEach((tick, index) => {
      tick.textContent = config.xTicks[index] || "";
    });
    yTicks.forEach((tick, index) => {
      tick.textContent = config.yTicks[index] || "";
    });
    modeButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.chartMode === mode));
    });
  }

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => setChartMode(button.dataset.chartMode));
  });
})();
