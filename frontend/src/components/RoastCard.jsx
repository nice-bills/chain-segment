import React from 'react';

const RoastCard = ({ explanation }) => {
  const cleanText = explanation ? explanation.replace(/^["']|["']$/g, '') : '';

  return (
    <div className="h-full w-full p-4 overflow-y-auto font-mono text-xs md:text-sm leading-relaxed text-zinc-300">
      <div className="mb-2 text-zinc-500 uppercase text-[10px] tracking-widest border-l-2 border-amber-500 pl-2">
        Behavioral Pattern Detected
      </div>
      <p>
        {cleanText || "Awaiting input stream..."}
      </p>
      <div className="mt-4 flex gap-1">
        <span className="w-1 h-3 bg-amber-500 animate-pulse"></span>
        <span className="w-1 h-3 bg-transparent border border-zinc-700"></span>
      </div>
    </div>
  );
};

export default RoastCard;