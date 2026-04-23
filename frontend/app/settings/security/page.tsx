"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SecuritySettingsPage() {
  const [user, setUser] = useState<any>(null);
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [showSetup, setShowSetup] = useState(false);
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [verifyCode, setVerifyCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    fetchUser();
  }, []);

  const getToken = () => localStorage.getItem("access_token") || "";

  const fetchUser = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/auth/me", {
        headers: { Authorization: `Bearer ${getToken()}` },
        credentials: "include",
      });

      if (!response.ok) {
        router.push("/login");
        return;
      }

      const data = await response.json();
      setUser(data);
      setTotpEnabled(data.totp_enabled);
    } catch {
      router.push("/login");
    }
  };

  const handleSetupTOTP = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/totp/setup", {
        headers: { Authorization: `Bearer ${getToken()}` },
        credentials: "include",
      });

      const data = await response.json();
      setQrCode(data.qr_code_base64);
      setSecret(data.secret);
      setShowSetup(true);
    } catch (err: any) {
      setError("Failed to initialize TOTP setup.");
    }
    setLoading(false);
  };

  const handleEnableTOTP = async () => {
    if (verifyCode.length !== 6) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/totp/enable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        credentials: "include",
        body: JSON.stringify({ code: verifyCode }),
      });

      const data = await response.json();

      if (data.success) {
        setTotpEnabled(true);
        setShowSetup(false);
        setMessage("Two-factor authentication enabled successfully.");
        setVerifyCode("");
      } else {
        setError(data.detail || "Invalid code.");
      }
    } catch {
      setError("Failed to enable TOTP.");
    }
    setLoading(false);
  };

  const handleDisableTOTP = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/totp/disable", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        setTotpEnabled(false);
        setShowSetup(false);
        setMessage("Two-factor authentication disabled.");
      } else {
        setError(data.detail || "Failed to disable.");
      }
    } catch {
      setError("Failed to disable TOTP.");
    }
    setLoading(false);
  };

  const handleLogout = async () => {
    try {
      await fetch("http://localhost:8000/api/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        credentials: "include",
      });
    } catch { /* ignore */ }

    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("auth_email");
    router.push("/login");
  };

  if (!user) {
    return (
      <main className="flex-1 flex items-center justify-center min-h-screen">
        <span className="text-secondary text-xs uppercase tracking-widest animate-pulse">Loading...</span>
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col min-h-screen p-4 md:p-8 max-w-3xl mx-auto w-full relative z-10">

      {/* Header */}
      <nav className="w-full flex items-center justify-between mb-12 text-[10px] md:text-xs uppercase tracking-widest text-secondary">
        <Link href="/analyze" className="hover:text-primary transition-colors">← DASHBOARD</Link>
        <div>SECURITY SETTINGS</div>
      </nav>

      <div className="mb-10">
        <h1 className="text-4xl font-display font-bold uppercase tracking-tight text-primary mb-2">
          Security
        </h1>
        <div className="w-12 h-[1px] bg-accent mb-4"></div>
        <p className="text-secondary text-sm">
          Manage your authentication and two-factor security settings.
        </p>
      </div>

      {/* User Info */}
      <div className="border border-borders rounded-[4px] p-6 mb-8">
        <div className="text-xs uppercase tracking-widest text-secondary mb-4 font-bold">Account</div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-primary font-display font-bold text-lg">{user.email}</div>
            <div className="text-secondary text-xs mt-1">
              {user.full_name || "No name set"} · {user.is_verified ? "Verified" : "Unverified"}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs uppercase tracking-widest text-secondary border border-borders px-4 py-2 rounded-[4px] hover:text-[#ff5555] hover:border-[#ff5555] transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="w-full h-[1px] bg-dividers mb-8"></div>

      {/* 2FA Section */}
      <div className="border border-borders rounded-[4px] p-6">
        <div className="text-xs uppercase tracking-widest text-secondary mb-4 font-bold">
          Two-Factor Authentication
        </div>

        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-primary font-bold">
              {totpEnabled ? "🟢 TOTP Enabled" : "⚪ TOTP Disabled"}
            </div>
            <div className="text-secondary text-xs mt-1">
              {totpEnabled
                ? "Your account is protected with an authenticator app."
                : "Add an extra layer of security with an authenticator app."}
            </div>
          </div>
        </div>

        {!totpEnabled && !showSetup && (
          <button
            onClick={handleSetupTOTP}
            disabled={loading}
            className="bg-accent text-background font-bold uppercase text-xs tracking-wider px-6 py-3 rounded-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50"
            id="enable-totp-btn"
          >
            {loading ? "Loading..." : "Enable TOTP Authentication"}
          </button>
        )}

        {totpEnabled && (
          <button
            onClick={handleDisableTOTP}
            disabled={loading}
            className="text-xs uppercase tracking-widest text-secondary border border-borders px-6 py-3 rounded-[4px] hover:text-[#ff5555] hover:border-[#ff5555] transition-colors disabled:opacity-50"
          >
            {loading ? "Disabling..." : "Disable 2FA"}
          </button>
        )}

        {/* TOTP Setup Flow */}
        {showSetup && (
          <div className="mt-8 flex flex-col gap-6">
            <div className="w-full h-[1px] bg-dividers"></div>

            <div className="text-xs uppercase tracking-widest text-secondary font-bold">
              1. Scan QR Code
            </div>

            {qrCode && (
              <div className="flex justify-center p-4 bg-white rounded-[4px] w-fit mx-auto">
                <img
                  src={`data:image/png;base64,${qrCode}`}
                  alt="TOTP QR Code"
                  className="w-48 h-48"
                />
              </div>
            )}

            <div className="text-xs uppercase tracking-widest text-secondary font-bold">
              2. Backup Secret Key
            </div>

            <div className="border border-borders rounded-[4px] p-4 font-mono text-sm text-accent break-all select-all">
              {secret}
            </div>
            <span className="text-[10px] text-borders tracking-wide">
              Save this key in a secure location. You will need it if you lose your authenticator app.
            </span>

            <div className="text-xs uppercase tracking-widest text-secondary font-bold">
              3. Verify Code
            </div>

            <div className="flex w-full">
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
                placeholder="000000"
                className="flex-1 bg-transparent border border-borders rounded-l-[4px] px-4 py-4 text-sm text-primary placeholder:text-borders outline-none focus:border-accent transition-colors font-mono text-center text-2xl tracking-[0.5em]"
                id="totp-verify-input"
              />
              <button
                onClick={handleEnableTOTP}
                disabled={loading || verifyCode.length !== 6}
                className="bg-accent text-background font-bold uppercase text-xs tracking-wider px-6 py-4 rounded-r-[4px] border border-accent hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                id="totp-verify-btn"
              >
                {loading ? "..." : "VERIFY"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      {message && (
        <div className="text-accent text-xs uppercase tracking-widest p-3 border border-accent rounded-[4px] mt-6 text-center">
          {message}
        </div>
      )}

      {error && (
        <div className="text-[#ff5555] text-xs uppercase tracking-widest p-3 border border-[#ff5555] rounded-[4px] mt-6 text-center">
          {error}
        </div>
      )}

    </main>
  );
}
