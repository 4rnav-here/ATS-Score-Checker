"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

const PRIORITY_COLORS: Record<string, string> = {
  critical: "border-[#ff5555] text-[#ff5555]",
  high: "border-[#ffaa55] text-[#ffaa55]",
  medium: "border-accent text-accent",
  low: "border-borders text-secondary",
};

const PRIORITY_BG: Record<string, string> = {
  critical: "bg-[#ff5555]/10",
  high: "bg-[#ffaa55]/10",
  medium: "bg-accent/10",
  low: "bg-transparent",
};

const INDIA_CITIES = [
  "All India",
  "Bangalore",
  "Hyderabad",
  "Pune",
  "Chennai",
  "Mumbai",
  "Delhi NCR",
  "Remote",
];

// ── Copy-to-clipboard button ──────────────────────────────────────────────────
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };
  return (
    <button
      onClick={handleCopy}
      className="text-[10px] uppercase tracking-widest border border-borders px-2 py-1 rounded-[2px] text-secondary hover:text-accent hover:border-accent transition-colors whitespace-nowrap"
    >
      {copied ? "Copied ✓" : "Copy"}
    </button>
  );
}

// ── Suggested fix collapsible ─────────────────────────────────────────────────
function SuggestedFix({ suggestions }: { suggestions: any[] }) {
  const [open, setOpen] = useState(false);
  if (!suggestions || suggestions.length === 0) return null;
  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-[10px] uppercase tracking-widest text-accent hover:brightness-110 transition-all flex items-center gap-2"
      >
        <span>{open ? "▲" : "▼"}</span>
        <span>Suggested Fix</span>
      </button>
      {open && (
        <div className="mt-3 flex flex-col gap-2">
          {suggestions.map((s: any, i: number) => (
            <div key={i} className="border border-borders rounded-[4px] overflow-hidden">
              <div className="flex items-center justify-between px-3 py-1.5 bg-dividers">
                <span className="text-[10px] uppercase tracking-widest text-secondary font-bold">
                  {s.section}
                </span>
                <CopyButton text={s.content} />
              </div>
              <div className="px-3 py-2.5 font-mono text-xs text-primary leading-relaxed whitespace-pre-wrap">
                {s.content_type === "bullet" ? `• ${s.content}` : s.content}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Score row ─────────────────────────────────────────────────────────────────
function ScoreRow({
  label,
  value,
  isPenalty = false,
}: {
  label: string;
  value: number;
  isPenalty?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-primary">{label}</span>
      <span
        className={`font-mono ${isPenalty && value < 0 ? "text-[#ff5555]" : "text-accent"}`}
      >
        {isPenalty ? "" : "+"}
        {typeof value === "number" ? value.toFixed(1) : value}
      </span>
    </div>
  );
}

// ── Job card ──────────────────────────────────────────────────────────────────
function JobCard({ job, idx }: { job: any; idx: number }) {
  return (
    <div className="border border-borders rounded-[4px] p-5 hover:border-accent transition-colors group">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            {job.match_score !== undefined && (
              <span className="text-[10px] uppercase tracking-widest border border-accent text-accent px-2 py-0.5 rounded-[2px] font-bold">
                {Math.round(job.match_score)}% Match
              </span>
            )}
            {job.tier_label && (
              <span className="text-[10px] uppercase tracking-widest border border-[#f0c040] text-[#f0c040] px-2 py-0.5 rounded-[2px] font-bold">
                {job.tier_label}
              </span>
            )}
            <span className="text-[10px] uppercase tracking-widest text-borders">
              {job.source}
            </span>
          </div>
          <h3 className="text-base font-bold text-primary group-hover:text-accent transition-colors">
            {job.title}
          </h3>
          <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-secondary">
            <span>{job.company}</span>
            {job.location && (
              <>
                <span className="text-borders">·</span>
                <span>{job.location}</span>
              </>
            )}
          </div>
        </div>
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs uppercase tracking-widest border border-borders px-4 py-2 rounded-[4px] text-secondary hover:text-accent hover:border-accent transition-colors whitespace-nowrap shrink-0"
        >
          Apply →
        </a>
      </div>

      {(job.salary_min || job.salary_max) && (
        <div className="text-xs text-accent font-mono mb-2">
          ₹{job.salary_min?.toLocaleString()} – ₹{job.salary_max?.toLocaleString()} / yr
        </div>
      )}

      {job.description && (
        <p className="text-xs text-borders leading-relaxed line-clamp-2">
          {job.description}
        </p>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState("");
  const [jobsFetched, setJobsFetched] = useState(false);
  const [selectedCity, setSelectedCity] = useState("All India");

  useEffect(() => {
    if (!params.id) return;
    try {
      const stored = localStorage.getItem(`ats_result_${params.id}`);
      if (stored) {
        setData(JSON.parse(stored));
      } else {
        router.push("/analyze");
      }
    } catch (e) {
      console.error("Failed to parse result data", e);
    }
  }, [params.id, router]);

  const fetchJobs = async (city: string) => {
    setJobsLoading(true);
    setJobsError("");
    try {
      const cityFilter =
        city === "All India" || city === "Remote"
          ? null
          : [city === "Delhi NCR" ? "Delhi" : city];

      const res = await fetch("http://localhost:8000/api/jobs/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_id: params.id,
          max_days_old: 30,
          cities: cityFilter,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const payload = await res.json();
      setJobs(payload.jobs);
      setJobsFetched(true);
    } catch (e: any) {
      setJobsError(e.message || "Failed to fetch jobs.");
    } finally {
      setJobsLoading(false);
    }
  };

  if (!data) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen text-secondary text-xs uppercase tracking-widest">
        LOADING DATA...
      </div>
    );
  }

  const {
    scores,
    section_scores,
    skill_gaps,
    format_issues,
    quality_issues,
    jd_alignment_warning,
    recommendations,
    recommendation_summary,
  } = data;

  return (
    <main className="flex-1 flex flex-col min-h-screen p-4 md:p-8 max-w-5xl mx-auto w-full relative z-10">
      <nav className="w-full flex items-center justify-between mb-8 text-[10px] md:text-xs uppercase tracking-widest text-secondary">
        <Link href="/analyze" className="hover:text-primary transition-colors">
          ← NEW ANALYSIS
        </Link>
        <div>REPORT {params.id?.toString().split("-")[0]}</div>
      </nav>

      {/* ── Main Score Header ─────────────────────────────────────────────── */}
      <div className="mb-12 border border-borders rounded-[4px] p-6 md:p-10 flex flex-col md:flex-row items-center justify-between gap-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-display font-bold uppercase tracking-tight text-primary mb-2">
            Analysis Complete
          </h1>
          <div className="w-12 h-[1px] bg-accent mb-4" />
          {jd_alignment_warning ? (
            <p className="text-[#ff5555] text-sm uppercase tracking-wider">
              {jd_alignment_warning}
            </p>
          ) : (
            <p className="text-secondary text-sm uppercase tracking-wider">
              Document alignment meets baseline thresholds.
            </p>
          )}
        </div>
        <div className="flex flex-col items-center justify-center border-4 border-accent rounded-full w-32 h-32 shrink-0">
          <span className="text-4xl font-display font-bold text-primary">
            {Math.round(scores.final)}
          </span>
          <span className="text-[10px] uppercase tracking-widest text-secondary">
            FINAL SCORE
          </span>
        </div>
      </div>

      {/* ── Score Breakdown + Skill Gaps ──────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="flex flex-col gap-8">
          <section>
            <h2 className="text-xs uppercase tracking-widest text-secondary font-bold mb-4 border-b border-dividers pb-2">
              Score Breakdown
            </h2>
            <div className="flex flex-col gap-3">
              <ScoreRow label="Semantic Match" value={scores.semantic} />
              <ScoreRow label="Keyword TF-IDF" value={scores.keyword} />
              <ScoreRow label="Format Penalty" value={-scores.format_penalty} isPenalty />
            </div>
          </section>
          <section>
            <h2 className="text-xs uppercase tracking-widest text-secondary font-bold mb-4 border-b border-dividers pb-2">
              Section Scores
            </h2>
            <div className="flex flex-col gap-3">
              <ScoreRow label="Skills" value={section_scores.skills} />
              <ScoreRow label="Experience" value={section_scores.experience} />
              <ScoreRow label="Education" value={section_scores.education} />
              {section_scores.projects != null && (
                <ScoreRow label="Projects" value={section_scores.projects} />
              )}
              {section_scores.summary != null && (
                <ScoreRow label="Summary" value={section_scores.summary} />
              )}
            </div>
          </section>
        </div>

        <div className="flex flex-col gap-8">
          <section>
            <h2 className="text-xs uppercase tracking-widest text-secondary font-bold mb-4 border-b border-dividers pb-2">
              Skill Gaps ({skill_gaps.length})
            </h2>
            {skill_gaps.length === 0 ? (
              <p className="text-sm text-borders">No major skill gaps detected.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {skill_gaps.map((skill: string) => (
                  <span
                    key={skill}
                    className="text-xs border border-borders px-3 py-1 rounded-[2px] text-primary bg-background uppercase"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-secondary font-bold mb-4 border-b border-dividers pb-2">
              Quality &amp; Format Issues
            </h2>
            <div className="flex flex-col gap-2">
              {[...format_issues, ...quality_issues].map(
                (issue: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-2 text-sm text-secondary">
                    <span className="text-accent mt-1">▪</span>
                    <span>{issue}</span>
                  </div>
                )
              )}
              {format_issues.length === 0 && quality_issues.length === 0 && (
                <p className="text-sm text-borders">No issues detected.</p>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* ── Recommendations ────────────────────────────────────────────────── */}
      {recommendations && recommendations.length > 0 && (
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl md:text-2xl font-display font-bold uppercase tracking-tight text-primary">
              Recommendations
            </h2>
            {recommendation_summary && (
              <div className="flex gap-3 text-[10px] uppercase tracking-widest">
                {recommendation_summary.critical > 0 && (
                  <span className="text-[#ff5555]">
                    {recommendation_summary.critical} Critical
                  </span>
                )}
                {recommendation_summary.high > 0 && (
                  <span className="text-[#ffaa55]">
                    {recommendation_summary.high} High
                  </span>
                )}
                {recommendation_summary.medium > 0 && (
                  <span className="text-accent">
                    {recommendation_summary.medium} Medium
                  </span>
                )}
                {recommendation_summary.low > 0 && (
                  <span className="text-secondary">
                    {recommendation_summary.low} Low
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="w-full h-[1px] bg-dividers mb-6" />

          <div className="flex flex-col gap-4">
            {recommendations.map((rec: any, idx: number) => (
              <div
                key={idx}
                className={`border border-borders rounded-[4px] p-5 ${PRIORITY_BG[rec.priority] || ""}`}
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-[10px] uppercase tracking-widest border px-2 py-0.5 rounded-[2px] font-bold ${PRIORITY_COLORS[rec.priority] || "text-secondary border-borders"}`}
                    >
                      {rec.priority}
                    </span>
                    <h3 className="text-sm font-bold text-primary">{rec.title}</h3>
                  </div>
                </div>
                <p className="text-sm text-secondary leading-relaxed mb-3">
                  {rec.description}
                </p>
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-borders">
                  <span>Impact:</span>
                  <span className="text-accent">{rec.impact}</span>
                </div>
                {/* ── Suggested fix section ── */}
                <SuggestedFix suggestions={rec.suggested_content} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Find Jobs Section ──────────────────────────────────────────────── */}
      <div className="mb-12">
        <div className="flex flex-col gap-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl md:text-2xl font-display font-bold uppercase tracking-tight text-primary">
                Matching Jobs
              </h2>
              <p className="text-secondary text-xs mt-1 uppercase tracking-widest">
                India-based · Experience-matched · Company quality ranked
              </p>
            </div>
            {!jobsFetched && (
              <button
                onClick={() => fetchJobs(selectedCity)}
                disabled={jobsLoading}
                id="find-jobs-btn"
                className="bg-accent text-background font-bold uppercase text-xs tracking-wider px-6 py-3 rounded-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {jobsLoading ? "SEARCHING..." : "FIND JOBS NOW"}
              </button>
            )}
            {jobsFetched && (
              <span className="text-xs text-secondary uppercase tracking-widest">
                {jobs.length} Results
              </span>
            )}
          </div>

          {/* City filter chips */}
          <div className="flex flex-wrap gap-2">
            {INDIA_CITIES.map((city) => (
              <button
                key={city}
                onClick={() => {
                  setSelectedCity(city);
                  if (jobsFetched) fetchJobs(city);
                }}
                className={`text-[10px] uppercase tracking-widest px-3 py-1 rounded-[2px] border transition-colors ${
                  selectedCity === city
                    ? "border-accent text-accent bg-accent/10"
                    : "border-borders text-secondary hover:border-accent hover:text-accent"
                }`}
              >
                {city}
              </button>
            ))}
          </div>
        </div>

        <div className="w-full h-[1px] bg-dividers mb-6" />

        {jobsLoading && (
          <div className="flex items-center gap-3 text-secondary text-xs uppercase tracking-widest py-8">
            <span className="animate-pulse">
              ● QUERYING ADZUNA INDIA + LINKEDIN INDIA...
            </span>
          </div>
        )}

        {jobsError && (
          <div className="text-[#ff5555] text-xs uppercase tracking-widest p-3 border border-[#ff5555] rounded-[4px]">
            {jobsError}
          </div>
        )}

        {!jobsFetched && !jobsLoading && (
          <div className="border border-borders border-dashed rounded-[4px] p-8 text-center">
            <p className="text-secondary text-sm">
              Click "Find Jobs Now" to search Adzuna India + LinkedIn India for
              roles matching your skills and experience level.
            </p>
          </div>
        )}

        {jobsFetched && jobs.length === 0 && (
          <div className="border border-borders rounded-[4px] p-6 text-center">
            <p className="text-secondary text-sm">
              No matching jobs found. Try selecting a different city or run a
              new analysis with a different job description.
            </p>
          </div>
        )}

        {jobs.length > 0 && (
          <div className="flex flex-col gap-4">
            {jobs.map((job: any, idx: number) => (
              <JobCard key={idx} job={job} idx={idx} />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
