// App preset data — seeded from the logo assets in `frontend/public/logos/` plus
// additional well-known apps (social/media/dev) and the `news` category, to reach
// at least 60 entries (task 3.3). See design.md, section "1. Preset registry".
//
// NOTE on `icon` encoding:
// - Presets backed by a real asset in `public/logos/` use `{ type: 'logo', value: '/logos/<file>' }`.
// - Presets with no logo asset use `{ type: 'fontawesome', value: 'prefix:iconName' }`,
//   following the same `"prefix:iconName"` string encoding documented in `system.ts`.
//
// NOTE on `action`: every preset here defaults to `{ type: 'cross_platform', config: { action: 'open_url', url: ... } }`,
// i.e. "open this app/site's homepage". This mirrors the `open-url` / `launch-browser`
// system presets and gives every app preset a working default action out of the box.

import type { ButtonPreset } from './types'

// ---------------------------------------------------------------------------
// Logo-backed presets (one per file in frontend/public/logos/)
// ---------------------------------------------------------------------------
const logoPresets: ButtonPreset[] = [
  {
    id: 'adobe',
    name: 'Adobe',
    category: 'media',
    brand: { primary: '#FF0000' },
    icon: { type: 'logo', value: '/logos/adobe-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.adobe.com' } },
    keywords: ['creative cloud', 'photoshop']
  },
  {
    id: 'antigravity',
    name: 'Antigravity',
    category: 'ai',
    brand: { primary: '#6C5CE7' },
    icon: { type: 'logo', value: '/logos/antigravity-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://antigravity.google' } },
    keywords: ['google', 'agent']
  },
  {
    id: 'bedrock',
    name: 'Amazon Bedrock',
    category: 'ai',
    brand: { primary: '#FF9900' },
    icon: { type: 'logo', value: '/logos/bedrock-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://aws.amazon.com/bedrock' } },
    keywords: ['aws', 'amazon']
  },
  {
    id: 'claude',
    name: 'Claude',
    category: 'ai',
    brand: { primary: '#D97757' },
    icon: { type: 'logo', value: '/logos/claude-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://claude.ai' } },
    keywords: ['anthropic', 'chatbot']
  },
  {
    id: 'claude-code',
    name: 'Claude Code',
    category: 'dev',
    brand: { primary: '#D97757' },
    icon: { type: 'logo', value: '/logos/claudecode-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://claude.com/product/claude-code' } },
    keywords: ['claude', 'anthropic', 'cli']
  },
  {
    id: 'cline',
    name: 'Cline',
    category: 'dev',
    brand: { primary: '#3498db' },
    icon: { type: 'logo', value: '/logos/cline.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://cline.bot' } },
    keywords: ['ai coding', 'vscode']
  },
  {
    id: 'codex',
    name: 'Codex',
    category: 'ai',
    brand: { primary: '#412991' },
    icon: { type: 'logo', value: '/logos/codex-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://openai.com/codex' } },
    keywords: ['openai', 'coding agent']
  },
  {
    id: 'crewai',
    name: 'CrewAI',
    category: 'ai',
    brand: { primary: '#FF5A1F' },
    icon: { type: 'logo', value: '/logos/crewai-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.crewai.com' } },
    keywords: ['agents', 'orchestration']
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    category: 'ai',
    brand: { primary: '#4D6BFE' },
    icon: { type: 'logo', value: '/logos/deepseek-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.deepseek.com' } },
    keywords: ['llm', 'chatbot']
  },
  {
    id: 'figma',
    name: 'Figma',
    category: 'dev',
    brand: { primary: '#F24E1E' },
    icon: { type: 'logo', value: '/logos/figma-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.figma.com' } },
    keywords: ['design', 'ui']
  },
  {
    id: 'flux',
    name: 'Flux',
    category: 'media',
    brand: { primary: '#1A1A1A' },
    icon: { type: 'logo', value: '/logos/flux.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://blackforestlabs.ai' } },
    keywords: ['image generation', 'black forest labs']
  },
  {
    id: 'gemini',
    name: 'Gemini',
    category: 'ai',
    brand: { primary: '#4285F4' },
    icon: { type: 'logo', value: '/logos/gemini-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://gemini.google.com' } },
    keywords: ['google', 'chatbot']
  },
  {
    id: 'github',
    name: 'GitHub',
    category: 'dev',
    brand: { primary: '#181717' },
    icon: { type: 'logo', value: '/logos/github.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://github.com' } },
    keywords: ['git', 'repo']
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    category: 'dev',
    brand: { primary: '#181717' },
    icon: { type: 'logo', value: '/logos/githubcopilot.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://github.com/features/copilot' } },
    keywords: ['ai coding', 'github']
  },
  {
    id: 'google',
    name: 'Google',
    category: 'dev',
    brand: { primary: '#4285F4' },
    icon: { type: 'logo', value: '/logos/google-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.google.com' } },
    keywords: ['search', 'browser']
  },
  {
    id: 'grok',
    name: 'Grok',
    category: 'ai',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/grok.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://grok.com' } },
    keywords: ['xai', 'chatbot']
  },
  {
    id: 'huggingface',
    name: 'Hugging Face',
    category: 'ai',
    brand: { primary: '#FFD21E' },
    icon: { type: 'logo', value: '/logos/huggingface-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://huggingface.co' } },
    keywords: ['models', 'datasets']
  },
  {
    id: 'ideogram',
    name: 'Ideogram',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/ideogram.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://ideogram.ai' } },
    keywords: ['image generation', 'art']
  },
  {
    id: 'kilocode',
    name: 'Kilo Code',
    category: 'dev',
    brand: { primary: '#3498db' },
    icon: { type: 'logo', value: '/logos/kilocode.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://kilocode.ai' } },
    keywords: ['ai coding', 'vscode']
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    category: 'ai',
    brand: { primary: '#1C3C3C' },
    icon: { type: 'logo', value: '/logos/langgraph-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.langchain.com/langgraph' } },
    keywords: ['langchain', 'agents']
  },
  {
    id: 'lightricks',
    name: 'Lightricks',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/lightricks.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.lightricks.com' } },
    keywords: ['ltx studio', 'video']
  },
  {
    id: 'manus',
    name: 'Manus',
    category: 'ai',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/manus.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://manus.im' } },
    keywords: ['agent', 'autonomous']
  },
  {
    id: 'microsoft',
    name: 'Microsoft',
    category: 'dev',
    brand: { primary: '#00A4EF' },
    icon: { type: 'logo', value: '/logos/microsoft-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.microsoft.com' } },
    keywords: ['office', 'windows']
  },
  {
    id: 'midjourney',
    name: 'Midjourney',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/midjourney.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.midjourney.com' } },
    keywords: ['image generation', 'art']
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    category: 'ai',
    brand: { primary: '#E31C79' },
    icon: { type: 'logo', value: '/logos/minimax-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.minimax.io' } },
    keywords: ['llm', 'chatbot']
  },
  {
    id: 'n8n',
    name: 'n8n',
    category: 'dev',
    brand: { primary: '#EA4B71' },
    icon: { type: 'logo', value: '/logos/n8n-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://n8n.io' } },
    keywords: ['automation', 'workflow']
  },
  {
    id: 'notebooklm',
    name: 'NotebookLM',
    category: 'ai',
    brand: { primary: '#4285F4' },
    icon: { type: 'logo', value: '/logos/notebooklm.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://notebooklm.google.com' } },
    keywords: ['google', 'research']
  },
  {
    id: 'notion',
    name: 'Notion',
    category: 'dev',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/notion.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.notion.so' } },
    keywords: ['notes', 'productivity']
  },
  {
    id: 'ollama',
    name: 'Ollama',
    category: 'ai',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/ollama.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://ollama.com' } },
    keywords: ['local llm', 'models']
  },
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'ai',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/openai.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://openai.com' } },
    keywords: ['gpt', 'chatgpt']
  },
  {
    id: 'openclaw',
    name: 'OpenClaw',
    category: 'ai',
    brand: { primary: '#FF6B00' },
    icon: { type: 'logo', value: '/logos/openclaw-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://openclaw.ai' } },
    keywords: ['agent', 'automation']
  },
  {
    id: 'recraft',
    name: 'Recraft',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/recraft.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.recraft.ai' } },
    keywords: ['image generation', 'vector']
  },
  {
    id: 'runway',
    name: 'Runway',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/runway.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://runwayml.com' } },
    keywords: ['video generation', 'ai video']
  },
  {
    id: 'sora',
    name: 'Sora',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/sora-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://sora.chatgpt.com' } },
    keywords: ['openai', 'video generation']
  },
  {
    id: 'suno',
    name: 'Suno',
    category: 'media',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/suno.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://suno.com' } },
    keywords: ['music generation', 'ai music']
  },
  {
    id: 'v0',
    name: 'v0',
    category: 'dev',
    brand: { primary: '#000000' },
    icon: { type: 'logo', value: '/logos/v0.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://v0.dev' } },
    keywords: ['vercel', 'ai coding']
  },
  {
    id: 'zapier',
    name: 'Zapier',
    category: 'dev',
    brand: { primary: '#FF4A00' },
    icon: { type: 'logo', value: '/logos/zapier-color.png' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://zapier.com' } },
    keywords: ['automation', 'workflow']
  }
]

