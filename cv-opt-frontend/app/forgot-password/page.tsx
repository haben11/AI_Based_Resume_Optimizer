"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Mail, ArrowRight, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";
import { forgotPassword } from "@/lib/api";
import { toast } from "sonner";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
      toast.success("Recovery email sent", {
        description: `Check your inbox at ${email}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to send recovery email";
      setError(msg);
      toast.error("Recovery failed", {
        description: msg,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-mesh flex items-center justify-center px-4 py-12 relative overflow-hidden">
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-primary-500/10 blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative"
      >
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center shadow-lg shadow-primary-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-surface-50">
              ResumeAI<span className="text-primary-400">Pro</span>
            </span>
          </Link>
        </div>

        <div className="glass rounded-3xl p-8 shadow-2xl shadow-black/20">
          {sent ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
              <div className="w-16 h-16 rounded-full bg-accent-500/15 flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-8 h-8 text-accent-500" />
              </div>
              <h2 className="text-xl font-bold mb-3">Check Your Email</h2>
              <p className="text-surface-200/50 text-sm mb-6">
                Recovery link sent to <strong className="text-surface-50">{email}</strong>.
              </p>
              <Link href="/login" className="inline-flex items-center gap-2 text-sm text-primary-400 hover:text-primary-300 font-medium">
                <ArrowLeft className="w-4 h-4" /> Back to Sign In
              </Link>
            </motion.div>
          ) : (
            <>
              <div className="text-center mb-8">
                <h1 className="text-2xl font-bold mb-2">Forgot Password?</h1>
                <p className="text-surface-200/50 text-sm">Enter your email for a recovery link</p>
              </div>

              {error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                  className="mb-6 px-4 py-3 rounded-xl bg-danger-500/10 border border-danger-500/20 text-danger-500 text-sm">
                  {error}
                </motion.div>
              )}

              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="forgot-email" className="block text-sm font-medium text-surface-200/70 mb-2">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/30" />
                    <input id="forgot-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                      placeholder="you@example.com"
                      className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/8 text-surface-50 placeholder:text-surface-200/25 focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/30 transition-all text-sm" />
                  </div>
                </div>

                <button type="submit" disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-3.5 text-sm font-semibold text-white gradient-primary rounded-xl hover:opacity-90 transition-all shadow-lg shadow-primary-500/25 disabled:opacity-50">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><span>Send Recovery Link</span><ArrowRight className="w-4 h-4" /></>}
                </button>
              </form>

              <div className="mt-6 text-center">
                <Link href="/login" className="inline-flex items-center gap-2 text-sm text-surface-200/40 hover:text-surface-200/60">
                  <ArrowLeft className="w-4 h-4" /> Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}
