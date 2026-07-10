import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { TimingTooltip } from "@/components/charts/timing/TimingTooltip";
import { modelColors, timingData } from "@/components/charts/timing/timing-data";
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import { resultColumns, type ResultColumn } from "@/data/benchmark";

export type TimingChartProps = {
  columns?: ResultColumn[];
};

function buildTimingChartConfig(columns: ResultColumn[]) {
  return Object.fromEntries(
    columns.map((column) => [column.key, { label: column.label, color: modelColors[column.key] }]),
  ) satisfies ChartConfig;
}

export function TimingChart({ columns = resultColumns }: TimingChartProps = {}) {
  const timingChartConfig = buildTimingChartConfig(columns);

  return (
    <div className="timing-chart react-timing-chart" role="img" aria-label="Task duration bars for model runs">
      <ChartContainer
        className="timing-chart-container"
        config={timingChartConfig}
        initialDimension={{ width: 900, height: 760 }}
      >
        <BarChart
          accessibilityLayer
          data={timingData}
          layout="vertical"
          margin={{ top: 10, right: 24, bottom: 10, left: 12 }}
        >
          <CartesianGrid stroke="var(--grid-line)" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 240]}
            tickFormatter={(value) => `${value}s`}
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
          />
          <YAxis
            dataKey="task"
            type="category"
            width={138}
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
          />
          <ChartTooltip
            content={<TimingTooltip />}
            cursor={{ fill: "color-mix(in srgb, var(--nix-blue) 6%, transparent)" }}
          />
          <ChartLegend content={<ChartLegendContent />} />
          {columns.map((column) => (
            <Bar
              key={column.key}
              dataKey={column.key}
              name={column.label}
              fill={`var(--color-${column.key}, ${modelColors[column.key]})`}
              radius={0}
            />
          ))}
        </BarChart>
      </ChartContainer>
    </div>
  );
}
