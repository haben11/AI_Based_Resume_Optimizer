"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  History, 
  FileText, 
  Calendar, 
  ExternalLink, 
  Loader2,
  Search,
  Filter,
  FileCheck,
  ChevronRight
} from "lucide-react";
import Link from "next/link";
import { getHistory, Resume } from "@/lib/api";

export default function HistoryPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getHistory();
        setResumes(data);
      } catch (err) {
        console.error("Failed to fetch history:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const filteredResumes = resumes.filter(r => 
    r.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10">
        <div>
          <h1 className="text-3xl font-bold mb-2">Optimization History</h1>
          <p className="text-surface-200/50">View and manage your past resume optimizations.</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/30" />
            <input 
              type="text"
              placeholder="Search by filename..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm focus:outline-none focus:border-primary-500/50 w-full sm:w-64"
            />
          </div>
          <button className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-surface-200/50 hover:text-white transition-colors">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 text-surface-200/50">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p>Loading your history...</p>
        </div>
      ) : filteredResumes.length === 0 ? (
        <div className="glass p-20 rounded-3xl text-center border-dashed border-white/5">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-6">
            <History className="w-8 h-8 text-surface-200/20" />
          </div>
          <h2 className="text-xl font-bold mb-2">No history found</h2>
          <p className="text-surface-200/40 mb-8 max-w-xs mx-auto">
            You haven't optimized any resumes yet. Start by uploading your first one!
          </p>
          <Link href="/dashboard" className="inline-flex items-center gap-2 px-6 py-3 gradient-primary text-white font-bold rounded-xl shadow-lg shadow-primary-500/25">
            Optimize Now
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredResumes.map((resume, idx) => (
            <motion.div
              key={resume.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="group glass p-6 rounded-2xl hover:bg-white/5 transition-all flex flex-col md:flex-row md:items-center gap-6"
            >
              <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center shrink-0">
                <FileText className="w-6 h-6 text-primary-400" />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-lg mb-1 truncate group-hover:text-primary-300 transition-colors">
                  {resume.filename}
                </h3>
                <div className="flex flex-wrap items-center gap-4 text-xs text-surface-200/40">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(resume.created_at).toLocaleDateString()}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <FileCheck className="w-3.5 h-3.5 text-accent-500" />
                    {resume.optimizations?.length || 0} Optimizations
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Link 
                  href={`/dashboard/resume/${resume.id}`}
                  className="px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-sm font-medium transition-colors flex items-center gap-2"
                >
                  View Details
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
