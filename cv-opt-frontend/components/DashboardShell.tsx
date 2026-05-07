"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, LayoutDashboard, History, User, LogOut, Menu, X, ChevronDown,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Optimizer", icon: LayoutDashboard },
  { href: "/dashboard/history", label: "History", icon: History },
];

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = async () => { await logout(); window.location.href = "/login"; };

  return (
    <div className="min-h-screen bg-surface-950 flex">
      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside className={`fixed lg:sticky top-0 left-0 z-50 h-screen w-64 flex flex-col bg-surface-900/80 backdrop-blur-xl border-r border-white/5 transition-transform lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-6 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shadow-lg shadow-primary-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-surface-50">ResumeAI<span className="text-primary-400">Pro</span></span>
          </Link>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-surface-200/50 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${active ? "bg-primary-500/15 text-primary-300" : "text-surface-200/50 hover:text-surface-100 hover:bg-white/5"}`}>
                <item.icon className="w-5 h-5" />
                {item.label}
                {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-400" />}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-white/5">
          <div className="relative">
            <button onClick={() => setProfileOpen(!profileOpen)}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center text-xs font-bold text-white">
                {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="flex-1 text-left min-w-0">
                <p className="text-sm font-medium text-surface-100 truncate">{user?.full_name || "User"}</p>
                <p className="text-xs text-surface-200/40 truncate">{user?.email}</p>
              </div>
              <ChevronDown className={`w-4 h-4 text-surface-200/30 transition-transform ${profileOpen ? "rotate-180" : ""}`} />
            </button>

            <AnimatePresence>
              {profileOpen && (
                <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                  className="absolute bottom-full left-0 right-0 mb-2 glass rounded-xl overflow-hidden shadow-xl">
                  <Link href="/dashboard/profile" onClick={() => { setProfileOpen(false); setSidebarOpen(false); }}
                    className="flex items-center gap-3 px-4 py-3 text-sm text-surface-200/70 hover:text-surface-100 hover:bg-white/5 transition-colors">
                    <User className="w-4 h-4" /> Profile Settings
                  </Link>
                  <button onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-danger-500 hover:bg-danger-500/10 transition-colors">
                    <LogOut className="w-4 h-4" /> Sign Out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col min-h-screen">
        {/* Top bar (mobile) */}
        <header className="lg:hidden sticky top-0 z-30 glass px-4 py-3 flex items-center gap-3">
          <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-white/5">
            <Menu className="w-5 h-5 text-surface-200" />
          </button>
          <span className="text-sm font-semibold text-surface-100">ResumeAI Pro</span>
        </header>
        <div className="flex-1 p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
