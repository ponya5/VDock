/**
 * Onboarding guides for the keys on Settings → Accounts & keys: what each
 * integration does, how to set it up, what to try next, and a ready-made
 * starter scene that is offered once the key works.
 *
 * Button actions use the real action ids from the backend catalog
 * (`gh_*` are the GitHub pack, `claude_api_prompt` the Claude pack,
 * `weather` the weather widget).
 */
import type { TemplateButton } from '@/data/appTemplates'

export interface IntegrationScene {
  /** Stable id: lets the UI tell "already added" from "not yet". */
  sceneKey: string
  name: string
  icon: string
  color: string
  buttons: TemplateButton[]
}

export interface IntegrationGuide {
  /** Matches the secret id from `GET /api/config/integrations`. */
  id: string
  title: string
  /** One line: what it unlocks. */
  summary: string
  /** How to get and add the key. */
  setup: string[]
  /** What to do once it is set. */
  next: string[]
  /** Our advice, including when you can skip the key. */
  recommendation: string
  scene: IntegrationScene
}

const gh = (type: string, config: Record<string, unknown> = {}) => ({ type, config })

export const INTEGRATION_GUIDES: Record<string, IntegrationGuide> = {
  GITHUB_TOKEN: {
    id: 'GITHUB_TOKEN',
    title: 'GitHub',
    summary: 'Live pull-request, CI and notification badges on your keys, plus one-press GitHub actions.',
    setup: [
      'Click "Get a key", sign in, and create a token (classic with the "repo" and "notifications" scopes, or a fine-grained one with read access to your repositories).',
      'Click "Set key" here and paste it. It is saved on this PC only and is never shown again.',
      'Press "Test" to confirm GitHub accepts it. You should see "signed in as <your username>".',
    ],
    next: [
      'Press "Add GitHub scene" below. It adds a scene with live PR / CI / notification badges and the common actions.',
      'Open a project in your editor and press a button: VDock works out the repository from the focused editor window, so one scene works across all your repos.',
      'Open a pull request, press "PR Checks" and watch the CI badge turn green or red. The badge also notifies you when CI fails.',
    ],
    recommendation:
      'If you already use the GitHub CLI (gh auth login) you can skip the token: the action buttons and the live badges both use that login automatically. Add a token only if gh is not installed on this PC, or you want a separate token with limited access.',
    scene: {
      sceneKey: 'integration-github',
      name: 'GitHub',
      icon: 'github',
      color: '#24292e',
      buttons: [
        { label: 'Open PRs', icon: ['fas', 'code-pull-request'], action: gh('gh_widget_prs'), tooltip: 'Live count of open pull requests' },
        { label: 'Review Me', icon: ['fas', 'user-check'], action: gh('gh_widget_prs', { only_mine: true }), tooltip: 'Pull requests waiting for your review' },
        { label: 'CI', icon: ['fas', 'heart-pulse'], action: gh('gh_widget_ci'), tooltip: 'CI status for the current branch (alerts when it fails)' },
        { label: 'Inbox', icon: ['fas', 'bell'], action: gh('gh_widget_notifications'), tooltip: 'Unread GitHub notifications' },
        { label: 'My Work', icon: ['fas', 'list-check'], action: gh('gh_status'), tooltip: 'Assigned issues, review requests and mentions' },
        { label: 'Pull Requests', icon: ['fas', 'code-pull-request'], action: gh('gh_pr_list'), tooltip: 'List open pull requests' },
        { label: 'New PR', icon: ['fas', 'circle-plus'], action: gh('gh_pr_create'), tooltip: 'Open a pull request for the current branch' },
        { label: 'Open PR', icon: ['fas', 'up-right-from-square'], action: gh('gh_pr_view'), tooltip: "Open this branch's pull request in the browser" },
        { label: 'PR Checks', icon: ['fas', 'circle-check'], action: gh('gh_pr_checks'), tooltip: 'CI results for the current pull request' },
        { label: 'Issues', icon: ['fas', 'circle-dot'], action: gh('gh_issue_list'), tooltip: 'List open issues' },
        { label: 'Runs', icon: ['fas', 'play'], action: gh('gh_run_list'), tooltip: 'Recent GitHub Actions runs' },
        { label: 'Rerun Failed', icon: ['fas', 'rotate-right'], action: gh('gh_run_rerun'), tooltip: 'Rerun the failed jobs of the latest run' },
      ],
    },
  },

  ANTHROPIC_API_KEY: {
    id: 'ANTHROPIC_API_KEY',
    title: 'Claude API',
    summary: 'One-press "ask Claude" buttons that work on whatever you copied, with the answer copied back.',
    setup: [
      'Click "Get a key", sign in to the Anthropic Console and create an API key.',
      'Click "Set key" here and paste it.',
      'Press "Test" to confirm Anthropic accepts it.',
    ],
    next: [
      'Press "Add Claude scene" below for ready-made buttons: summarise, explain, fix grammar, translate.',
      'Copy some text anywhere, press a button, and the answer lands in a notification and on your clipboard.',
      'Edit a button to write your own prompt. {clipboard} inserts what you copied.',
    ],
    recommendation:
      'You do not need this for Claude Code: its buttons and the agent alerts use the Claude Code CLI and hooks, not an API key. Add a key only for the one-shot "Ask Claude (API)" buttons. API use is billed per token, so keep the default low-effort setting.',
    scene: {
      sceneKey: 'integration-claude-api',
      name: 'Ask Claude',
      icon: 'comment-dots',
      color: '#d97757',
      buttons: [
        { label: 'Summarize', icon: ['fas', 'compress'], action: { type: 'claude_api_prompt', config: { prompt: 'Summarize this in 3 short bullet points:\n\n{clipboard}', effort: 'low', output: 'both' } }, tooltip: 'Summarize the copied text' },
        { label: 'Explain', icon: ['fas', 'lightbulb'], action: { type: 'claude_api_prompt', config: { prompt: 'Explain this simply, in one short paragraph:\n\n{clipboard}', effort: 'low', output: 'both' } }, tooltip: 'Explain the copied text' },
        { label: 'Fix Grammar', icon: ['fas', 'spell-check'], action: { type: 'claude_api_prompt', config: { prompt: 'Fix the grammar and spelling. Return only the corrected text:\n\n{clipboard}', effort: 'low', output: 'clipboard' } }, tooltip: 'Correct the copied text and copy the result' },
        { label: 'Translate', icon: ['fas', 'language'], action: { type: 'claude_api_prompt', config: { prompt: 'Translate this to English. Return only the translation:\n\n{clipboard}', effort: 'low', output: 'both' } }, tooltip: 'Translate the copied text to English' },
        { label: 'Commit Msg', icon: ['fas', 'code-commit'], action: { type: 'claude_api_prompt', config: { prompt: 'Write a one-line conventional commit message for this change:\n\n{clipboard}', effort: 'low', output: 'clipboard' } }, tooltip: 'Commit message for the copied diff' },
        { label: 'Reply', icon: ['fas', 'reply'], action: { type: 'claude_api_prompt', config: { prompt: 'Draft a short, friendly reply to this message:\n\n{clipboard}', effort: 'low', output: 'both' } }, tooltip: 'Draft a reply to the copied message' },
      ],
    },
  },

  WEATHERAPI_KEY: {
    id: 'WEATHERAPI_KEY',
    title: 'Weather',
    summary: 'Weather works out of the box. A WeatherAPI key is only a backup in case the built-in service stops working.',
    setup: [
      'Nothing is required: VDock uses the free Open-Meteo service when no key is set.',
      'Backup only: if the built-in service ever stops working, click "Get a key" to create a free WeatherAPI.com account, then "Set key" and paste it. VDock then uses WeatherAPI.com instead.',
      'Press "Test" to confirm the weather service works.',
    ],
    next: [
      'Press "Add Weather scene" below to add weather buttons.',
      'Edit a button to set a city (for example "Tel Aviv"). Leave it blank for a default location.',
      'The screensaver weather widget is separate and always works without any key.',
    ],
    recommendation:
      'Skip the key unless you need WeatherAPI.com specifically. The built-in service covers current conditions for any city, and you avoid managing another account.',
    scene: {
      sceneKey: 'integration-weather',
      name: 'Weather',
      icon: 'cloud-sun',
      color: '#3498db',
      buttons: [
        { label: 'Weather °C', icon: ['fas', 'cloud-sun'], action: { type: 'weather', config: { weather_location: 'auto', refresh_interval: 15, temperature_unit: 'C' } }, tooltip: 'Current weather in °C. Edit the button to set your city.' },
        { label: 'Weather °F', icon: ['fas', 'temperature-half'], action: { type: 'weather', config: { weather_location: 'auto', refresh_interval: 15, temperature_unit: 'F' } }, tooltip: 'Current weather in °F. Edit the button to set your city.' },
      ],
    },
  },
}

export function guideFor(id: string): IntegrationGuide | undefined {
  return INTEGRATION_GUIDES[id]
}
