"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  FileText, 
  Calendar, 
  Sparkles, 
  Loader2,
  Copy,
  ChevronDown,
  ChevronUp,
  History as HistoryIcon,
  Download
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { getResumeDetails, Resume, downloadResumePdf } from "@/lib/api";
import { toast } from "sonner";

export default function ResumeDetailsPage() {
  const { id } = useParams();
  const router = useRouter();
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number>(0);

  useEffect(() => {
    async function fetchDetails() {
      try {
        const data = await getResumeDetails(id as string);
        setResume(data);
      } catch (err) {
        console.error("Failed to fetch resume details:", err);
      } finally {
        setLoading(false);
      }
    }
    if (id) fetchDetails();
  }, [id]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const handleDownload = async (optimizationId: string) => {
    if (!resume) return;
    try {
      await downloadResumePdf(resume.id, optimizationId);
      toast.success("PDF Downloaded");
    } catch (err) {
      toast.error("Download failed");
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-surface-200/50">
        <Loader2 className="w-10 h-10 animate-spin mb-4" />
        <p>Loading resume details...</p>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="text-center py-24">
        <h2 className="text-2xl font-bold mb-4">Resume not found</h2>
        <button onClick={() => router.back()} className="text-primary-400 hover:underline">Go back</button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <button 
        onClick={() => router.back()}
        className="flex items-center gap-2 text-surface-200/50 hover:text-white transition-colors mb-8 group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        Back to History
      </button>

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-primary-500/10 flex items-center justify-center">
              <FileText className="w-6 h-6 text-primary-400" />
            </div>
            <h1 className="text-3xl font-bold">{resume.filename}</h1>
          </div>
          <p className="text-surface-200/50 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Uploaded on {new Date(resume.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-2 text-surface-200/70 uppercase tracking-widest text-xs font-bold">
          <HistoryIcon className="w-4 h-4" />
          Optimization History ({resume.optimizations?.length || 0})
        </div>

        {resume.optimizations?.length === 0 ? (
          <div className="glass p-12 rounded-3xl text-center text-surface-200/30">
            No optimizations yet for this resume.
          </div>
        ) : (
          resume.optimizations.map((opt, idx) => (
            <div key={idx} className="glass rounded-3xl overflow-hidden border border-white/5">
              <button 
                onClick={() => setExpandedIndex(expandedIndex === idx ? -1 : idx)}
                className="w-full p-6 flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-accent-500/10 flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-accent-400" />
                  </div>
                  <div className="text-left min-w-0">
                    <p className="font-bold text-sm truncate max-w-md">Optimized for: {opt.job_description.substring(0, 60)}...</p>
                    <p className="text-xs text-surface-200/40 mt-0.5">{new Date(opt.created_at).toLocaleString()}</p>
                  </div>
                </div>
                {expandedIndex === idx ? <ChevronUp className="w-5 h-5 text-surface-200/30" /> : <ChevronDown className="w-5 h-5 text-surface-200/30" />}
              </button>

              <AnimatePresence>
                {expandedIndex === idx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/5"
                  >
                    <div className="p-6 bg-white/5">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-bold text-surface-200/40 uppercase tracking-wider">Optimized Content</span>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => handleCopy(opt.optimized_content)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-medium transition-colors"
                          >
                            <Copy className="w-3.5 h-3.5" />
                            Copy
                          </button>
                          <button 
                            onClick={() => handleDownload(opt.id)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg gradient-primary text-white text-xs font-medium transition-opacity"
                          >
                            <Download className="w-3.5 h-3.5" />
                            PDF
                          </button>
                        </div>
                      </div>
                      <div className="p-8 rounded-2xl bg-surface-900 border border-white/5 markdown-output">
                        <ReactMarkdown>{opt.optimized_content}</ReactMarkdown>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
