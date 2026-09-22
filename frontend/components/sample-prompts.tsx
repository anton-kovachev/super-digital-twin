import { useEffect, useState } from "react";
import { flushSync } from "react-dom";

export default function SamplePrompts({
  sendMessage,
  baseUrl,
}: {
  sendMessage: (prompt: string | null | undefined) => void;
  baseUrl: string;
}) {
  const [samplePrompts, setSamplePrompts] = useState([]);

  useEffect(() => {
    const fetchSamplePrompts = async () => {
      try {
        const response = await fetch(`${baseUrl}/sample-prompts`);
        if (!response.ok) throw new Error("Failed to fetch sample prompts");
        const data = await response.json();
        // Assuming setSamplePrompts is available in the parent component
        setSamplePrompts(data || []);
      } catch (error) {
        console.error("Error fetching sample prompts:", error);
      }
    };
    fetchSamplePrompts();
  }, []);
  return (
    <div className="grid grid-cols-3 auto-rows-[60px] gap-2">
      {samplePrompts.map((prompt, index) => (
        <button
          key={index}
          className="h-fullpx-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:cursor-pointer"
          onClick={() => {
            sendMessage(prompt);
          }}
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
