"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || jdText.trim().length < 20) {
      setError("Please provide a PDF resume and a job description (min 20 words).");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("jd_text", jdText);

      const response = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Analysis failed. Ensure the backend is running.");
      }

      const data = await response.json();
      
      // Store result in localStorage
      localStorage.setItem(`ats_result_${data.analysis_id}`, JSON.stringify(data));
      
      // Redirect
      router.push(`/results/${data.analysis_id}`);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col min-h-screen p-4 md:p-8 max-w-4xl mx-auto w-full relative z-10">
      
      {/* Minimal Header */}
      <nav className="w-full flex items-center justify-between mb-12 text-[10px] md:text-xs uppercase tracking-widest text-secondary">
        <Link href="/" className="hover:text-primary transition-colors">← RETURN</Link>
        <div>SYSTEM INPUT</div>
      </nav>

      <div className="mb-10">
        <h1 className="text-4xl font-display font-bold uppercase tracking-tight text-primary mb-2">Initialize Analysis</h1>
        <div className="w-12 h-[1px] bg-accent mb-4"></div>
        <p className="text-secondary text-sm">Upload your document and target specification for processing.</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-8 flex-1">
        {/* File Upload */}
        <div className="flex flex-col gap-2">
          <label className="text-xs uppercase tracking-widest text-secondary font-bold">1. Document Input (PDF)</label>
          <div className="border border-borders rounded-[4px] p-4 bg-transparent focus-within:border-accent transition-colors relative">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="flex items-center justify-between pointer-events-none">
              <span className={file ? "text-primary" : "text-borders"}>
                {file ? file.name : "SELECT PDF FILE..."}
              </span>
              <span className="text-[10px] uppercase tracking-widest text-secondary border border-borders px-2 py-1 rounded-[2px]">BROWSE</span>
            </div>
          </div>
        </div>

        {/* JD Text Input */}
        <div className="flex flex-col gap-2 flex-1 min-h-[200px]">
          <label className="text-xs uppercase tracking-widest text-secondary font-bold">2. Target Specification (JD)</label>
          <textarea 
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="PASTE JOB DESCRIPTION HERE..."
            className="flex-1 border border-borders rounded-[4px] p-4 bg-transparent text-primary placeholder:text-borders outline-none focus:border-accent transition-colors resize-none text-sm"
          />
        </div>

        {error && (
          <div className="text-[#ff5555] text-xs uppercase tracking-widest p-3 border border-[#ff5555] rounded-[4px]">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button 
          type="submit"
          disabled={loading}
          className="bg-accent text-background font-bold uppercase text-sm tracking-widest py-4 px-8 rounded-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-auto"
        >
          {loading ? "PROCESSING..." : "EXECUTE ANALYSIS"}
        </button>
      </form>

    </main>
  );
}
