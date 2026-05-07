"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-surface-950">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-bold text-surface-100">
              ResumeAI<span className="text-primary-400">Pro</span>
            </span>
          </div>
          <div className="flex items-center gap-8 text-sm text-surface-200/60">
            <Link href="/" className="hover:text-surface-100 transition-colors">Home</Link>
            <Link href="/login" className="hover:text-surface-100 transition-colors">Login</Link>
            <Link href="/signup" className="hover:text-surface-100 transition-colors">Sign Up</Link>
          </div>
          <p className="text-xs text-surface-200/40">
            &copy; {new Date().getFullYear()} ResumeAI Pro. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
