"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 glass"
    >
      <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-primary-500/40 transition-shadow">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight text-surface-50">
            ResumeAI<span className="text-primary-400">Pro</span>
          </span>
        </Link>

        <div className="flex items-center gap-3">
          {isLanding ? (
            <>
              <Link
                href="/login"
                className="px-5 py-2.5 text-sm font-medium text-surface-200 hover:text-white transition-colors rounded-xl hover:bg-white/5"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="px-5 py-2.5 text-sm font-semibold text-white gradient-primary rounded-xl hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25"
              >
                Get Started Free
              </Link>
            </>
          ) : (
            <Link
              href="/login"
              className="px-5 py-2.5 text-sm font-semibold text-white gradient-primary rounded-xl hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
