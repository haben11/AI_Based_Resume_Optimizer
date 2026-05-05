"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, 
  FileText, 
  Sparkles, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Copy,
  Download,
  RotateCcw,
  X,
  Zap,
  Wand2,
  Settings2,
  Check
} from "lucide-react";
import { useDropzone } from "react-dropzone";
import ReactMarkdown from "react-markdown";
import { uploadResume, downloadResumePdf, getResumePreview, optimizeSnippet } from "@/lib/api";
import { useStreamingOptimization } from "@/lib/streaming-api";
import { toast } from "sonner";

// Component to render real content snippet for the template cards
const TemplateThumbnail = ({ templateId, colorHex, optimizedCv }: { templateId: string, colorHex: string | undefined, optimizedCv: string | null }) => {
  // If we have optimized content, use snippets from it
  const displaySkills = optimizedCv 
    ? optimizedCv.split('## Skills')[1]?.split('##')[0]?.split('\n')
        .map(s => s.trim().replace(new RegExp("^[-*]\\s*"), ""))
        .filter(s => s.length > 0)
        .slice(0, 4) || ["Strategy", "Leadership", "Technology", "Growth"]
    : ["Strategy", "Leadership", "Technology", "Growth"];

  return (
    <div className="h-full w-full overflow-hidden relative bg-white">

      <div className="p-4 space-y-3">
        {templateId === "tokyo-1" ? (
          <div className="space-y-4">
             <div className="h-1 w-full bg-primary-500 bg-opacity-20" />
             <div className="space-y-1">
                <div className="h-4 w-2/3 bg-zinc-900 rounded-sm" />
                <div className="h-2 w-1/3 bg-primary-500 bg-opacity-10 rounded-sm" />
             </div>
             <div className="grid grid-cols-3 gap-2">
                <div className="col-span-1 space-y-2">
                   <div className="h-2 w-full bg-zinc-100 rounded" />
                   <div className="h-2 w-full bg-zinc-100 rounded" />
                   <div className="h-2 w-full bg-zinc-100 rounded" />
                </div>
                <div className="col-span-2 space-y-2">
                   <div className="h-2 w-full bg-zinc-50 rounded" />
                   <div className="h-2 w-full bg-zinc-50 rounded" />
                   <div className="h-2 w-3/4 bg-zinc-50 rounded" />
                </div>
             </div>
          </div>
        ) : templateId === "vienna-1" ? (
          <div className="text-center py-4 space-y-4">
             <div className="space-y-2 mx-auto">
                <div className="h-5 w-3/4 bg-zinc-900 rounded-sm mx-auto" />
                <div className="h-1.5 w-1/2 bg-zinc-200 rounded-sm mx-auto" />
             </div>
             <div className="h-px w-full bg-zinc-100" />
             <div className="space-y-2 text-left">
                <div className="h-3 w-1/3 bg-zinc-300 rounded-sm" />
                <div className="space-y-1.5">
                   <div className="h-2 w-full bg-zinc-50 rounded" />
                   <div className="h-2 w-full bg-zinc-50 rounded" />
                </div>
             </div>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full ${colorHex || 'bg-primary-500'} opacity-30 shrink-0`} />
              <div className="space-y-1 flex-1">
                 <div className="h-3 w-1/2 bg-zinc-300 rounded" />
                 <div className="h-2 w-1/3 bg-zinc-100 rounded" />
              </div>
            </div>
            <div className="space-y-1.5">
               <div className="h-2 w-full bg-zinc-50 rounded" />
               <div className="h-2 w-full bg-zinc-50 rounded" />
               <div className="h-2 w-4/5 bg-zinc-50 rounded" />
            </div>
          </>
        )}
        
        <div className="flex flex-wrap gap-1 mt-2">
           {displaySkills.map((s, i) => (
             <div key={i} className="px-2 py-0.5 bg-zinc-100 text-[8px] text-zinc-500 rounded-sm font-bold">{s}</div>
           ))}
        </div>
      </div>
      

      <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent pointer-events-none" />
    </div>
  );
};

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [optimizedCv, setOptimizedCv] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState("modern-1-blue");
  
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(1); // 1: Upload, 2: Job Desc, 3: Result
  const [isRefining, setIsRefining] = useState(false);
  const [selection, setSelection] = useState<{ start: number, end: number, text: string } | null>(null);
  const [isRegeneratingSnippet, setIsRegeneratingSnippet] = useState(false);

  // Streaming optimization hook
  const {
    optimize,
    reset: resetStreaming,
    isStreaming,
    progress,
    stage,
    message,
    tokens,
    result,
    error: streamError
  } = useStreamingOptimization();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setError(null);
    setIsUploading(true);

    try {
      const res = await uploadResume(selectedFile);
      setResumeId(res.resume_id);
      toast.success("Resume uploaded", {
        description: "Your experience has been indexed successfully.",
      });
      setStep(2);
    } catch (err: any) {
      const msg = err.message || "Failed to upload resume";
      setError(msg);
      toast.error("Upload failed", {
        description: msg,
      });
    } finally {
      setIsUploading(false);
    }
  }, []);
  
  const handleSelectionChange = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    const text = target.value.substring(start, end);

    if (text && text.trim().length > 5) {
      setSelection({ start, end, text });
    } else {
      setSelection(null);
    }
  };

  const handleRegenerateSnippet = async () => {
    if (!resumeId || !jobDescription || !selection || !optimizedCv) return;

    setIsRegeneratingSnippet(true);
    try {
      // Get surrounding context (±200 chars)
      const contextStart = Math.max(0, selection.start - 200);
      const contextEnd = Math.min(optimizedCv.length, selection.end + 200);
      const context = optimizedCv.substring(contextStart, contextEnd);

      const res = await optimizeSnippet(
        resumeId,
        jobDescription,
        selection.text,
        context
      );

      // Replace in original CV
      const newCv = 
        optimizedCv.substring(0, selection.start) + 
        res.optimized_cv + 
        optimizedCv.substring(selection.end);
      
      setOptimizedCv(newCv);
      setSelection(null);
      toast.success("Snippet regenerated");
    } catch (err: any) {
      toast.error("Regeneration failed", {
        description: err.message || "Failed to regenerate snippet."
      });
    } finally {
      setIsRegeneratingSnippet(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      ['application' + String.fromCharCode(47) + 'pdf']: ['.pdf'],
      ['application' + String.fromCharCode(47) + 'vnd.openxmlformats-officedocument.wordprocessingml.document']: ['.docx']
    },
    multiple: false,
    disabled: isUploading
  });

  const handleOptimize = async () => {
    if (!resumeId || !jobDescription) return;

    setError(null);

    try {
      // Get access token from localStorage
      const accessToken = localStorage.getItem('access_token');
      if (!accessToken) {
        throw new Error('Not authenticated');
      }

      // Start streaming optimization
      await optimize(resumeId, jobDescription, accessToken);
      
      // Check if we have a result
      if (result) {
        setOptimizedCv(result.optimized_content);
        toast.success("Optimization complete", {
          description: "Your resume has been tailored for the role.",
        });
        setStep(3);
      }
    } catch (err: any) {
      const msg = err.message || "Failed to optimize resume";
      setError(msg);
      toast.error("Optimization failed", {
        description: msg,
      });
    }
  };

  // Watch for streaming completion
  useEffect(() => {
    if (result && !isStreaming) {
      setOptimizedCv(result.optimized_content);
      toast.success("Optimization complete", {
        description: `Quality score: ${result.validation.quality_score.toFixed(2)}`,
      });
      setStep(3);
    }
  }, [result, isStreaming]);

  // Watch for streaming errors
  useEffect(() => {
    if (streamError) {
      setError(streamError);
      toast.error("Optimization failed", {
        description: streamError,
      });
    }
  }, [streamError]);

  const handleCopy = () => {
    if (optimizedCv) {
      navigator.clipboard.writeText(optimizedCv);
      toast.success("Copied to clipboard");
    }
  };

  const handleReset = () => {
    setFile(null);
    setResumeId(null);
    setJobDescription("");
    setOptimizedCv(null);
    setStep(1);
    setError(null);
    resetStreaming();
  };

  const templates = [
    { id: "vienna-1", name: "Vienna Luxury", desc: "Executive Serif & Prestige", badge: "Premium" },
    { id: "tokyo-1", name: "Tokyo Minimal", desc: "Tech-Focused Grid", badge: "Hot" },
    { id: "modern-1", name: "Modern Sidebar", desc: "Professional & High Density" },
    { id: "modern-2", name: "Modern Split", desc: "Impactful & Visual" },
    { id: "executive-1", name: "Executive Serif", desc: "Classic Leadership" },
    { id: "creative-1", name: "Creative Vision", desc: "Bold & Dark Mode" },
    { id: "professional-1", name: "Compact Pro", desc: "High Info Density" },
    { id: "minimal-1", name: "Centered", desc: "Editorial Style" },
  ];

  const colors = [
    { id: "blue", hex: "bg-blue-600" },
    { id: "slate", hex: "bg-slate-700" },
    { id: "emerald", hex: "bg-emerald-600" },
    { id: "indigo", hex: "bg-indigo-600" },
    { id: "rose", hex: "bg-rose-600" },
    { id: "amber", hex: "bg-amber-600" },
    { id: "violet", hex: "bg-violet-600" },
    { id: "cyan", hex: "bg-cyan-600" }
  ];

  const [activeColors, setActiveColors] = useState<Record<string, string>>(
    templates.reduce((acc, t) => ({ ...acc, [t.id]: "blue" }), {})
  );

  const handleDownload = async (templateId: string, color: string, format: string = "pdf") => {
    if (!resumeId) return;
    const fullTemplateId = `${templateId}-${color}`;
    setIsDownloading(true);
    try {
      await downloadResumePdf(resumeId, undefined, fullTemplateId, format);
      toast.success("File Downloaded", {
        description: `Your resume has been saved as a ${format.toUpperCase()}.`
      });
    } catch (err) {
      toast.error("Download failed", {
        description: "Could not generate file. Please try again."
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handlePreview = async (templateId: string, color: string) => {
    if (!resumeId) return;
    const fullTemplateId = `${templateId}-${color}`;
    setIsDownloading(true);
    try {
      const { html } = await getResumePreview(resumeId, undefined, fullTemplateId);
      setPreviewHtml(html);
      setIsPreviewing(true);
      setSelectedTemplate(fullTemplateId);
    } catch (err: any) {
      toast.error("Preview failed", {
        description: err.message || "Could not load template preview."
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">Resume Optimizer</h1>
        <p className="text-surface-200 text-opacity-50">Follow the steps below to tailor your resume for any job.</p>
      </div>

      <div className="flex items-center gap-4 mb-10 overflow-x-auto pb-2">
        {[
          { num: 1, label: "Upload Resume" },
          { num: 2, label: "Job Description" },
          { num: 3, label: "Optimization" }
        ].map((s) => (
          <div key={s.num} className="flex items-center gap-3 shrink-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border transition-colors ${
              step >= s.num ? "bg-primary-500 border-primary-500 text-white" : "border-white border-opacity-10 text-surface-200 text-opacity-30"
            }`}>
              {step > s.num ? <CheckCircle2 className="w-5 h-5" /> : s.num}
            </div>
            <span className={`text-sm font-medium ${step >= s.num ? "text-surface-50" : "text-surface-200 text-opacity-30"}`}>
              {s.label}
            </span>
            {s.num < 3 && <div className="w-10 h-px bg-white bg-opacity-10 mx-2" />}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass p-12 rounded-3xl text-center"
          >
            <div {...getRootProps()} className={`upload-zone rounded-2xl p-16 cursor-pointer ${isDragActive ? "dragging" : ""}`}>
              <input {...getInputProps()} />
              <div className="w-20 h-20 rounded-2xl bg-primary-500 bg-opacity-10 flex items-center justify-center mx-auto mb-6">
                {isUploading ? (
                  <Loader2 className="w-10 h-10 text-primary-400 animate-spin" />
                ) : (
                  <Upload className="w-10 h-10 text-primary-400" />
                )}
              </div>
              <h2 className="text-2xl font-bold mb-3">
                {file ? file.name : "Upload your current resume"}
              </h2>
              <p className="text-surface-200 text-opacity-50 mb-8 max-w-sm mx-auto">
                Support PDF and DOCX files. Our AI will extract your skills and experience automatically.
              </p>
              {error && (
                <div className="flex items-center justify-center gap-2 text-danger-500 text-sm mb-6 bg-danger-500 bg-opacity-10 p-3 rounded-lg border border-danger-500 border-opacity-20">
                  <AlertCircle className="w-4 h-4" />
                  {error}
                </div>
              )}
              <div className="inline-flex items-center gap-2 px-6 py-3 bg-white bg-opacity-5 border border-white border-opacity-10 rounded-xl font-medium hover:bg-white bg-opacity-10 transition-colors">
                Select File
              </div>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="glass p-8 rounded-3xl"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-accent-500 bg-opacity-10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-accent-400" />
              </div>
              <h2 className="text-xl font-bold">Paste Job Description</h2>
            </div>
            
            {!isStreaming ? (
              <>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the full job description here (minimum 50 characters)..."
                  className="w-full h-80 bg-white bg-opacity-5 border border-white border-opacity-10 rounded-2xl p-6 text-surface-50 placeholder:text-surface-200 text-opacity-20 focus:outline-none focus:border-primary-500 border-opacity-50 transition-all mb-8 resize-none"
                />
                
                {error && (
                  <div className="flex items-center gap-2 text-danger-500 text-sm mb-6 bg-danger-500 bg-opacity-10 p-4 rounded-xl border border-danger-500 border-opacity-20">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {error}
                  </div>
                )}

                <div className="flex items-center justify-between gap-4">
                  <button
                    onClick={() => setStep(1)}
                    className="px-6 py-3 text-sm font-medium text-surface-200 hover:text-white transition-colors"
                  >
                    Back to Upload
                  </button>
                  <button
                    onClick={handleOptimize}
                    disabled={isStreaming || jobDescription.length < 50}
                    className="flex items-center gap-2 px-8 py-3.5 text-sm font-semibold text-white gradient-primary rounded-xl hover:opacity-90 transition-all shadow-lg shadow-primary-500 shadow-opacity-25 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Zap className="w-4 h-4" />
                    Optimize with Streaming AI
                  </button>
                </div>
              </>
            ) : (
              <div className="space-y-6">
                {/* Progress Bar */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-surface-200 font-medium capitalize">
                      {stage.replace(new RegExp("_", "g"), ' ')}
                    </span>
                    <span className="text-primary-400 font-bold">{progress}%</span>
                  </div>
                  <div className="h-2 bg-white bg-opacity-5 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary-500 to-accent-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="text-surface-200 text-opacity-50 text-sm">{message}</p>
                </div>

                {/* Stage Indicators */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { id: 'grounding', label: 'Fetching Data', icon: '🔍' },
                    { id: 'retrieval', label: 'Analyzing Resume', icon: '📄' },
                    { id: 'generation', label: 'Generating', icon: '✨' },
                    { id: 'validation', label: 'Validating', icon: '✅' }
                  ].map((s) => (
                    <div
                      key={s.id}
                      className={`p-4 rounded-xl border transition-all ${
                        stage === s.id
                          ? 'bg-primary-500 bg-opacity-10 border-primary-500 border-opacity-50'
                          : stage > s.id || progress > 50
                          ? 'bg-white bg-opacity-5 border-white border-opacity-10'
                          : 'bg-white bg-opacity-5 border-white border-opacity-5 opacity-50'
                      }`}
                    >
                      <div className="text-2xl mb-2">{s.icon}</div>
                      <div className="text-xs font-medium text-surface-200">{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* Live Token Stream */}
                {tokens && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm font-medium text-surface-200">
                      <Sparkles className="w-4 h-4 text-primary-400 animate-pulse" />
                      Live Generation
                    </div>
                    <div className="h-64 bg-white bg-opacity-5 border border-white border-opacity-10 rounded-2xl p-6 overflow-auto">
                      <div className="text-surface-50 text-sm whitespace-pre-wrap font-mono">
                        {tokens}
                        <span className="inline-block w-2 h-4 bg-primary-400 animate-pulse ml-1" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Cancel Button */}
                <div className="flex justify-center">
                  <button
                    onClick={handleReset}
                    className="px-6 py-2 text-sm text-surface-200 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {step === 3 && optimizedCv && (
  <motion.div
    key="step3"
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="space-y-6"
  >
    <div className="space-y-10">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{isRefining ? "Refine Your Resume" : "Select Your Template"}</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsRefining(!isRefining)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all text-sm font-bold ${
              isRefining
                ? "bg-primary-500 text-white shadow-lg shadow-primary-500/25"
                : "bg-white/5 hover:bg-white/10 text-surface-200"
            }`}
          >
            <Wand2 className="w-4 h-4" />
            {isRefining ? "Finish Editing" : "Refine with AI"}
          </button>
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-surface-200 transition-colors text-sm font-medium"
          >
            <RotateCcw className="w-4 h-4" />
            Start Over
          </button>
        </div>
      </div>

      {isRefining ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative glass rounded-[2.5rem] p-10 border border-white/10 shadow-2xl"
        >
          <div className="flex items-center justify-between mb-8">
            <div>
              <h3 className="text-xl font-bold text-white mb-1">AI-Powered Editor</h3>
              <p className="text-surface-200/50 text-sm">Edit directly or highlight text to regenerate it with market-grounded AI.</p>
            </div>
            <div className="flex items-center gap-4">
              <AnimatePresence>
                {selection && (
                  <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    onClick={handleRegenerateSnippet}
                    disabled={isRegeneratingSnippet}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-500 to-accent-500 text-white rounded-2xl font-bold text-sm shadow-xl shadow-primary-500/30 hover:scale-[1.02] active:scale-95 transition-all"
                  >
                    {isRegeneratingSnippet ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    Regenerate Selection
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="relative">
            <textarea
              value={optimizedCv || ""}
              onChange={(e) => setOptimizedCv(e.target.value)}
              onSelect={handleSelectionChange}
              onMouseUp={handleSelectionChange}
              className="w-full h-[650px] bg-black/40 border border-white/5 rounded-[2rem] p-10 text-surface-50 font-mono text-sm focus:outline-none focus:border-primary-500/30 transition-all resize-none shadow-inner leading-relaxed"
              placeholder="Edit your resume here..."
            />
            <div className="absolute top-6 right-10 text-[10px] font-black text-white/10 uppercase tracking-widest pointer-events-none">
              Interactive Markdown Editor
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {templates.map((template) => {
            const activeColor = activeColors[template.id];
            const colorHex = colors.find(c => c.id === activeColor)?.hex;

            return (
              <div key={template.id} className="group flex flex-col glass rounded-[2.5rem] overflow-hidden border border-white/5 hover:border-primary-500/30 transition-all duration-500 hover:shadow-2xl hover:shadow-primary-500/10">

                <div className="relative bg-white overflow-hidden" style={{ aspectRatio: "3 / 4" }}>
                  <TemplateThumbnail templateId={template.id} colorHex={colorHex} optimizedCv={optimizedCv} />

                  <div className="absolute inset-0 bg-primary-500/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-500 flex items-center justify-center p-8">
                    <div className="text-center transform translate-y-4 group-hover:translate-y-0 transition-transform duration-500">
                      <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-4 border border-white/30">
                        <CheckCircle2 className="w-8 h-8 text-white" />
                      </div>
                      <p className="text-white font-black text-xl mb-2 uppercase tracking-tighter">Use this Template</p>
                      <p className="text-white/70 text-xs px-4">Download your optimized resume instantly in this style.</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handlePreview(template.id, activeColor)}
                    className="absolute bottom-6 left-1/2 -translate-x-1/2 px-6 py-2 bg-primary-500 text-white font-bold text-xs rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-xl shadow-primary-500/40 z-20"
                  >
                    Use this template
                  </button>
                </div>

                <div className="p-8 space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-black text-white leading-none">{template.name}</h3>
                        {template.badge && (
                          <span className="px-1.5 py-0.5 rounded bg-primary-500/20 text-primary-400 text-[8px] font-black uppercase tracking-widest">
                            {template.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-surface-200/40 uppercase tracking-widest font-bold">{template.desc}</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {(colors.slice(0, 5)).map((c) => (
                        <button
                          key={c.id}
                          onClick={() => setActiveColors(prev => ({ ...prev, [template.id]: c.id }))}
                          className={`w-4 h-4 rounded-full ${c.hex} border-2 transition-all ${
                            activeColor === c.id ? "border-white scale-125 shadow-lg" : "border-transparent opacity-40 hover:opacity-100"
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleDownload(template.id, activeColor, "pdf")}
                      disabled={isDownloading}
                      className="flex items-center justify-center gap-2 py-3 rounded-2xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-bold transition-all border border-white/5 active:scale-95 disabled:opacity-50"
                    >
                      <span className="opacity-40">PDF</span>
                      {isDownloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                    </button>
                    <button
                      onClick={() => handleDownload(template.id, activeColor, "docx")}
                      disabled={isDownloading}
                      className="flex items-center justify-center gap-2 py-3 rounded-2xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-bold transition-all shadow-lg shadow-primary-500/20 active:scale-95 disabled:opacity-50"
                    >
                      <span className="opacity-60">DOCX</span>
                      {isDownloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  </motion.div>
)}
      </AnimatePresence>


      <AnimatePresence>
        {isPreviewing && previewHtml && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-10 bg-black bg-opacity-90 backdrop-blur-xl"
          >
            <div className="relative w-full max-w-5xl h-full bg-white rounded-[2rem] overflow-hidden shadow-2xl flex flex-col">

               <div className="flex items-center justify-between p-6 bg-zinc-50 border-b border-zinc-200 shrink-0">
                  <div className="flex items-center gap-4">
                     <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white">
                        <Sparkles className="w-5 h-5" />
                     </div>
                     <div>
                        <h3 className="font-bold text-zinc-900 leading-none">Template Preview</h3>
                        <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-1">Reviewing: {selectedTemplate}</p>
                     </div>
                  </div>
                  <div className="flex items-center gap-2">
                     <button
                        onClick={() => {
                          const [t, c] = selectedTemplate.split('-');
                          handleDownload(t, c, "pdf");
                        }}
                        className="flex items-center gap-2 px-6 py-2.5 bg-zinc-900 hover:bg-black text-white text-xs font-bold rounded-xl transition-all shadow-lg"
                     >
                        <Download className="w-4 h-4" />
                        PDF
                     </button>
                     <button
                        onClick={() => {
                          const [t, c] = selectedTemplate.split('-');
                          handleDownload(t, c, "docx");
                        }}
                        className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 hover:bg-primary-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg"
                     >
                        <Download className="w-4 h-4" />
                        DOCX
                     </button>
                     <button 
                        onClick={() => setIsPreviewing(false)}
                        className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-zinc-200 transition-colors"
                     >
                        <X className="w-5 h-5 text-zinc-400" />
                     </button>
                  </div>
               </div>


               <div className="flex-1 overflow-hidden bg-zinc-100 p-8">
                  <div className="w-full h-full bg-white shadow-inner overflow-auto rounded-xl">
                     <iframe 
                        srcDoc={previewHtml}
                        className="w-full h-full border-none"
                        title="Resume Preview"
                     />
                  </div>
               </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
