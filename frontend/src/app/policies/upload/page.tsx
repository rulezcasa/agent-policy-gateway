import { PolicyUploadDropzone } from "@/components/policies/policy-upload-dropzone";

export default function PolicyUploadPage() {
  return <div className="mx-auto max-w-4xl space-y-10"><section className="border-b border-slate-200/80 pb-7"><p className="text-xs font-medium uppercase tracking-[0.1em] text-coral-600">Policy ingestion</p><h2 className="mt-3 text-[30px] font-medium tracking-[-0.045em] text-slate-950">Upload policy</h2><p className="mt-3 max-w-2xl text-[15px] leading-7 text-slate-500">Upload policy PDFs.</p></section><PolicyUploadDropzone /></div>;
}
