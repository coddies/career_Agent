import Script from 'next/script'

export default function CareerAgent() {
  return (
    <div className="w-full h-screen bg-[#0a0a0a] overflow-hidden">
      {/* 
        Option 1: Web Component (gradio-app)
        We load the Gradio script using Next.js Script component
      */}
      <Script 
        type="module" 
        src="https://gradio.s3-us-west-2.amazonaws.com/6.28.0/gradio.js" 
        strategy="lazyOnload"
      />
      
      {/* 
        This is the custom Gradio Web Component. 
        It will automatically render the Hugging Face Space UI here.
      */}
      {/* @ts-ignore - Custom web component */}
      <gradio-app 
        src="https://muhammadburhan-career-agent-backend.hf.space" 
        theme_mode="dark"
        style={{ width: '100%', height: '100%', border: 'none' }}
      ></gradio-app>

      {/* 
        Option 2: Fallback Iframe (Commented out, but ready if web component fails)
        
        <iframe
          src="https://muhammadburhan-career-agent-backend.hf.space/?__theme=dark"
          frameBorder="0"
          style={{ width: '100%', height: '100%', border: 'none' }}
          allow="microphone; camera; clipboard-read; clipboard-write"
        ></iframe>
      */}
    </div>
  )
}
