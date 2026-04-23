"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function VerifyOTPPage() {
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const router = useRouter();

  useEffect(() => {
    const storedEmail = sessionStorage.getItem("auth_email");
    if (!storedEmail) {
      router.push("/login");
      return;
    }
    setEmail(storedEmail);
    // Focus first input
    inputRefs.current[0]?.focus();
  }, [router]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // digits only

    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all filled
    if (newOtp.every((d) => d !== "")) {
      handleSubmit(newOtp.join(""));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (text.length === 6) {
      const newOtp = text.split("");
      setOtp(newOtp);
      handleSubmit(text);
    }
  };

  const handleSubmit = async (code?: string) => {
    const otpCode = code || otp.join("");
    if (otpCode.length !== 6) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/verify-login-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, otp: otpCode }),
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.detail || "Invalid OTP.");
        setOtp(["", "", "", "", "", ""]);
        inputRefs.current[0]?.focus();
        setLoading(false);
        return;
      }

      if (data.requires_2fa) {
        router.push("/verify-2fa");
        return;
      }

      // Login successful — store tokens and redirect
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        if (data.user) {
          localStorage.setItem("user", JSON.stringify(data.user));
        }
      }

      router.push("/analyze");
    } catch (err: any) {
      setError(err.message || "Network error.");
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError("");
    try {
      const response = await fetch("http://localhost:8000/api/auth/request-login-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!data.success) {
        setError(data.detail || "Failed to resend.");
      }
    } catch {
      setError("Failed to resend OTP.");
    }
    setResending(false);
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center min-h-screen relative px-4 md:px-8">

      {/* Navigation */}
      <nav className="absolute top-0 left-0 right-0 flex items-center justify-between z-10 text-[10px] md:text-xs uppercase tracking-widest text-secondary px-4 md:px-8 pt-8">
        <Link href="/login" className="hover:text-primary transition-colors">← BACK</Link>
        <div className="flex-1 mx-4 h-[1px] bg-dividers"></div>
        <div>VERIFICATION</div>
      </nav>

      <div className="flex flex-col items-center gap-8 max-w-md w-full z-10">

        {/* Cinematic Headline */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="w-6 h-[1px] bg-accent"></div>
            <span className="text-xs uppercase tracking-widest text-secondary">Step 2 of 2</span>
            <div className="w-6 h-[1px] bg-accent"></div>
          </div>

          <h1 className="font-display font-bold uppercase tracking-tighter text-5xl md:text-6xl text-primary leading-[0.9]">
            VERIFY
            <br />
            ACCESS
          </h1>
        </div>

        {/* OTP Input */}
        <div className="flex flex-col items-center gap-4 w-full">
          <label className="text-xs uppercase tracking-widest text-secondary font-bold">
            6 Digit Code
          </label>

          <div className="flex gap-3" onPaste={handlePaste}>
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                disabled={loading}
                className="w-12 h-14 md:w-14 md:h-16 bg-transparent border border-borders rounded-[4px] text-center text-2xl font-display font-bold text-primary outline-none focus:border-accent transition-colors disabled:opacity-50"
                id={`otp-input-${i}`}
              />
            ))}
          </div>

          <span className="text-[10px] text-borders tracking-wide uppercase">
            Code expires in 10 minutes
          </span>
        </div>

        {error && (
          <div className="text-[#ff5555] text-xs uppercase tracking-widest p-3 border border-[#ff5555] rounded-[4px] w-full text-center">
            {error}
          </div>
        )}

        {/* Verify Button */}
        <button
          onClick={() => handleSubmit()}
          disabled={loading || otp.join("").length !== 6}
          className="w-full bg-accent text-background font-bold uppercase text-sm tracking-widest py-4 rounded-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          id="verify-otp-btn"
        >
          {loading ? "VERIFYING..." : "VERIFY"}
        </button>

        {/* Resend */}
        <button
          onClick={handleResend}
          disabled={resending}
          className="text-xs uppercase tracking-widest text-secondary hover:text-accent transition-colors disabled:opacity-50"
        >
          {resending ? "Sending..." : "Resend Code"}
        </button>

      </div>

      {/* Footer */}
      <div className="absolute bottom-0 left-0 right-0 px-4 md:px-8 py-4 z-10">
        <div className="w-full h-[1px] bg-dividers mb-4"></div>
        <div className="flex items-center justify-between text-[10px] text-borders uppercase tracking-widest">
          <span>Sent to {email}</span>
          <span>PASSWORDLESS</span>
        </div>
      </div>

    </main>
  );
}
