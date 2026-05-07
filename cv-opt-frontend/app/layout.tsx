import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ResumeAI Pro — AI-Powered Resume Optimization",
  description:
    "Upload your resume and job description. Our AI analyzes and produces a perfectly optimized resume tailored for that specific role.",
  keywords: ["resume", "AI", "optimizer", "job", "career", "cv"],
};

import { Toaster } from "sonner";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          {children}
          <Toaster 
            position="bottom-right" 
            toastOptions={{
              className: "glass !bg-surface-900/80 !text-surface-50 !border-white/10",
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
