// System preset data — migrated out of the `createPreconfiguredButton` switch
// statement in `frontend/src/views/DashboardView.vue` (task 3.2).
// See design.md, section "1. Preset registry".
//
// NOTE on `icon.value` encoding:
// `ButtonPreset.icon` is `{ type: 'fontawesome'; value: string }`, but the source
// switch statement uses a FontAwesome tuple, e.g. `['fas', 'power-off']`. We encode
// that tuple as a single `"prefix:iconName"` string (e.g. `'fas:power-off'`) so it
// fits the `value: string` field. `presetToButton` (task 3.6) must split on `:` to
// reconstruct the `[prefix, iconName]` tuple expected by `Button.icon`.
//
// NOTE on scope: the `custom-icon` case in the original switch statement produces a
// button with no `action` (it's a placeholder for user-provided media, not a
// functional action), so it has no equivalent here — `ButtonPreset.action` is
// required. The `default` case (unmatched action ids) also has no preset equivalent.
//
// DashboardView.vue's switch statement is NOT modified by this task (still works
// unchanged) — removal happens in task 3.8 once `presetToButton` exists (task 3.6).

import type { ButtonPreset } from './types'

export const systemPresets: ButtonPreset[] = [
  {
    id: 'shutdown',
    name: 'Shutdown',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:power-off' },
    action: { type: 'cross_platform', config: { action: 'shutdown' } },
    keywords: ['power off', 'turn off']
  },
  {
    id: 'restart',
    name: 'Restart',
    category: 'system',
    brand: { primary: '#f39c12' },
    icon: { type: 'fontawesome', value: 'fas:redo' },
    action: { type: 'cross_platform', config: { action: 'restart' } },
    keywords: ['reboot']
  },
  {
    id: 'sleep',
    name: 'Sleep',
    category: 'system',
    brand: { primary: '#9b59b6' },
    icon: { type: 'fontawesome', value: 'fas:moon' },
    action: { type: 'cross_platform', config: { action: 'sleep' } },
    keywords: ['suspend']
  },
  {
    id: 'lock',
    name: 'Lock',
    category: 'system',
    brand: { primary: '#34495e' },
    icon: { type: 'fontawesome', value: 'fas:lock' },
    action: { type: 'cross_platform', config: { action: 'lock_screen' } },
    keywords: ['lock screen']
  },
  {
    id: 'fullscreen',
    name: 'Full Screen',
    category: 'system',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:expand' },
    action: { type: 'system_control', config: { action: 'fullscreen' } },
    keywords: ['maximize display']
  },
  {
    id: 'volume-up',
    name: 'Volume Up',
    category: 'system',
    brand: { primary: '#27ae60' },
    icon: { type: 'fontawesome', value: 'fas:volume-up' },
    action: { type: 'cross_platform', config: { action: 'volume_up', step: 2000 } },
    keywords: ['audio', 'louder']
  },
  {
    id: 'volume-down',
    name: 'Volume Down',
    category: 'system',
    brand: { primary: '#27ae60' },
    icon: { type: 'fontawesome', value: 'fas:volume-down' },
    action: { type: 'cross_platform', config: { action: 'volume_down', step: 2000 } },
    keywords: ['audio', 'quieter']
  },
  {
    id: 'play-pause',
    name: 'Play/Pause',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:play' },
    action: { type: 'cross_platform', config: { action: 'media_play_pause' } },
    keywords: ['media']
  },
  {
    id: 'next-track',
    name: 'Next Track',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:forward' },
    action: { type: 'cross_platform', config: { action: 'media_next' } },
    keywords: ['media', 'skip']
  },
  {
    id: 'prev-track',
    name: 'Previous Track',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:backward' },
    action: { type: 'cross_platform', config: { action: 'media_previous' } },
    keywords: ['media', 'back']
  },
  {
    id: 'stop',
    name: 'Stop',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:stop' },
    action: { type: 'cross_platform', config: { action: 'media_stop' } },
    keywords: ['media']
  },
  {
    id: 'screenshot',
    name: 'Screenshot',
    category: 'system',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:camera' },
    action: { type: 'cross_platform', config: { action: 'screenshot', path: 'screenshot.png' } },
    keywords: ['capture', 'snip']
  },
  {
    id: 'open-url',
    name: 'Open URL',
    category: 'system',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://example.com' } },
    keywords: ['website', 'link']
  },
  {
    id: 'brightness-up',
    name: 'Brightness Up',
    category: 'system',
    brand: { primary: '#f1c40f' },
    icon: { type: 'fontawesome', value: 'fas:sun' },
    action: { type: 'cross_platform', config: { action: 'brightness_up', step: 10 } },
    keywords: ['display', 'screen']
  },
  {
    id: 'brightness-down',
    name: 'Brightness Down',
    category: 'system',
    brand: { primary: '#95a5a6' },
    icon: { type: 'fontawesome', value: 'fas:moon' },
    action: { type: 'cross_platform', config: { action: 'brightness_down', step: 10 } },
    keywords: ['display', 'screen']
  },
  {
    id: 'open-app',
    name: 'Open App',
    category: 'system',
    brand: { primary: '#e67e22' },
    icon: { type: 'fontawesome', value: 'fas:rocket' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'notepad.exe' } },
    keywords: ['launch', 'program']
  },
  {
    id: 'open-folder',
    name: 'Open Folder',
    category: 'system',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:folder-open' },
    action: { type: 'cross_platform', config: { action: 'open_folder', path: 'C:\\' } },
    keywords: ['directory', 'explorer']
  },
  {
    id: 'open-file',
    name: 'Open File',
    category: 'system',
    brand: { primary: '#2c3e50' },
    icon: { type: 'fontawesome', value: 'fas:file' },
    action: {
      type: 'cross_platform',
      config: { action: 'open_file', path: 'C:\\Windows\\System32\\notepad.exe' }
    },
    keywords: ['document']
  },
  {
    id: 'metric_cpu_usage',
    name: 'CPU Usage',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:microchip' },
    action: { type: 'metric_cpu_usage', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'performance']
  },
  {
    id: 'metric_memory',
    name: 'Memory',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:memory' },
    action: { type: 'metric_memory', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'ram']
  },
  {
    id: 'metric_harddisk',
    name: 'Hard Disk',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:hdd' },
    action: { type: 'metric_harddisk', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'storage']
  },
  {
    id: 'metric_cpu_frequency',
    name: 'CPU Frequency',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:wave-square' },
    action: { type: 'metric_cpu_frequency', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'performance']
  },
  {
    id: 'metric_internet_speed',
    name: 'Internet Speed',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:network-wired' },
    action: { type: 'metric_internet_speed', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'network']
  },
  {
    id: 'metric_gpu_temperature',
    name: 'GPU Temperature',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:thermometer-half' },
    action: { type: 'metric_gpu_temperature', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'graphics']
  },
  {
    id: 'metric_gpu_frequency',
    name: 'GPU Core Frequency',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:wave-square' },
    action: { type: 'metric_gpu_frequency', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'graphics']
  },
  {
    id: 'metric_gpu_usage',
    name: 'GPU Core Usage',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:grip-vertical' },
    action: { type: 'metric_gpu_usage', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'graphics']
  },
  {
    id: 'metric_gpu_memory_freq',
    name: 'GPU Memory Frequency',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:memory' },
    action: { type: 'metric_gpu_memory_freq', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'graphics']
  },
  {
    id: 'metric_gpu_memory_usage',
    name: 'GPU Memory Usage',
    category: 'system',
    brand: { primary: '#2980b9' },
    icon: { type: 'fontawesome', value: 'fas:memory' },
    action: { type: 'metric_gpu_memory_usage', config: { refresh_interval: 10 } },
    keywords: ['monitor', 'graphics']
  },
  {
    id: 'time_world_clock',
    name: 'World Clock',
    category: 'system',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'time_world_clock', config: { timezone: 'local' } },
    keywords: ['time', 'clock']
  },
  {
    id: 'time_timer',
    name: 'Timer',
    category: 'system',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:stopwatch' },
    action: { type: 'time_timer', config: { timer_duration: 0 } },
    keywords: ['time', 'stopwatch']
  },
  {
    id: 'time_countdown',
    name: 'Countdown',
    category: 'system',
    brand: { primary: '#8e44ad' },
    icon: { type: 'fontawesome', value: 'fas:hourglass-half' },
    action: { type: 'time_countdown', config: { countdown_target: '' } },
    keywords: ['time']
  },
  {
    id: 'weather',
    name: 'Weather',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:cloud-sun' },
    action: {
      type: 'weather',
      config: { weather_location: 'auto', refresh_interval: 15, temperature_unit: 'C' }
    },
    keywords: ['forecast', 'temperature']
  },
  {
    id: 'next-page',
    name: 'Next Page',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:arrow-right' },
    action: { type: 'next_page', config: {} },
    keywords: ['navigation']
  },
  {
    id: 'previous-page',
    name: 'Previous Page',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:arrow-left' },
    action: { type: 'previous_page', config: {} },
    keywords: ['navigation']
  },
  {
    id: 'home-page',
    name: 'Home',
    category: 'system',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:home' },
    action: { type: 'home_page', config: {} },
    keywords: ['navigation']
  },
  {
    id: 'empty-recycle-bin',
    name: 'Empty Recycle Bin',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:trash-alt' },
    action: { type: 'cross_platform', config: { action: 'empty_recycle_bin' } },
    keywords: ['trash', 'delete']
  },
  {
    id: 'task-manager',
    name: 'Task Manager',
    category: 'system',
    brand: { primary: '#34495e' },
    icon: { type: 'fontawesome', value: 'fas:tasks' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'taskmgr.exe' } },
    keywords: ['processes']
  },
  {
    id: 'control-panel',
    name: 'Control Panel',
    category: 'system',
    brand: { primary: '#7f8c8d' },
    icon: { type: 'fontawesome', value: 'fas:cog' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'control.exe' } },
    keywords: ['settings']
  },
  {
    id: 'device-manager',
    name: 'Device Manager',
    category: 'system',
    brand: { primary: '#95a5a6' },
    icon: { type: 'fontawesome', value: 'fas:hard-drive' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'devmgmt.msc' } },
    keywords: ['hardware']
  },
  {
    id: 'run-command',
    name: 'Run Command',
    category: 'system',
    brand: { primary: '#2c3e50' },
    icon: { type: 'fontawesome', value: 'fas:terminal' },
    action: { type: 'cross_platform', config: { action: 'run_command', command: 'echo Hello' } },
    keywords: ['shell', 'exec']
  },
  {
    id: 'close-app',
    name: 'Close App',
    category: 'system',
    brand: { primary: '#c0392b' },
    icon: { type: 'fontawesome', value: 'fas:times-circle' },
    action: { type: 'cross_platform', config: { action: 'close_app', app_name: 'notepad.exe' } },
    keywords: ['kill', 'quit']
  },
  {
    id: 'mute',
    name: 'Mute',
    category: 'system',
    brand: { primary: '#e67e22' },
    icon: { type: 'fontawesome', value: 'fas:volume-mute' },
    action: { type: 'cross_platform', config: { action: 'volume_mute' } },
    keywords: ['audio', 'silence']
  },
  {
    id: 'microphone-mute',
    name: 'Mute Mic',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:microphone-slash' },
    action: { type: 'cross_platform', config: { action: 'microphone_mute' } },
    keywords: ['audio', 'mic']
  },
  {
    id: 'microphone-unmute',
    name: 'Unmute Mic',
    category: 'system',
    brand: { primary: '#27ae60' },
    icon: { type: 'fontawesome', value: 'fas:microphone' },
    action: { type: 'cross_platform', config: { action: 'microphone_unmute' } },
    keywords: ['audio', 'mic']
  },
  {
    id: 'launch-browser',
    name: 'Browser',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:globe' },
    action: { type: 'cross_platform', config: { action: 'open_url', url: 'https://www.google.com' } },
    keywords: ['web', 'internet']
  },
  {
    id: 'launch-file-explorer',
    name: 'File Explorer',
    category: 'system',
    brand: { primary: '#f39c12' },
    icon: { type: 'fontawesome', value: 'fas:folder' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'explorer.exe' } },
    keywords: ['files']
  },
  {
    id: 'launch-calculator',
    name: 'Calculator',
    category: 'system',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:calculator' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'calc.exe' } },
    keywords: ['math']
  },
  {
    id: 'launch-notepad',
    name: 'Notepad',
    category: 'system',
    brand: { primary: '#95a5a6' },
    icon: { type: 'fontawesome', value: 'fas:file-alt' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'notepad.exe' } },
    keywords: ['text editor']
  },
  {
    id: 'launch-cmd',
    name: 'Command Prompt',
    category: 'system',
    brand: { primary: '#2c3e50' },
    icon: { type: 'fontawesome', value: 'fas:terminal' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'cmd.exe' } },
    keywords: ['shell', 'console']
  },
  {
    id: 'launch-powershell',
    name: 'PowerShell',
    category: 'system',
    brand: { primary: '#34495e' },
    icon: { type: 'fontawesome', value: 'fas:terminal' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'powershell.exe' } },
    keywords: ['shell', 'console']
  },
  {
    id: 'launch-paint',
    name: 'Paint',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:paint-brush' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'mspaint.exe' } },
    keywords: ['draw']
  },
  {
    id: 'launch-snipping-tool',
    name: 'Snipping Tool',
    category: 'system',
    brand: { primary: '#9b59b6' },
    icon: { type: 'fontawesome', value: 'fas:cut' },
    action: { type: 'cross_platform', config: { action: 'open_app', path: 'SnippingTool.exe' } },
    keywords: ['screenshot', 'capture']
  },
  {
    id: 'minimize-window',
    name: 'Minimize',
    category: 'system',
    brand: { primary: '#95a5a6' },
    icon: { type: 'fontawesome', value: 'fas:window-minimize' },
    action: { type: 'hotkey', config: { keys: ['Win', 'Down'] } },
    keywords: ['window']
  },
  {
    id: 'maximize-window',
    name: 'Maximize',
    category: 'system',
    brand: { primary: '#16a085' },
    icon: { type: 'fontawesome', value: 'fas:window-maximize' },
    action: { type: 'hotkey', config: { keys: ['Win', 'Up'] } },
    keywords: ['window']
  },
  {
    id: 'close-window',
    name: 'Close Window',
    category: 'system',
    brand: { primary: '#e74c3c' },
    icon: { type: 'fontawesome', value: 'fas:window-close' },
    action: { type: 'hotkey', config: { keys: ['Alt', 'F4'] } },
    keywords: ['window']
  },
  {
    id: 'switch-window',
    name: 'Switch Window',
    category: 'system',
    brand: { primary: '#3498db' },
    icon: { type: 'fontawesome', value: 'fas:window-restore' },
    action: { type: 'hotkey', config: { keys: ['Alt', 'Tab'] } },
    keywords: ['window', 'alt-tab']
  },
  {
    id: 'show-desktop',
    name: 'Show Desktop',
    category: 'system',
    brand: { primary: '#7f8c8d' },
    icon: { type: 'fontawesome', value: 'fas:desktop' },
    action: { type: 'hotkey', config: { keys: ['Win', 'D'] } },
    keywords: ['window', 'minimize all']
  }
]
