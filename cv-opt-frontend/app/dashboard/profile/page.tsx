"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  User, 
  Mail, 
  Shield, 
  CheckCircle2, 
  Loader2, 
  Save,
  AlertCircle
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { updateProfile } from "@/lib/api";
import { toast } from "sonner";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [email, setEmail] = useState(user?.email || "");
  
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccess(false);
    setError(null);

    try {
      await updateProfile({ full_name: fullName, email });
      await refreshUser();
      setSuccess(true);
      toast.success("Profile updated", {
        description: "Your information has been saved successfully.",
      });
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      const msg = err.message || "Failed to update profile";
      setError(msg);
      toast.error("Update failed", {
        description: msg,
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">Account Settings</h1>
        <p className="text-surface-200/50">Manage your personal information and preferences.</p>
      </div>

      <div className="grid gap-8">
        {/* Profile Info */}
        <section className="glass rounded-3xl p-8 overflow-hidden relative">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/5 blur-3xl -mr-10 -mt-10" />
          
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center">
              <User className="w-5 h-5 text-primary-400" />
            </div>
            <h2 className="text-xl font-bold">Personal Information</h2>
          </div>

          <form onSubmit={handleSave} className="space-y-6">
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-surface-200/60 mb-2">Full Name</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/20" />
                  <input 
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-primary-500/50 transition-all text-sm"
                    placeholder="John Doe"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-200/60 mb-2">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-200/20" />
                  <input 
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:outline-none focus:border-primary-500/50 transition-all text-sm"
                    placeholder="john@example.com"
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-danger-500 text-sm bg-danger-500/10 p-4 rounded-xl border border-danger-500/20">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <div className="flex items-center justify-end gap-4 pt-4 border-t border-white/5">
              <button
                type="submit"
                disabled={isSaving}
                className="flex items-center gap-2 px-8 py-3 rounded-xl gradient-primary text-white text-sm font-bold shadow-lg shadow-primary-500/25 disabled:opacity-50"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : success ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {isSaving ? "Saving..." : success ? "Saved!" : "Save Changes"}
              </button>
            </div>
          </form>
        </section>

        {/* Security / Subscription placeholder */}
        <section className="glass rounded-3xl p-8 opacity-50 cursor-not-allowed grayscale">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-accent-500/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-accent-400" />
            </div>
            <h2 className="text-xl font-bold">Security & Subscription</h2>
          </div>
          <p className="text-sm text-surface-200/40">Advanced security features and subscription management coming soon in the Pro version.</p>
        </section>
      </div>
    </div>
  );
}
