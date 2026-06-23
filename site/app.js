(function () {
  const canvases = document.querySelectorAll(".trace-canvas");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  canvases.forEach((canvas) => {
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    let width = 0;
    let height = 0;
    let frame = 0;
    const scene = canvas.dataset.scene || "landing";

    function resize() {
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width));
      height = Math.max(1, Math.floor(rect.height));
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    function drawGrid() {
      context.clearRect(0, 0, width, height);
      context.fillStyle = "#0e1117";
      context.fillRect(0, 0, width, height);

      context.lineWidth = 1;
      context.strokeStyle = "rgba(244, 246, 249, 0.06)";
      for (let x = 0; x < width; x += 44) {
        context.beginPath();
        context.moveTo(x, 0);
        context.lineTo(x, height);
        context.stroke();
      }
      for (let y = 0; y < height; y += 44) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(width, y);
        context.stroke();
      }
    }

    function node(x, y, radius, color, label) {
      context.beginPath();
      context.fillStyle = color;
      context.arc(x, y, radius, 0, Math.PI * 2);
      context.fill();

      if (width < 560) {
        return;
      }

      context.font = "700 11px SFMono-Regular, ui-monospace, monospace";
      context.fillStyle = "rgba(244, 246, 249, 0.74)";
      context.fillText(label, x + radius + 8, y + 4);
    }

    function link(a, b, color) {
      context.beginPath();
      context.lineWidth = 2;
      context.strokeStyle = color;
      context.moveTo(a[0], a[1]);
      context.lineTo(b[0], b[1]);
      context.stroke();
    }

    function drawTrace() {
      drawGrid();

      const drift = reducedMotion ? 0 : Math.sin(frame / 42) * 8;
      const scan = reducedMotion ? width * 0.62 : (frame * 2.1) % (width + 240) - 120;

      const points = scene === "results"
        ? [
            [width * 0.48, height * 0.23 + drift, "#c47a35", "gpt: pass"],
            [width * 0.72, height * 0.31 - drift, "#3f82cc", "claude: pass"],
            [width * 0.58, height * 0.52, "#d24a3a", "hidden fail"],
            [width * 0.83, height * 0.66 + drift, "#a9682b", "timeout"],
            [width * 0.44, height * 0.78 - drift, "#f4f6f9", "score 500"],
          ]
        : [
            [width * 0.48, height * 0.17 + drift, "#f4f6f9", "starter tree"],
            [width * 0.72, height * 0.28 - drift, "#3f82cc", "agent diff"],
            [width * 0.83, height * 0.48 + drift, "#c47a35", "fake lib"],
            [width * 0.58, height * 0.61, "#3f9d63", "hidden eval"],
            [width * 0.76, height * 0.78 + drift, "#f4f6f9", "score.json"],
            [width * 0.39, height * 0.82 - drift, "#d24a3a", "false lead"],
          ];

      context.globalAlpha = 0.72;
      for (let i = 0; i < points.length - 1; i += 1) {
        link(points[i], points[i + 1], "rgba(244, 246, 249, 0.22)");
      }
      context.globalAlpha = 1;

      points.forEach((point) => node(point[0], point[1], 7, point[2], point[3]));

      context.fillStyle = "rgba(63, 130, 204, 0.16)";
      context.fillRect(scan, 0, 90, height);
      context.fillStyle = "rgba(244, 246, 249, 0.18)";
      context.fillRect(scan + 88, 0, 2, height);

      if (width >= 560) {
        context.font = "700 12px SFMono-Regular, ui-monospace, monospace";
        context.fillStyle = "rgba(244, 246, 249, 0.34)";
        context.fillText(scene === "results" ? "hidden evaluator trace" : "17-task evaluator trace", width - 230, height - 34);
      }
    }

    function tick() {
      frame += 1;
      drawTrace();
      if (!reducedMotion) {
        window.requestAnimationFrame(tick);
      }
    }

    resize();
    drawTrace();
    window.addEventListener("resize", resize);
    if (!reducedMotion) {
      window.requestAnimationFrame(tick);
    }
  });
})();
