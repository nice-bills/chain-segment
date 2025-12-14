import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

const PersonaChart = ({ scores }) => {
  const data = Object.keys(scores).map(key => ({
    subject: key.split(" / ")[0].toUpperCase(), // Truncate and Uppercase for cleanliness
    value: scores[key] * 100,
    fullMark: 100,
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black border border-zinc-700 p-2 shadow-xl">
          <div className="flex justify-between items-center gap-4 mb-1 border-b border-zinc-800 pb-1">
             <span className="text-[10px] font-mono text-zinc-400 uppercase">{payload[0].payload.subject}</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-amber-500 font-bold font-mono text-sm">
              {payload[0].value.toFixed(1)}%
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
        <PolarGrid stroke="#27272a" />
        <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'JetBrains Mono', fontWeight: 500 }} 
        />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          name="Confidence"
          dataKey="value"
          stroke="#f59e0b"
          strokeWidth={2}
          fill="#f59e0b"
          fillOpacity={0.2}
          isAnimationActive={true}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#f59e0b', strokeWidth: 1 }} />
      </RadarChart>
    </ResponsiveContainer>
  );
};

export default PersonaChart;