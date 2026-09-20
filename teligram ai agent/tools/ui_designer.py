import os

class UIDesignerTool:
    """Generates complete, page-by-page UI/UX code and design specifications."""
    
    @staticmethod
    def generate_page(title: str, description: str, theme: str = "dark") -> str:
        bg_class = "bg-slate-950 text-slate-100" if theme == "dark" else "bg-slate-50 text-slate-900"
        card_class = "bg-slate-900/80 border-slate-800" if theme == "dark" else "bg-white border-slate-200"
        
        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - CyberVerse UI</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
  </style>
</head>
<body class="{bg_class} min-h-screen antialiased selection:bg-cyan-500 selection:text-white">
  <!-- Navigation -->
  <header class="border-b { 'border-slate-800' if theme == 'dark' else 'border-slate-200' } sticky top-0 backdrop-blur-md z-50">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
          CV
        </div>
        <span class="font-bold tracking-tight text-lg">{title}</span>
      </div>
      <nav class="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-400">
        <a href="#overview" class="hover:text-cyan-400 transition">Overview</a>
        <a href="#features" class="hover:text-cyan-400 transition">Features</a>
        <a href="#demo" class="hover:text-cyan-400 transition">Live Demo</a>
      </nav>
      <div>
        <button class="px-4 py-2 text-sm font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition shadow-md shadow-cyan-500/20">
          Get Started
        </button>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <main class="max-w-7xl mx-auto px-6 py-20">
    <div class="max-w-3xl">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-6">
        <span>✨ Interactive UI Preview</span>
      </div>
      <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-6">
        {title}
      </h1>
      <p class="text-lg md:text-xl text-slate-400 leading-relaxed mb-8">
        {description}
      </p>
    </div>

    <!-- Dynamic Card Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
      <div class="p-6 rounded-2xl border {card_class} shadow-xl hover:border-cyan-500/40 transition">
        <div class="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold mb-4">01</div>
        <h3 class="text-lg font-bold mb-2">High Fidelity Design</h3>
        <p class="text-sm text-slate-400 leading-relaxed">Page-by-page production layout ready for direct Figma and Frontend integration.</p>
      </div>
      <div class="p-6 rounded-2xl border {card_class} shadow-xl hover:border-cyan-500/40 transition">
        <div class="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold mb-4">02</div>
        <h3 class="text-lg font-bold mb-2">Adaptive Responsiveness</h3>
        <p class="text-sm text-slate-400 leading-relaxed">Fully responsive grid adapting seamlessly across mobile, tablet, and ultra-wide screens.</p>
      </div>
      <div class="p-6 rounded-2xl border {card_class} shadow-xl hover:border-cyan-500/40 transition">
        <div class="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold mb-4">03</div>
        <h3 class="text-lg font-bold mb-2">Modern Micro-Interactions</h3>
        <p class="text-sm text-slate-400 leading-relaxed">Sleek gradients, glassmorphism cards, and fluid interactive states.</p>
      </div>
    </div>
  </main>
</body>
</html>"""
        return template