// ---------------------------------------------------------------------------
// Additional well-known apps (no logo asset — FontAwesome brand icons)
// ---------------------------------------------------------------------------
const additionalPresets: ButtonPreset[] = [
  {
    id: 'twitter-x',
    name: 'X (Twitter)',
    category: 'social',
    brand: { primary: '#000000' },
    icon: { type: 'fontawesome', value: 'fab:x-twitter' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://x.com' } },
    keywords: ['twitter', 'social']
  },
  {
    id: 'discord',
    name: 'Discord',
    category: 'social',
    brand: { primary: '#5865F2' },
    icon: { type: 'fontawesome', value: 'fab:discord' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://discord.com' } },
    keywords: ['chat', 'voice']
  },
  {
    id: 'slack',
    name: 'Slack',
    category: 'social',
    brand: { primary: '#4A154B' },
    icon: { type: 'fontawesome', value: 'fab:slack' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://slack.com' } },
    keywords: ['chat', 'work']
  },
  {
    id: 'whatsapp',
    name: 'WhatsApp',
    category: 'social',
    brand: { primary: '#25D366' },
    icon: { type: 'fontawesome', value: 'fab:whatsapp' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://web.whatsapp.com' } },
    keywords: ['chat', 'messaging']
  },
  {
    id: 'telegram',
    name: 'Telegram',
    category: 'social',
    brand: { primary: '#26A5E4' },
    icon: { type: 'fontawesome', value: 'fab:telegram' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://web.telegram.org' } },
    keywords: ['chat', 'messaging']
  },
  {
    id: 'instagram',
    name: 'Instagram',
    category: 'social',
    brand: { primary: '#E4405F' },
    icon: { type: 'fontawesome', value: 'fab:instagram' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.instagram.com' } },
    keywords: ['photos', 'social']
  },
  {
    id: 'youtube',
    name: 'YouTube',
    category: 'media',
    brand: { primary: '#FF0000' },
    icon: { type: 'fontawesome', value: 'fab:youtube' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.youtube.com' } },
    keywords: ['video', 'streaming']
  },
  {
    id: 'reddit',
    name: 'Reddit',
    category: 'social',
    brand: { primary: '#FF4500' },
    icon: { type: 'fontawesome', value: 'fab:reddit' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.reddit.com' } },
    keywords: ['forum', 'social']
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    category: 'social',
    brand: { primary: '#0A66C2' },
    icon: { type: 'fontawesome', value: 'fab:linkedin' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.linkedin.com' } },
    keywords: ['professional', 'network']
  },
  {
    id: 'facebook',
    name: 'Facebook',
    category: 'social',
    brand: { primary: '#1877F2' },
    icon: { type: 'fontawesome', value: 'fab:facebook' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.facebook.com' } },
    keywords: ['social', 'network']
  },
  {
    id: 'spotify',
    name: 'Spotify',
    category: 'media',
    brand: { primary: '#1DB954' },
    icon: { type: 'fontawesome', value: 'fab:spotify' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://open.spotify.com' } },
    keywords: ['music', 'streaming']
  },
  {
    id: 'netflix',
    name: 'Netflix',
    category: 'media',
    brand: { primary: '#E50914' },
    icon: { type: 'fontawesome', value: 'fas:film' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.netflix.com' } },
    keywords: ['streaming', 'video']
  },
  {
    id: 'twitch',
    name: 'Twitch',
    category: 'media',
    brand: { primary: '#9146FF' },
    icon: { type: 'fontawesome', value: 'fab:twitch' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.twitch.tv' } },
    keywords: ['streaming', 'gaming']
  },
  {
    id: 'vlc',
    name: 'VLC',
    category: 'media',
    brand: { primary: '#FF8800' },
    icon: { type: 'fontawesome', value: 'fas:play-circle' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'vlc.exe' } },
    keywords: ['media player', 'video']
  },
  {
    id: 'vscode',
    name: 'VS Code',
    category: 'dev',
    brand: { primary: '#007ACC' },
    icon: { type: 'fontawesome', value: 'fas:code' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'code' } },
    keywords: ['editor', 'ide']
  },
  {
    id: 'docker',
    name: 'Docker',
    category: 'dev',
    brand: { primary: '#2496ED' },
    icon: { type: 'fontawesome', value: 'fab:docker' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'Docker Desktop.exe' } },
    keywords: ['containers', 'devops']
  },
  {
    id: 'postman',
    name: 'Postman',
    category: 'dev',
    brand: { primary: '#FF6C37' },
    icon: { type: 'fontawesome', value: 'fas:paper-plane' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.postman.com' } },
    keywords: ['api', 'testing']
  },
  {
    id: 'chrome',
    name: 'Chrome',
    category: 'dev',
    brand: { primary: '#4285F4' },
    icon: { type: 'fontawesome', value: 'fab:chrome' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'chrome.exe' } },
    keywords: ['browser', 'google']
  },
  {
    id: 'firefox',
    name: 'Firefox',
    category: 'dev',
    brand: { primary: '#FF7139' },
    icon: { type: 'fontawesome', value: 'fab:firefox' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'firefox.exe' } },
    keywords: ['browser', 'mozilla']
  },
  {
    id: 'zoom',
    name: 'Zoom',
    category: 'social',
    brand: { primary: '#2D8CFF' },
    icon: { type: 'fontawesome', value: 'fas:video' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://zoom.us' } },
    keywords: ['video call', 'meeting']
  },
  {
    id: 'obs-studio',
    name: 'OBS Studio',
    category: 'media',
    brand: { primary: '#302E31' },
    icon: { type: 'fontawesome', value: 'fas:video' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'obs64.exe' } },
    keywords: ['streaming', 'recording']
  },
  {
    id: 'steam',
    name: 'Steam',
    category: 'media',
    brand: { primary: '#1B2838' },
    icon: { type: 'fontawesome', value: 'fab:steam' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'steam.exe' } },
    keywords: ['gaming', 'games']
  },
  {
    id: 'gmail',
    name: 'Gmail',
    category: 'dev',
    brand: { primary: '#EA4335' },
    icon: { type: 'fontawesome', value: 'fas:envelope' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://mail.google.com' } },
    keywords: ['email', 'google']
  }
]

// ---------------------------------------------------------------------------
// News category — Israeli news/tech sites (no logo assets — generic icon)
// ---------------------------------------------------------------------------
const newsPresets: ButtonPreset[] = [
  {
    id: 'n12',
    name: 'N12',
    category: 'news',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:newspaper' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.n12.co.il' } },
    keywords: ['news', 'israel']
  },
  {
    id: 'ynet',
    name: 'Ynet',
    category: 'news',
    brand: { primary: '#c0392b' },
    icon: { type: 'fontawesome', value: 'fas:newspaper' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.ynet.co.il' } },
    keywords: ['news', 'israel']
  },
  {
    id: 'walla',
    name: 'Walla',
    category: 'news',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:newspaper' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.walla.co.il' } },
    keywords: ['news', 'israel']
  },
  {
    id: 'mako',
    name: 'Mako',
    category: 'news',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:newspaper' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.mako.co.il' } },
    keywords: ['news', 'israel']
  },
  {
    id: 'sport1',
    name: 'Sport1',
    category: 'news',
    brand: { primary: '#27ae60' },
    icon: { type: 'fontawesome', value: 'fas:futbol' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.sport1.co.il' } },
    keywords: ['sports', 'news']
  },
  {
    id: 'one',
    name: 'ONE',
    category: 'news',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:futbol' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.one.co.il' } },
    keywords: ['sports', 'news']
  },
  {
    id: 'geektime',
    name: 'Geektime',
    category: 'news',
    brand: { primary: '#f39c12' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.geektime.co.il' } },
    keywords: ['tech', 'news']
  },
  {
    id: 'tgspot',
    name: 'TGSpot',
    category: 'news',
    brand: { primary: '#34495e' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.tgspot.co.il' } },
    keywords: ['tech', 'news']
  },
  {
    id: 'lastartup',
    name: 'Lastartup',
    category: 'news',
    brand: { primary: '#e67e22' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.lastartup.co.il' } },
    keywords: ['startups', 'news']
  },
  {
    id: 'letsai',
    name: 'Letsai',
    category: 'news',
    brand: { primary: '#9b59b6' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.letsai.co.il' } },
    keywords: ['ai', 'news']
  }
]

export const appPresets: ButtonPreset[] = [...logoPresets, ...additionalPresets, ...newsPresets]
