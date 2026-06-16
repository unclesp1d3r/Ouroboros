<script lang="ts">
    // Performance data comes from `GET /api/v1/web/agents/{agent_id}/performance` endpoint and has the following structure:
    /*
    {
    "series": [
        {
        "device": "string",
        "data": [
            {
            "timestamp": "2025-06-04T22:53:59.758Z",
            "speed": 0
            }
        ]
        }
    ]
    }
    */
    // Render a single multi-series chart: x = timestamp, y = speed, one line per device.

    import * as Chart from '$lib/components/ui/chart/index.js';
    import { LineChart } from 'layerchart';
    import * as Card from '$lib/components/ui/card/index.js';
    import { scaleUtc } from 'd3-scale';
    import { curveNatural } from 'd3-shape';

    export let series: Array<{
        device: string;
        data: Array<{ timestamp: string; speed: number }>;
    }> = [];

    // 1. Collect all unique timestamps
    const allTimestamps = Array.from(
        new Set(series.flatMap((d) => d.data.map((p) => p.timestamp)))
    ).toSorted();

    // 2. Build wide-format data: [{ timestamp, [device1]: speed, [device2]: speed, ... }]
    const wideData = allTimestamps.map((timestamp) => {
        const row: Record<string, string | number | Date | null> = {
            timestamp: new Date(timestamp),
        };
        for (const device of series) {
            const point = device.data.find((d) => d.timestamp === timestamp);
            row[device.device] = point ? point.speed : null;
        }
        return row;
    });

    // 3. Build series array for LineChart
    const colorPalette = [
        '#2563eb', // blue-600
        '#16a34a', // green-600
        '#f59e42', // orange-400
        '#e11d48', // rose-600
        '#7c3aed', // violet-600
        '#facc15', // yellow-400
        '#0ea5e9', // sky-500
        '#d946ef', // fuchsia-500
    ];
    const chartSeries = series.map((d, i) => ({
        key: d.device,
        label: d.device,
        color: colorPalette[i % colorPalette.length],
    }));

    const today = new Date();
    const xScale = scaleUtc([new Date(today.getTime() - 8 * 60 * 60 * 1000), today]);

    const chartConfig = {};
</script>

{#if series && series.length > 0}
    <Card.Root>
        <Card.Header>
            <Card.Title>Agent Performance</Card.Title>
            <Card.Description>Showing performance for the last 8 hours</Card.Description>
        </Card.Header>
        <Card.Content>
            <Chart.Container config={chartConfig} data-testid="agent-performance-chart">
                <LineChart
                    data={wideData}
                    x="timestamp"
                    {xScale}
                    series={chartSeries}
                    props={{
                        spline: { curve: curveNatural, motion: 'tween', strokeWidth: 2 },
                        xAxis: {
                            format: (v: Date) =>
                                v.toLocaleTimeString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                }),
                        },
                        highlight: { points: { r: 4 } },
                    }}>
                    {#snippet tooltip()}
                        <Chart.Tooltip />
                    {/snippet}
                </LineChart>
            </Chart.Container>
        </Card.Content>
    </Card.Root>
{:else}
    <div class="text-gray-500 italic">No device performance data available for this agent.</div>
{/if}
