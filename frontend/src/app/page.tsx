import Script from 'next/script'

export default function CareerAgent() {
  return (
    <div className="w-full h-screen bg-[#0a0a0a] overflow-hidden">
      <iframe
        src="https://muhammadburhan-career-agent-backend.hf.space/?__theme=dark"
        frameBorder="0"
        style={{ width: '100%', height: '100%', border: 'none' }}
        allow="microphone; camera; clipboard-read; clipboard-write"
      ></iframe>
    </div>
  )
}
