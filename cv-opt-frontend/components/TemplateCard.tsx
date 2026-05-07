import { Download, Loader2, CheckCircle2 } from "lucide-react";

interface TemplateCardProps {
  template: any;
  activeColor: string;
  colorHex: string | undefined;
  colors: any[];
  optimizedCv: string | null;
  isDownloading: boolean;
  onColorChange: (templateId: string, colorId: string) => void;
  onPreview: (templateId: string, colorId: string) => void;
  onDownload: (templateId: string, colorId: string, format: string) => void;
  TemplateThumbnail: any;
}

export default function TemplateCard({
  template,
  activeColor,
  colorHex,
  colors,
  optimizedCv,
  isDownloading,
  onColorChange,
  onPreview,
  onDownload,
  TemplateThumbnail,
}: TemplateCardProps) {
  return (
    <div className="group flex flex-col glass rounded-[2.5rem] overflow-hidden border border-white border-opacity-5 hover:border-primary-500 hover:border-opacity-30 transition-all duration-500 hover:shadow-2xl hover:shadow-primary-500/10">
      {/* Visual Preview Card */}
      <div className="relative aspect-[3_/_4] bg-white overflow-hidden">
        <TemplateThumbnail templateId={template.id} colorHex={colorHex} optimizedCv={optimizedCv} />

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-primary-500 bg-opacity-80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-500 flex items-center justify-center p-8">
          <div className="text-center transform translate-y-4 group-hover:translate-y-0 transition-transform duration-500">
            <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-4 border border-white/30">
              <CheckCircle2 className="w-8 h-8 text-white" />
            </div>
            <p className="text-white font-black text-xl mb-2 uppercase tracking-tighter">Use this Template</p>
            <p className="text-white/70 text-xs px-4">Download your optimized resume instantly in this style.</p>
          </div>
        </div>
        
        {/* Use this Template Button */}
        <button 
          onClick={() => onPreview(template.id, activeColor)}
          className="absolute bottom-6 left-1/2 -translate-x-1/2 px-6 py-2 bg-primary-500 text-white font-bold text-xs rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-xl shadow-primary-500/40 z-20"
        >
          Use this template
        </button>
      </div>

      {/* Footer Actions */}
      <div className="p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-black text-white leading-none">{template.name}</h3>
              {template.badge && (
                <span className="px-1.5 py-0.5 rounded bg-primary-500 bg-opacity-20 text-primary-400 text-[8px] font-black uppercase tracking-widest">
                  {template.badge}
                </span>
              )}
            </div>
            <p className="text-[10px] text-surface-200 text-opacity-40 uppercase tracking-widest font-bold">{template.desc}</p>
          </div>
          <div className="flex items-center gap-1.5">
            {colors.slice(0, 5).map((c) => (
              <button
                key={c.id}
                onClick={() => onColorChange(template.id, c.id)}
                className={`w-4 h-4 rounded-full ${c.hex} border-2 transition-all ${
                  activeColor === c.id ? "border-white scale-125 shadow-lg" : "border-transparent opacity-40 hover:opacity-100"
                }`}
              />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => onDownload(template.id, activeColor, "pdf")}
            disabled={isDownloading}
            className="flex items-center justify-center gap-2 py-3 rounded-2xl bg-surface-800 hover:bg-surface-700 text-white text-xs font-bold transition-all border border-white border-opacity-5 active:scale-95 disabled:opacity-50"
          >
            <span className="opacity-40">PDF</span>
            {isDownloading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
          </button>
          <button
            onClick={() => onDownload(template.id, activeColor, "docx")}
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
}
