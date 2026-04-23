import Link from "next/link";
import RotatingBadge from "./components/RotatingBadge";

export default function LandingPage() {
  return (
    <main className="flex-1 flex flex-col relative overflow-hidden px-4 md:px-8 pt-8 pb-8 md:pb-12 min-h-screen">
      
      {/* Navigation */}
      <nav className="w-full flex items-center justify-between z-10 text-[10px] md:text-xs uppercase tracking-widest text-secondary">
        <div>SD—PROTOCOL 01</div>
        <div className="flex-1 mx-4 h-[1px] bg-dividers"></div>
        <div>INVITE ONLY</div>
      </nav>

      {/* Hero Section */}
      <div className="flex-1 flex flex-col justify-center mt-16 md:mt-24 z-10">
        <div className="flex items-center gap-4 mb-4 md:mb-6">
          <div className="w-6 h-[1px] bg-accent"></div>
          <span className="text-xs uppercase tracking-widest text-secondary">Early Access</span>
        </div>
        
        {/* Cinematic Headline */}
        <div className="relative font-display font-bold uppercase tracking-tighter leading-[0.85] text-[16vw] md:text-[11.5vw] select-none">
          {/* Back Layer (Stroke) */}
          <div 
            className="absolute top-0 left-0 text-transparent" 
            style={{ 
              WebkitTextStroke: "1px var(--color-borders)",
              transform: "translate(4px, 4px)"
            }}
            aria-hidden="true"
          >
            ATS ANALYZER
          </div>
          {/* Front Layer */}
          <div className="relative text-primary">
            ATS ANALYZER
          </div>
        </div>
      </div>

      <div className="mt-auto z-10 flex flex-col gap-6 md:gap-10">
        {/* Bottom Divider */}
        <div className="w-full h-[1px] bg-dividers"></div>

        {/* Bottom Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 md:gap-4 items-end">
          {/* Left Column */}
          <div className="md:col-span-5 flex flex-col gap-6">
            <p className="text-xl md:text-2xl font-light leading-relaxed text-secondary max-w-md">
              A private, automated intelligence layer for parsing, scoring, and optimizing resumes against exact job requirements.
            </p>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
              <span className="text-xs uppercase tracking-widest text-secondary">Batch 003 Filling</span>
            </div>
          </div>

          <div className="hidden md:block md:col-span-1"></div>

          {/* Right Column / Email Form Fake -> Redirects to Analyze */}
          <div className="md:col-span-6 flex flex-col gap-3 max-w-md w-full ml-auto">
            <form action="/login" className="flex w-full">
              <input 
                type="email" 
                name="email"
                placeholder="ENTER EMAIL FOR ACCESS" 
                className="flex-1 bg-transparent border border-borders rounded-l-[4px] px-4 py-3 md:py-4 text-sm text-primary placeholder:text-borders outline-none focus:border-accent transition-colors"
                required
              />
              <button 
                type="submit"
                className="bg-accent text-background font-bold uppercase text-xs tracking-wider px-6 md:px-8 py-3 md:py-4 rounded-r-[4px] border border-accent hover:brightness-110 transition-all"
              >
                Access
              </button>
            </form>
            <span className="text-[10px] text-borders tracking-wide">
              Zero passwords. Passwordless OTP authentication. Immediate access.
            </span>
          </div>
        </div>
      </div>

      {/* Rotating Badge */}
      <RotatingBadge />
      
    </main>
  );
}
