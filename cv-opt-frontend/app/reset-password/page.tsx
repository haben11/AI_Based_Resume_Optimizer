"use client";

import { useState, FormEvent, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Lock, ArrowRight, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { resetPassword } from "@/lib/api";

function ResetForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Passwords do not match"); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters"); return; }
    if (!token) { setError("Invalid or missing reset token"); return; }
    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
        <div className="w-16 h-16 rounded-full bg-accent-500/15 flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-8 h-8 text-accent-500" />
        </div>
        <h2 className="text-xl font-bold mb-3">Password Updated</h2>
        <p className="text-surface-200/50 text-sm mb-6">Your password has been reset successfully.</p>
        <Link href="/login" className="inline-flex items-center gap-2 px-6 py-3 text-sm font-semibold text-white gradient-primary rounded-xl">
          Sign In <ArrowRight className="w-4 h-4" />
        </Link>
      </motion.div>
    );
  }

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2">Reset Password</h1>
        <p className="text-surface-200/50 text-sm">Choose a new secure password</p>
      </div>
      {error && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          className="mb-6 px-4 py-3 rounded-xl bg-danger-500/10 border border-danger-500/20 text-danger-500 text-sm">
          {error}
        </motion.div>
      )}
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="rp-pass" className="block text-sm font-medium text-surface-200/70 mb-2">New Password</label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/30" />
            <input id="rp-pass" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••"
              className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/8 text-surface-50 placeholder:text-surface-200/25 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/30 transition-all text-sm" />
          </div>
        </div>
        <div>
          <label htmlFor="rp-confirm" className="block text-sm font-medium text-surface-200/70 mb-2">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/30" />
            <input id="rp-confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="••••••••"
              className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/8 text-surface-50 placeholder:text-surface-200/25 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/30 transition-all text-sm" />
          </div>
        </div>
        <button type="submit" disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-semibold text-white gradient-primary rounded-xl hover:opacity-90 transition-all shadow-lg shadow-primary-500/25 disabled:opacity-50">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><span>Reset Password</span><ArrowRight className="w-4 h-4" /></>}
        </button>
      </form>
      <div className="mt-6 text-center">
        <Link href="/login" className="inline-flex items-center gap-2 text-sm text-surface-200/40 hover:text-surface-200/60">
          <ArrowLeft className="w-4 h-4" /> Back to Sign In
        </Link>
      </div>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen gradient-mesh flex items-center justify-center px-4 py-12 relative overflow-hidden">
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-primary-500/10 blur-[120px]" />
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center shadow-lg shadow-primary-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-surface-50">ResumeAI<span className="text-primary-400">Pro</span></span>
          </Link>
        </div>
        <div className="glass rounded-3xl p-8 shadow-2xl shadow-black/20">
          <Suspense fallback={<div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-primary-400" /></div>}>
            <ResetForm />
          </Suspense>
        </div>
      </motion.div>
    </div>
  );
}
