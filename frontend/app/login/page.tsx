"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/request-login-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.detail || "Failed to send OTP.");
        setLoading(false);
        return;
      }

      // Store email for OTP verification page
      sessionStorage.setItem("auth_email", email);
      setSent(true);

      // Redirect to OTP verification
      setTimeout(() => router.push("/verify-otp"), 500);
    } catch (err: any) {
      setError(err.message || "Network error. Is the backend running?");
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col min-h-screen relative overflow-hidden">

      {/* Navigation */}
      <nav className="w-full flex items-center justify-between z-10 text-[10px] md:text-xs uppercase tracking-widest text-secondary px-4 md:px-8 pt-8">
        <Link href="/" className="hover:text-primary transition-colors">← RETURN</Link>
        <div className="flex-1 mx-4 h-[1px] bg-dividers"></div>
        <div>SECURE ACCESS</div>
      </nav>

      {/* Main Content — Split Layout */}
      <div className="flex-1 flex flex-col md:flex-row items-center z-10 px-4 md:px-8">

        {/* Left — Cinematic Typography */}
        <div className="flex-1 flex flex-col justify-center py-16 md:py-0">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-6 h-[1px] bg-accent"></div>
            <span className="text-xs uppercase tracking-widest text-secondary">Authentication</span>
          </div>

          <div className="relative font-display font-bold uppercase tracking-tighter leading-[0.85] text-[14vw] md:text-[7vw] select-none">
            {/* Back Layer (Stroke) */}
            <div
              className="absolute top-0 left-0 text-transparent"
              style={{
                WebkitTextStroke: "1px var(--color-borders)",
                transform: "translate(3px, 3px)",
              }}
              aria-hidden="true"
            >
              PRIVATE
              <br />
              ACCESS
            </div>
            {/* Front Layer */}
            <div className="relative text-primary">
              PRIVATE
              <br />
              ACCESS
            </div>
          </div>

          <p className="text-secondary text-sm md:text-base mt-8 max-w-sm leading-relaxed">
            Enter your email to receive a secure one-time access code. No passwords required.
          </p>
        </div>

        {/* Right — Login Form */}
        <div className="w-full md:w-[420px] flex flex-col gap-6 pb-16 md:pb-0">

          <div className="w-full h-[1px] bg-dividers md:hidden"></div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">

            <label className="text-xs uppercase tracking-widest text-secondary font-bold">
              Email Address
            </label>

            <div className="flex w-full">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="YOUR@EMAIL.COM"
                required
                disabled={loading || sent}
                className="flex-1 bg-transparent border border-borders rounded-l-[4px] px-4 py-4 text-sm text-primary placeholder:text-borders outline-none focus:border-accent transition-colors disabled:opacity-50"
                id="login-email-input"
              />
              <button
                type="submit"
                disabled={loading || sent}
                className="bg-accent text-background font-bold uppercase text-xs tracking-wider px-6 py-4 rounded-r-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                id="login-send-otp-btn"
              >
                {loading ? "SENDING..." : sent ? "SENT ✓" : "SEND OTP"}
              </button>
            </div>

            {error && (
              <div className="text-[#ff5555] text-xs uppercase tracking-widest p-3 border border-[#ff5555] rounded-[4px]">
                {error}
              </div>
            )}

            {sent && (
              <div className="text-accent text-xs uppercase tracking-widest p-3 border border-accent rounded-[4px]">
                Code sent — check your inbox
              </div>
            )}

          </form>

          <span className="text-[10px] text-borders tracking-wide">
            Zero passwords. Cryptographic OTP only. Your email is your identity.
          </span>

        </div>
      </div>

      {/* Bottom Divider */}
      <div className="w-full h-[1px] bg-dividers mx-4 md:mx-8 z-10"></div>
      <div className="px-4 md:px-8 py-4 z-10 flex items-center justify-between text-[10px] text-borders uppercase tracking-widest">
        <span>ATS ANALYZER</span>
        <span>PASSWORDLESS AUTH</span>
      </div>

    </main>
  );
}
