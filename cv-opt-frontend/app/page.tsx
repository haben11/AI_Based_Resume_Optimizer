"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles,
  Upload,
  FileText,
  Zap,
  ArrowRight,
  CheckCircle2,
  BarChart3,
  ShieldCheck,
  Globe,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

const features = [
  {
    icon: Upload,
    title: "Upload Your Resume",
    description: "Simply drag and drop your existing resume in PDF or DOCX format.",
  },
  {
    icon: FileText,
    title: "Paste Job Description",
    description: "Copy the target job posting and our AI will analyze every requirement.",
  },
  {
    icon: Zap,
    title: "Get Optimized Resume",
    description: "Receive a perfectly tailored resume that highlights your relevant skills.",
  },
];

const benefits = [
  {
    icon: BarChart3,
    title: "85% Higher Match Rate",
    description: "Our AI ensures your resume matches key ATS keywords and phrases.",
  },
  {
    icon: ShieldCheck,
    title: "Enterprise-Grade Security",
    description: "Your documents are encrypted end-to-end. We never share your data.",
  },
  {
    icon: Globe,
    title: "Works for Any Industry",
    description: "From tech to finance, healthcare to creative — optimized for all roles.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* ─── HERO ─── */}
      <section className="relative gradient-hero min-h-screen flex items-center overflow-hidden">
        {/* Ambient orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-primary-500/10 blur-[120px] animate-float" />
          <div className="absolute top-1/3 right-0 w-[500px] h-[500px] rounded-full bg-accent-500/8 blur-[100px] animate-float" style={{ animationDelay: "2s" }} />
          <div className="absolute -bottom-20 left-1/3 w-[400px] h-[400px] rounded-full bg-primary-600/8 blur-[80px] animate-float" style={{ animationDelay: "4s" }} />
        </div>

        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />

        <div className="relative mx-auto max-w-7xl px-6 pt-32 pb-24">
          <div className="max-w-4xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-sm text-primary-300 mb-8"
            >
              <Sparkles className="w-4 h-4" />
              <span>Powered by Advanced RAG + Gemini AI</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6"
            >
              Land Your Dream Job with{" "}
              <span className="gradient-text">AI-Optimized</span> Resumes
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.25 }}
              className="text-lg sm:text-xl text-surface-200/70 max-w-2xl mx-auto mb-10 leading-relaxed"
            >
              Upload your resume and job description. Our AI analyzes, restructures,
              and tailors your CV to perfectly match what recruiters are looking for.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.4 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Link
                href="/signup"
                className="group flex items-center gap-2 px-8 py-4 text-base font-semibold text-white gradient-primary rounded-2xl hover:opacity-90 transition-all shadow-2xl shadow-primary-500/30 hover:shadow-primary-500/50"
              >
                Start Optimizing Free
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/login"
                className="px-8 py-4 text-base font-medium text-surface-200 rounded-2xl glass hover:bg-white/10 transition-colors"
              >
                Sign In
              </Link>
            </motion.div>

            {/* Social proof */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.8 }}
              className="mt-14 flex flex-col sm:flex-row items-center justify-center gap-6 text-sm text-surface-200/50"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-accent-500" />
                <span>No credit card required</span>
              </div>
              <div className="hidden sm:block w-1 h-1 rounded-full bg-surface-200/20" />
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-accent-500" />
                <span>Optimized in seconds</span>
              </div>
              <div className="hidden sm:block w-1 h-1 rounded-full bg-surface-200/20" />
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-accent-500" />
                <span>ATS-compatible output</span>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="relative py-28 gradient-mesh">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            className="text-center mb-16"
          >
            <motion.p variants={fadeUp} custom={0} className="text-sm font-semibold text-primary-400 uppercase tracking-widest mb-3">
              How It Works
            </motion.p>
            <motion.h2 variants={fadeUp} custom={1} className="text-3xl sm:text-4xl font-bold tracking-tight">
              Three Simple Steps to Success
            </motion.h2>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            className="grid md:grid-cols-3 gap-8"
          >
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                variants={fadeUp}
                custom={i + 2}
                className="relative group p-8 rounded-3xl glass hover:bg-white/5 transition-all duration-300"
              >
                {/* Step number */}
                <div className="absolute -top-4 -left-2 text-7xl font-black text-primary-500/10 select-none">
                  {i + 1}
                </div>

                <div className="relative">
                  <div className="w-14 h-14 rounded-2xl bg-primary-500/15 flex items-center justify-center mb-6 group-hover:bg-primary-500/25 transition-colors">
                    <f.icon className="w-7 h-7 text-primary-400" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{f.title}</h3>
                  <p className="text-surface-200/60 leading-relaxed">{f.description}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── BENEFITS ─── */}
      <section className="py-28 bg-surface-950">
        <div className="mx-auto max-w-7xl px-6">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            className="text-center mb-16"
          >
            <motion.p variants={fadeUp} custom={0} className="text-sm font-semibold text-accent-500 uppercase tracking-widest mb-3">
              Why Choose Us
            </motion.p>
            <motion.h2 variants={fadeUp} custom={1} className="text-3xl sm:text-4xl font-bold tracking-tight">
              Built for Results
            </motion.h2>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            className="grid md:grid-cols-3 gap-8"
          >
            {benefits.map((b, i) => (
              <motion.div
                key={b.title}
                variants={fadeUp}
                custom={i + 2}
                className="p-8 rounded-3xl border border-white/5 hover:border-primary-500/20 bg-surface-900/50 hover:bg-surface-900/80 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-accent-500/15 flex items-center justify-center mb-5">
                  <b.icon className="w-6 h-6 text-accent-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{b.title}</h3>
                <p className="text-surface-200/50 text-sm leading-relaxed">{b.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="relative py-28 overflow-hidden">
        <div className="absolute inset-0 gradient-hero" />
        <div className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px)`,
            backgroundSize: "30px 30px",
          }}
        />
        <div className="relative mx-auto max-w-3xl px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-5">
              Ready to Transform Your Career?
            </h2>
            <p className="text-surface-200/60 mb-10 text-lg">
              Join thousands of professionals who land interviews faster with AI-optimized resumes.
            </p>
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 px-10 py-4 text-base font-semibold text-white gradient-primary rounded-2xl hover:opacity-90 transition-opacity shadow-2xl shadow-primary-500/30"
            >
              Create Your Free Account
              <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
