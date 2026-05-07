# ResumeAI Pro — Frontend

A high-end, AI-powered resume optimization platform built with Next.js, Tailwind CSS v4, and Framer Motion.

## 🚀 Features

- **Premium Design**: Modern, glassmorphic UI with staggered animations and custom color palettes.
- **RAG-Powered Optimization**: Integrates with Gemini AI to tailor resumes to specific job descriptions.
- **Full Auth Flow**: Secure login, signup, and password recovery systems.
- **Multi-Step Dashboard**: Intuitive workflow for uploading resumes and analyzing job descriptions.
- **Optimization History**: Track and manage all your past AI-tailored resume versions.
- **Production-Ready**: Fully typed with TypeScript, optimized fonts (Inter & JetBrains Mono), and responsive layouts.

## 🛠️ Tech Stack

- **Framework**: Next.js 15+ (App Router)
- **Styling**: Tailwind CSS v4 (using OKLCH colors & CSS-first configuration)
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **API Handling**: Fetch API with typed service layer
- **Markdown**: React Markdown (for AI output rendering)
- **File Handling**: React Dropzone

## 🏁 Getting Started

### 1. Environment Setup
Create a `.env.local` file in the root directory:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Run Development Server
```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## 📂 Project Structure

- `/app`: App router pages and layouts.
- `/components`: Reusable UI components (Navbar, Sidebar, Shell).
- `/lib`: Core logic, API client, and Auth context.
- `/public`: Static assets.
- `globals.css`: Core design system and Tailwind v4 configuration.

## 🔒 Security

Authentication is handled via JWT stored in LocalStorage. All protected routes are guarded by the `AuthContext` provider and middleware-level logic in the Dashboard layout.
