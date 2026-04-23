export default function RotatingBadge() {
  return (
    <div className="fixed bottom-4 right-4 md:bottom-8 md:right-8 w-16 h-16 md:w-20 md:h-20 z-50 pointer-events-none opacity-80 mix-blend-screen">
      <div className="relative w-full h-full animate-[spin_12s_linear_infinite]">
        <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible">
          <defs>
            <path
              id="circlePath"
              d="M 50, 50 m -35, 0 a 35,35 0 1,1 70,0 a 35,35 0 1,1 -70,0"
            />
          </defs>
          
          <circle cx="50" cy="50" r="45" fill="transparent" stroke="var(--color-borders)" strokeWidth="0.5" />
          
          <text fontSize="10" fontWeight="500" letterSpacing="1.5" fill="var(--color-secondary)" className="uppercase">
            <textPath href="#circlePath" startOffset="0%">
              WAITING LIST • WAITING LIST •
            </textPath>
          </text>
        </svg>
      </div>
    </div>
  );
}
