export interface TemplateButton {
  label: string
  icon: string[]
  action: { type: string; config: Record<string, unknown> }
  style?: { backgroundColor?: string; textColor?: string }
  tooltip?: string
}

export interface AppTemplate {
  id: string
  name: string
  description: string
  icon: string[]
  logo?: string
  color: string
  buttons: TemplateButton[]
}

export interface TemplateCategory {
  id: string
  name: string
  icon: string[]
  templates: AppTemplate[]
}

// ─── helpers ────────────────────────────────────────────────────────────────
const hk = (keys: string[]) => ({ type: 'hotkey', config: { keys } })
const cmd = (command: string) => ({ type: 'command', config: { command } })
const url = (u: string) => ({ type: 'url', config: { url: u } })
const prog = (program: string) => ({ type: 'program', config: { program } })

// ─── AI Assistants ───────────────────────────────────────────────────────────
const aiAssistants: AppTemplate[] = [
  {
    id: 'chatgpt',
    name: 'ChatGPT',
    description: 'OpenAI ChatGPT shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/chatgpt.png',
    color: '#10a37f',
    buttons: [
      { label: 'New Chat', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'o']), tooltip: 'Start a new conversation' },
      { label: 'Search', icon: ['fas', 'magnifying-glass'], action: hk(['ctrl', 'k']), tooltip: 'Search chats' },
      { label: 'Open ChatGPT', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://chat.openai.com'), tooltip: 'Open in browser' },
      { label: 'GPT-4o', icon: ['fas', 'brain'], action: url('https://chat.openai.com/?model=gpt-4o'), tooltip: 'Open GPT-4o' },
      { label: 'DALL·E', icon: ['fas', 'image'], action: url('https://chat.openai.com/?model=dall-e-3'), tooltip: 'Open image generation' },
      { label: 'Browse GPTs', icon: ['fas', 'puzzle-piece'], action: url('https://chat.openai.com/gpts'), tooltip: 'Browse GPTs' },
    ],
  },
  {
    id: 'claude',
    name: 'Claude',
    description: 'Anthropic Claude shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/claude.png',
    color: '#d97757',
    buttons: [
      { label: 'New Chat', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Start a new conversation' },
      { label: 'Open Claude', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://claude.ai'), tooltip: 'Open in browser' },
      { label: 'Projects', icon: ['fas', 'folder'], action: url('https://claude.ai/projects'), tooltip: 'Open Projects' },
      { label: 'Upload File', icon: ['fas', 'paperclip'], action: hk(['ctrl', 'u']), tooltip: 'Attach a file' },
      { label: 'Copy Last', icon: ['fas', 'copy'], action: hk(['ctrl', 'shift', 'c']), tooltip: 'Copy last response' },
    ],
  },
  {
    id: 'gemini',
    name: 'Gemini',
    description: 'Google Gemini shortcuts',
    icon: ['fas', 'gem'],
    logo: '/logos/gemini.png',
    color: '#4285f4',
    buttons: [
      { label: 'Open Gemini', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://gemini.google.com'), tooltip: 'Open Gemini' },
      { label: 'New Chat', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New conversation' },
      { label: 'Gemini Advanced', icon: ['fas', 'star'], action: url('https://gemini.google.com/advanced'), tooltip: 'Open Gemini Advanced' },
      { label: 'AI Studio', icon: ['fas', 'flask'], action: url('https://aistudio.google.com'), tooltip: 'Open AI Studio' },
    ],
  },
  {
    id: 'grok',
    name: 'Grok',
    description: 'xAI Grok shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/grok.png',
    color: '#1da1f2',
    buttons: [
      { label: 'Open Grok', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://grok.x.ai'), tooltip: 'Open Grok' },
      { label: 'New Chat', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New conversation' },
      { label: 'Grok 3', icon: ['fas', 'brain'], action: url('https://grok.x.ai'), tooltip: 'Open Grok 3' },
    ],
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek AI shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/deepseek.png',
    color: '#4f6ef7',
    buttons: [
      { label: 'Open DeepSeek', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://chat.deepseek.com'), tooltip: 'Open DeepSeek' },
      { label: 'New Chat', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New conversation' },
      { label: 'DeepThink R1', icon: ['fas', 'brain'], action: url('https://chat.deepseek.com'), tooltip: 'DeepThink R1 mode' },
    ],
  },
  {
    id: 'notebooklm',
    name: 'NotebookLM',
    description: 'Google NotebookLM shortcuts',
    icon: ['fas', 'book'],
    logo: '/logos/notebooklm.png',
    color: '#1a73e8',
    buttons: [
      { label: 'Open NotebookLM', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://notebooklm.google.com'), tooltip: 'Open NotebookLM' },
      { label: 'New Notebook', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Create new notebook' },
      { label: 'Audio Overview', icon: ['fas', 'headphones'], action: hk(['ctrl', 'shift', 'a']), tooltip: 'Generate audio overview' },
    ],
  },
  {
    id: 'manus',
    name: 'Manus',
    description: 'Manus AI agent shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/manus.png',
    color: '#6c63ff',
    buttons: [
      { label: 'Open Manus', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://manus.im'), tooltip: 'Open Manus' },
      { label: 'New Task', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Start new task' },
    ],
  },
]

// ─── AI Coding ───────────────────────────────────────────────────────────────
const aiCoding: AppTemplate[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    description: 'Anthropic Claude Code CLI shortcuts',
    icon: ['fas', 'terminal'],
    logo: '/logos/claude-code.png',
    color: '#d97757',
    buttons: [
      { label: 'New Session', icon: ['fas', 'plus'], action: cmd('claude'), tooltip: 'Start Claude Code' },
      { label: 'Continue', icon: ['fas', 'rotate-right'], action: cmd('claude --continue'), tooltip: 'Continue last session' },
      { label: 'Resume', icon: ['fas', 'play'], action: cmd('claude --resume'), tooltip: 'Resume a session' },
      { label: 'Print Mode', icon: ['fas', 'print'], action: cmd('claude -p ""'), tooltip: 'Non-interactive print mode' },
      { label: 'AI Commit', icon: ['fas', 'code-commit'], action: cmd('git add -A && claude -p "write a commit message and commit"'), tooltip: 'AI-powered commit' },
      { label: 'Review Diff', icon: ['fas', 'code-pull-request'], action: cmd('claude -p "review the current git diff"'), tooltip: 'Review changes' },
    ],
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    description: 'GitHub Copilot shortcuts',
    icon: ['fas', 'code'],
    logo: '/logos/github-copilot.png',
    color: '#6e40c9',
    buttons: [
      { label: 'Accept', icon: ['fas', 'check'], action: hk(['tab']), tooltip: 'Accept suggestion' },
      { label: 'Dismiss', icon: ['fas', 'xmark'], action: hk(['escape']), tooltip: 'Dismiss suggestion' },
      { label: 'Next', icon: ['fas', 'chevron-right'], action: hk(['alt', ']']), tooltip: 'Next suggestion' },
      { label: 'Prev', icon: ['fas', 'chevron-left'], action: hk(['alt', '[']), tooltip: 'Previous suggestion' },
      { label: 'Chat', icon: ['fas', 'comments'], action: hk(['ctrl', 'shift', 'i']), tooltip: 'Open Copilot Chat' },
      { label: 'Inline Chat', icon: ['fas', 'comment-dots'], action: hk(['ctrl', 'i']), tooltip: 'Inline chat' },
    ],
  },
  {
    id: 'cline',
    name: 'Cline',
    description: 'Cline AI coding assistant shortcuts',
    icon: ['fas', 'terminal'],
    logo: '/logos/cline.png',
    color: '#7c3aed',
    buttons: [
      { label: 'Open Cline', icon: ['fas', 'sidebar'], action: hk(['ctrl', 'shift', 'p']), tooltip: 'Open Cline panel' },
      { label: 'New Task', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New Cline task' },
      { label: 'Approve', icon: ['fas', 'check'], action: hk(['enter']), tooltip: 'Approve action' },
      { label: 'Reject', icon: ['fas', 'xmark'], action: hk(['escape']), tooltip: 'Reject action' },
    ],
  },
  {
    id: 'kilo-code',
    name: 'Kilo Code',
    description: 'Kilo Code AI assistant shortcuts',
    icon: ['fas', 'code'],
    logo: '/logos/kilo-code.png',
    color: '#0ea5e9',
    buttons: [
      { label: 'Open Panel', icon: ['fas', 'sidebar'], action: hk(['ctrl', 'shift', 'k']), tooltip: 'Open Kilo Code' },
      { label: 'New Task', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New task' },
    ],
  },
  {
    id: 'codex',
    name: 'Codex',
    description: 'OpenAI Codex CLI shortcuts',
    icon: ['fas', 'terminal'],
    logo: '/logos/codex.png',
    color: '#10a37f',
    buttons: [
      { label: 'Start Codex', icon: ['fas', 'play'], action: cmd('codex'), tooltip: 'Start Codex CLI' },
      { label: 'Full Auto', icon: ['fas', 'bolt'], action: cmd('codex --approval-mode full-auto'), tooltip: 'Full auto mode' },
      { label: 'Quiet Mode', icon: ['fas', 'volume-xmark'], action: cmd('codex -q'), tooltip: 'Quiet mode' },
    ],
  },
  {
    id: 'openclaw',
    name: 'OpenClaw',
    description: 'OpenClaw AI shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/openclaw.png',
    color: '#f59e0b',
    buttons: [
      { label: 'Open OpenClaw', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://openclaw.ai'), tooltip: 'Open OpenClaw' },
    ],
  },
]

// ─── AI Image & Video ────────────────────────────────────────────────────────
const aiImageVideo: AppTemplate[] = [
  {
    id: 'midjourney',
    name: 'Midjourney',
    description: 'Midjourney image generation shortcuts',
    icon: ['fas', 'image'],
    logo: '/logos/midjourney.png',
    color: '#000000',
    buttons: [
      { label: 'Open MJ', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://www.midjourney.com'), tooltip: 'Open Midjourney' },
      { label: 'Discord', icon: ['fab', 'discord'], action: url('https://discord.com/channels/@me'), tooltip: 'Open Discord for MJ' },
      { label: '/imagine', icon: ['fas', 'wand-magic-sparkles'], action: { type: 'text', config: { text: '/imagine prompt: ' } }, tooltip: 'Type /imagine' },
      { label: '/describe', icon: ['fas', 'align-left'], action: { type: 'text', config: { text: '/describe ' } }, tooltip: 'Describe an image' },
      { label: 'Upscale', icon: ['fas', 'up-right-and-down-left-from-center'], action: { type: 'text', config: { text: 'U1' } }, tooltip: 'Upscale option 1' },
      { label: 'Variation', icon: ['fas', 'shuffle'], action: { type: 'text', config: { text: 'V1' } }, tooltip: 'Variation option 1' },
    ],
  },
  {
    id: 'ideogram',
    name: 'Ideogram',
    description: 'Ideogram AI image shortcuts',
    icon: ['fas', 'image'],
    logo: '/logos/ideogram.png',
    color: '#6366f1',
    buttons: [
      { label: 'Open Ideogram', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://ideogram.ai'), tooltip: 'Open Ideogram' },
      { label: 'New Image', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Generate new image' },
      { label: 'Remix', icon: ['fas', 'shuffle'], action: hk(['ctrl', 'r']), tooltip: 'Remix image' },
    ],
  },
  {
    id: 'recraft',
    name: 'Recraft',
    description: 'Recraft AI design shortcuts',
    icon: ['fas', 'pen-nib'],
    logo: '/logos/recraft.png',
    color: '#f43f5e',
    buttons: [
      { label: 'Open Recraft', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://www.recraft.ai'), tooltip: 'Open Recraft' },
      { label: 'New Canvas', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New canvas' },
    ],
  },
  {
    id: 'flux',
    name: 'Flux',
    description: 'Black Forest Labs Flux shortcuts',
    icon: ['fas', 'image'],
    logo: '/logos/flux.png',
    color: '#0f172a',
    buttons: [
      { label: 'Open Flux', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://flux1.ai'), tooltip: 'Open Flux' },
      { label: 'Flux Pro', icon: ['fas', 'star'], action: url('https://flux1.ai/flux-pro'), tooltip: 'Flux Pro' },
    ],
  },
  {
    id: 'sora',
    name: 'Sora',
    description: 'OpenAI Sora video generation',
    icon: ['fas', 'video'],
    logo: '/logos/sora.png',
    color: '#10a37f',
    buttons: [
      { label: 'Open Sora', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://sora.com'), tooltip: 'Open Sora' },
      { label: 'New Video', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Create new video' },
    ],
  },
  {
    id: 'runway',
    name: 'Runway',
    description: 'Runway ML video generation shortcuts',
    icon: ['fas', 'film'],
    logo: '/logos/runway.png',
    color: '#1a1a2e',
    buttons: [
      { label: 'Open Runway', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://runwayml.com'), tooltip: 'Open Runway' },
      { label: 'Gen-3 Alpha', icon: ['fas', 'video'], action: url('https://app.runwayml.com/video-tools/teams/me/ai-tools/gen3a'), tooltip: 'Gen-3 Alpha' },
      { label: 'Img to Video', icon: ['fas', 'images'], action: url('https://app.runwayml.com'), tooltip: 'Image to video' },
    ],
  },
  {
    id: 'lightricks',
    name: 'Lightricks',
    description: 'Lightricks AI creative tools',
    icon: ['fas', 'wand-magic-sparkles'],
    logo: '/logos/lightricks.png',
    color: '#ff6b6b',
    buttons: [
      { label: 'Open Lightricks', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://www.lightricks.com'), tooltip: 'Open Lightricks' },
      { label: 'LTX Studio', icon: ['fas', 'film'], action: url('https://ltx.studio'), tooltip: 'Open LTX Studio' },
    ],
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    description: 'MiniMax AI video generation',
    icon: ['fas', 'video'],
    logo: '/logos/minimax.png',
    color: '#7c3aed',
    buttons: [
      { label: 'Open MiniMax', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://hailuoai.video'), tooltip: 'Open MiniMax' },
    ],
  },
  {
    id: 'suno',
    name: 'Suno',
    description: 'Suno AI music generation',
    icon: ['fas', 'music'],
    logo: '/logos/suno.png',
    color: '#f59e0b',
    buttons: [
      { label: 'Open Suno', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://suno.com'), tooltip: 'Open Suno' },
      { label: 'Create Song', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'Create new song' },
      { label: 'My Songs', icon: ['fas', 'list'], action: url('https://suno.com/me'), tooltip: 'My songs' },
    ],
  },
]

// ─── Design & Creative ───────────────────────────────────────────────────────
const designCreative: AppTemplate[] = [
  {
    id: 'figma',
    name: 'Figma',
    description: 'Figma design shortcuts',
    icon: ['fab', 'figma'],
    logo: '/logos/figma.png',
    color: '#f24e1e',
    buttons: [
      { label: 'Frame', icon: ['fas', 'square'], action: hk(['f']), tooltip: 'Create frame' },
      { label: 'Rectangle', icon: ['fas', 'vector-square'], action: hk(['r']), tooltip: 'Draw rectangle' },
      { label: 'Text', icon: ['fas', 'font'], action: hk(['t']), tooltip: 'Add text' },
      { label: 'Pen', icon: ['fas', 'pen-nib'], action: hk(['p']), tooltip: 'Pen tool' },
      { label: 'Component', icon: ['fas', 'cube'], action: hk(['ctrl', 'alt', 'k']), tooltip: 'Create component' },
      { label: 'Auto Layout', icon: ['fas', 'table-columns'], action: hk(['shift', 'a']), tooltip: 'Add auto layout' },
      { label: 'Group', icon: ['fas', 'object-group'], action: hk(['ctrl', 'g']), tooltip: 'Group selection' },
      { label: 'Ungroup', icon: ['fas', 'object-ungroup'], action: hk(['ctrl', 'shift', 'g']), tooltip: 'Ungroup' },
      { label: 'Zoom Fit', icon: ['fas', 'expand'], action: hk(['shift', '1']), tooltip: 'Zoom to fit' },
      { label: 'Preview', icon: ['fas', 'play'], action: hk(['ctrl', 'alt', 'enter']), tooltip: 'Present' },
    ],
  },
  {
    id: 'adobe-cc',
    name: 'Adobe CC',
    description: 'Adobe Creative Cloud shortcuts',
    icon: ['fas', 'palette'],
    logo: '/logos/adobe-cc.png',
    color: '#ff0000',
    buttons: [
      { label: 'Photoshop', icon: ['fas', 'image'], action: prog('photoshop'), tooltip: 'Open Photoshop' },
      { label: 'Illustrator', icon: ['fas', 'pen-nib'], action: prog('illustrator'), tooltip: 'Open Illustrator' },
      { label: 'Premiere', icon: ['fas', 'film'], action: prog('premiere'), tooltip: 'Open Premiere Pro' },
      { label: 'After Effects', icon: ['fas', 'wand-magic-sparkles'], action: prog('aftereffects'), tooltip: 'Open After Effects' },
      { label: 'CC Desktop', icon: ['fas', 'grid-2'], action: prog('adobe creative cloud'), tooltip: 'Open CC Desktop' },
    ],
  },
  {
    id: 'v0',
    name: 'v0',
    description: 'Vercel v0 UI generation shortcuts',
    icon: ['fas', 'code'],
    logo: '/logos/v0.png',
    color: '#000000',
    buttons: [
      { label: 'Open v0', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://v0.dev'), tooltip: 'Open v0' },
      { label: 'New Project', icon: ['fas', 'plus'], action: hk(['ctrl', 'shift', 'n']), tooltip: 'New project' },
    ],
  },
]

// ─── Automation & Dev ────────────────────────────────────────────────────────
const automationDev: AppTemplate[] = [
  {
    id: 'n8n',
    name: 'n8n',
    description: 'n8n workflow automation shortcuts',
    icon: ['fas', 'diagram-project'],
    logo: '/logos/n8n.png',
    color: '#ea4b71',
    buttons: [
      { label: 'Open n8n', icon: ['fas', 'arrow-up-right-from-square'], action: url('http://localhost:5678'), tooltip: 'Open n8n local' },
      { label: 'New Workflow', icon: ['fas', 'plus'], action: hk(['ctrl', 'alt', 'n']), tooltip: 'New workflow' },
      { label: 'Execute', icon: ['fas', 'play'], action: hk(['ctrl', 'enter']), tooltip: 'Execute workflow' },
      { label: 'Save', icon: ['fas', 'floppy-disk'], action: hk(['ctrl', 's']), tooltip: 'Save workflow' },
      { label: 'Zoom Fit', icon: ['fas', 'expand'], action: hk(['ctrl', 'shift', 'h']), tooltip: 'Fit to screen' },
    ],
  },
  {
    id: 'zapier',
    name: 'Zapier',
    description: 'Zapier automation shortcuts',
    icon: ['fas', 'bolt'],
    logo: '/logos/zapier.png',
    color: '#ff4a00',
    buttons: [
      { label: 'Open Zapier', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://zapier.com/app/dashboard'), tooltip: 'Open Zapier' },
      { label: 'New Zap', icon: ['fas', 'plus'], action: url('https://zapier.com/app/zaps/new'), tooltip: 'Create new Zap' },
      { label: 'My Zaps', icon: ['fas', 'list'], action: url('https://zapier.com/app/zaps'), tooltip: 'View all Zaps' },
    ],
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'GitHub shortcuts',
    icon: ['fab', 'github'],
    logo: '/logos/github.png',
    color: '#24292e',
    buttons: [
      { label: 'Open GitHub', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://github.com'), tooltip: 'Open GitHub' },
      { label: 'Pull Requests', icon: ['fas', 'code-pull-request'], action: url('https://github.com/pulls'), tooltip: 'My pull requests' },
      { label: 'Issues', icon: ['fas', 'circle-dot'], action: url('https://github.com/issues'), tooltip: 'My issues' },
      { label: 'Notifications', icon: ['fas', 'bell'], action: url('https://github.com/notifications'), tooltip: 'Notifications' },
      { label: 'Copilot', icon: ['fas', 'robot'], action: url('https://github.com/copilot'), tooltip: 'GitHub Copilot' },
    ],
  },
  {
    id: 'crewai',
    name: 'CrewAI',
    description: 'CrewAI multi-agent framework shortcuts',
    icon: ['fas', 'users'],
    logo: '/logos/crewai.png',
    color: '#e11d48',
    buttons: [
      { label: 'Open CrewAI', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://crewai.com'), tooltip: 'Open CrewAI' },
      { label: 'Docs', icon: ['fas', 'book'], action: url('https://docs.crewai.com'), tooltip: 'CrewAI docs' },
      { label: 'Run Crew', icon: ['fas', 'play'], action: cmd('crewai run'), tooltip: 'Run crew' },
      { label: 'Train', icon: ['fas', 'graduation-cap'], action: cmd('crewai train'), tooltip: 'Train crew' },
    ],
  },
  {
    id: 'langgraph',
    name: 'LangGraph',
    description: 'LangGraph agent framework shortcuts',
    icon: ['fas', 'diagram-project'],
    logo: '/logos/langgraph.png',
    color: '#1c7ed6',
    buttons: [
      { label: 'Open LangGraph', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://langchain-ai.github.io/langgraph'), tooltip: 'LangGraph docs' },
      { label: 'LangSmith', icon: ['fas', 'chart-line'], action: url('https://smith.langchain.com'), tooltip: 'Open LangSmith' },
    ],
  },
  {
    id: 'aws-bedrock',
    name: 'AWS Bedrock',
    description: 'AWS Bedrock AI shortcuts',
    icon: ['fab', 'aws'],
    logo: '/logos/aws-bedrock.png',
    color: '#ff9900',
    buttons: [
      { label: 'Open Bedrock', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://console.aws.amazon.com/bedrock'), tooltip: 'Open AWS Bedrock' },
      { label: 'Playground', icon: ['fas', 'flask'], action: url('https://console.aws.amazon.com/bedrock/home#/text-playground'), tooltip: 'Text playground' },
    ],
  },
  {
    id: 'composio',
    name: 'Composio',
    description: 'Composio MCP integration shortcuts',
    icon: ['fas', 'plug'],
    logo: '/logos/composio.png',
    color: '#6366f1',
    buttons: [
      { label: 'Open Composio', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://composio.dev'), tooltip: 'Open Composio' },
      { label: 'MCP Servers', icon: ['fas', 'server'], action: url('https://mcp.composio.dev'), tooltip: 'MCP servers' },
      { label: 'Docs', icon: ['fas', 'book'], action: url('https://docs.composio.dev'), tooltip: 'Documentation' },
    ],
  },
  {
    id: 'nango',
    name: 'Nango',
    description: 'Nango API integration shortcuts',
    icon: ['fas', 'link'],
    logo: '/logos/nango.png',
    color: '#0ea5e9',
    buttons: [
      { label: 'Open Nango', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://nango.dev'), tooltip: 'Open Nango' },
      { label: 'Dashboard', icon: ['fas', 'gauge'], action: url('https://app.nango.dev'), tooltip: 'Nango dashboard' },
    ],
  },
]

// ─── AI Models & Platforms ───────────────────────────────────────────────────
const aiPlatforms: AppTemplate[] = [
  {
    id: 'huggingface',
    name: 'HuggingFace',
    description: 'HuggingFace platform shortcuts',
    icon: ['fas', 'robot'],
    logo: '/logos/huggingface.png',
    color: '#ff9d00',
    buttons: [
      { label: 'Open HF', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://huggingface.co'), tooltip: 'Open HuggingFace' },
      { label: 'Models', icon: ['fas', 'brain'], action: url('https://huggingface.co/models'), tooltip: 'Browse models' },
      { label: 'Spaces', icon: ['fas', 'rocket'], action: url('https://huggingface.co/spaces'), tooltip: 'Browse Spaces' },
      { label: 'Datasets', icon: ['fas', 'database'], action: url('https://huggingface.co/datasets'), tooltip: 'Browse datasets' },
    ],
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Ollama local LLM shortcuts',
    icon: ['fas', 'server'],
    logo: '/logos/ollama.png',
    color: '#1a1a1a',
    buttons: [
      { label: 'Run Llama', icon: ['fas', 'play'], action: cmd('ollama run llama3.2'), tooltip: 'Run Llama 3.2' },
      { label: 'Run Mistral', icon: ['fas', 'play'], action: cmd('ollama run mistral'), tooltip: 'Run Mistral' },
      { label: 'Run Gemma', icon: ['fas', 'play'], action: cmd('ollama run gemma3'), tooltip: 'Run Gemma 3' },
      { label: 'List Models', icon: ['fas', 'list'], action: cmd('ollama list'), tooltip: 'List local models' },
      { label: 'Pull Model', icon: ['fas', 'download'], action: cmd('ollama pull llama3.2'), tooltip: 'Pull a model' },
      { label: 'Open WebUI', icon: ['fas', 'globe'], action: url('http://localhost:3000'), tooltip: 'Open Ollama WebUI' },
    ],
  },
  {
    id: 'antigravity',
    name: 'Antigravity',
    description: 'Antigravity AI shortcuts',
    icon: ['fas', 'rocket'],
    logo: '/logos/antigravity.png',
    color: '#8b5cf6',
    buttons: [
      { label: 'Open Antigravity', icon: ['fas', 'arrow-up-right-from-square'], action: url('https://antigravity.ai'), tooltip: 'Open Antigravity' },
    ],
  },
  {
    id: 'microsoft-ai',
    name: 'Microsoft AI',
    description: 'Microsoft AI tools shortcuts',
    icon: ['fab', 'microsoft'],
    logo: '/logos/microsoft-ai.png',
    color: '#0078d4',
    buttons: [
      { label: 'Copilot', icon: ['fas', 'robot'], action: url('https://copilot.microsoft.com'), tooltip: 'Open Microsoft Copilot' },
      { label: 'Azure AI', icon: ['fas', 'cloud'], action: url('https://ai.azure.com'), tooltip: 'Open Azure AI Studio' },
      { label: 'Bing AI', icon: ['fas', 'magnifying-glass'], action: url('https://www.bing.com/chat'), tooltip: 'Bing AI Chat' },
    ],
  },
  {
    id: 'google-ai',
    name: 'Google AI',
    description: 'Google AI platform shortcuts',
    icon: ['fab', 'google'],
    logo: '/logos/google-ai.png',
    color: '#4285f4',
    buttons: [
      { label: 'AI Studio', icon: ['fas', 'flask'], action: url('https://aistudio.google.com'), tooltip: 'Google AI Studio' },
      { label: 'Vertex AI', icon: ['fas', 'cloud'], action: url('https://console.cloud.google.com/vertex-ai'), tooltip: 'Vertex AI' },
      { label: 'Gemini API', icon: ['fas', 'code'], action: url('https://ai.google.dev'), tooltip: 'Gemini API docs' },
    ],
  },
]

// --- Exported categories ---
export const templateCategories: TemplateCategory[] = [
  { id: 'ai-assistants', name: 'AI Assistants', icon: ['fas', 'robot'], templates: aiAssistants },
  { id: 'ai-coding', name: 'AI Coding', icon: ['fas', 'terminal'], templates: aiCoding },
  { id: 'ai-image-video', name: 'AI Image & Video', icon: ['fas', 'image'], templates: aiImageVideo },
  { id: 'design-creative', name: 'Design & Creative', icon: ['fas', 'pen-nib'], templates: designCreative },
  { id: 'automation-dev', name: 'Automation & Dev', icon: ['fas', 'diagram-project'], templates: automationDev },
  { id: 'ai-platforms', name: 'AI Models & Platforms', icon: ['fas', 'brain'], templates: aiPlatforms },
]
