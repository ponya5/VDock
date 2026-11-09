<template>
  <!-- DL-156 / DL-163: storyboard scenes with articulated ToonHands.
       Pure function of p (springy slide-in) and t (stage rAF clock). -->
  <g :data-scene="scene" :opacity="opacity" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
    <!-- typing at the laptop (upgraded with dual articulated typing hands + screen glow) -->
    <g v-if="scene === 'typing'" :transform="`translate(${f(-(1 - u) * 130)} 0)`">
      <rect x="-22" y="130" width="136" height="14" rx="2" fill="#a85f43" stroke-width="1.6" />
      <!-- Laptop lid + illuminated screen -->
      <path d="M-8 64 L46 56 L58 116 L2 122 Z" fill="#7d7d7d" />
      <path d="M-4 68 L43 61 L53 111 L5 117 Z" fill="#14204a" stroke-width="1" opacity="0.9" />
      <!-- Animated code bars on laptop screen -->
      <path d="M4 76 L26 73" stroke="#ff6fa8" stroke-width="2.4" />
      <path :d="`M6 84 L${f(18 + Math.abs(Math.sin(t / 400)) * 22)} 81`" stroke="#6cc7ff" stroke-width="2.4" />
      <path :d="`M8 92 L${f(16 + Math.abs(Math.cos(t / 520)) * 24)} 89`" stroke="#ffd84d" stroke-width="2.4" />
      <path d="M10 100 L32 97" stroke="#ff9a4d" stroke-width="2.4" />
      <circle cx="24" cy="89" r="3.5" fill="#fff" stroke="none" opacity="0.22" />
      <!-- Laptop base + animated keys -->
      <path d="M-8 118 H72 V126 H-8 Z" fill="#9a9a9a" stroke-width="1.8" />
      <path d="M38 121 h6 M48 121 h6 M58 121 h6" stroke-width="1.5" />
      <!-- DL-165: two gloved hands, fingers fanned onto the keys -->
      <TypingGloves :t="t" />
    </g>

    <!-- typing-frenzy: high-speed furious coding with flying code sparks + vibrating mug -->
    <g v-else-if="scene === 'typing-frenzy'" :transform="`translate(${f(-(1 - u) * 130)} 0)`">
      <rect x="-22" y="130" width="244" height="14" rx="2" fill="#a85f43" stroke-width="1.6" />
      <!-- Laptop shaking slightly from intense keystrokes -->
      <g :transform="`translate(${f(Math.sin(t / 40) * 0.9)} ${f(Math.cos(t / 35) * 0.7)})`">
        <path d="M-8 62 L48 54 L60 116 L2 122 Z" fill="#5b6485" />
        <path d="M-4 66 L45 59 L55 111 L5 117 Z" fill="#0d1838" stroke-width="1.2" />
        <path :d="`M3 74 L${f(22 + Math.abs(Math.sin(t / 140)) * 22)} 71`" stroke="#ff4d4d" stroke-width="2.6" />
        <path :d="`M5 82 L${f(20 + Math.abs(Math.cos(t / 120)) * 24)} 79`" stroke="#6cc7ff" stroke-width="2.6" />
        <path :d="`M7 90 L${f(18 + Math.abs(Math.sin(t / 160 + 1)) * 26)} 87`" stroke="#ffd84d" stroke-width="2.6" />
        <path :d="`M9 98 L${f(22 + Math.abs(Math.cos(t / 130 + 2)) * 22)} 95`" stroke="#ff6fa8" stroke-width="2.6" />
        <path d="M-8 118 H76 V126 H-8 Z" fill="#9a9a9a" stroke-width="1.8" />
      </g>
      <!-- DL-165: two gloved hands, fingers fanned onto the keys -->
      <TypingGloves :t="t" fast />
      <!-- Flying keystroke sparks & code brackets -->
      <g :opacity="0.65 + 0.35 * Math.abs(Math.sin(t / 90))">
        <path :d="spark(68, 82 - ((t / 18) % 24), 0.9)" fill="#ffd84d" stroke="none" />
        <path :d="spark(88, 92 - ((t / 15 + 9) % 26), 0.75)" fill="#6cc7ff" stroke="none" />
        <path d="M72 92 L82 82 M84 96 L96 90 M64 84 L70 72" stroke="#ffd84d" stroke-width="2" />
      </g>
      <!-- Vibrating coffee mug on the right side of the desk -->
      <g :transform="`translate(${f(178 + Math.sin(t / 35) * 1.2)} ${f(116 - Math.abs(Math.sin(t / 70)) * 1.8)})`">
        <path d="M-10 -8 H10 V10 Q10 14 5 14 H-5 Q-10 14 -10 10 Z" fill="url(#rb-mug)" stroke-width="2" />
        <path d="M10 -4 Q17 -4 17 2 Q17 8 10 8" stroke-width="2.2" />
        <path :d="`M-4 -13 Q${f(-7 + Math.sin(t / 180) * 3)} -20 -3 -26 M3 -13 Q${f(6 + Math.cos(t / 180) * 3)} -20 4 -26`" stroke="#6cc7ff" stroke-width="1.8" opacity="0.8" />
      </g>
    </g>

    <!-- bored-desk: chin propped on left hand + right hand drumming fingers in a wave -->
    <g v-else-if="scene === 'bored-desk'" :transform="`translate(0 ${f((1 - u) * 100)})`">
      <rect x="-22" y="128" width="244" height="14" rx="2" fill="#a85f43" stroke-width="1.6" />
      <!-- Left arm propping up the robot's chin/cheek -->
      <g :transform="`translate(66 ${f(108 + Math.sin(t / 1000 * 2.2) * 1.5)}) rotate(-14)`">
        <path d="M-6 10 L-10 22" stroke="#fff" stroke-width="9" />
        <path d="M-6 10 L-10 22" stroke="#000" stroke-width="5" />
        <ToonHand kind="fist" :t="t" />
      </g>
      <!-- Right hand drumming fingers rhythmically on the desk -->
      <g :transform="`translate(152 120) scale(-1.12 1.12)`">
        <ToonHand kind="drum" :t="t" tap />
      </g>
      <!-- Sound ripples where fingers tap the desk -->
      <g :opacity="0.35 + 0.55 * Math.abs(Math.sin(t / 1000 * 6.5))" stroke="#6cc7ff" stroke-width="1.6">
        <path d="M126 125 Q122 121 118 125 M132 123 Q126 117 120 123" />
      </g>
      <!-- Slow ticking wall clock in top-left corner -->
      <g :transform="`translate(14 ${f(18 - (1 - u) * 50)})`">
        <circle cx="0" cy="0" r="18" fill="#000" stroke-width="2.4" />
        <circle cx="0" cy="0" r="15" stroke-width="1" opacity="0.5" />
        <path :transform="`rotate(${f((t / 1000 * 12) % 360)})`" d="M0 0 V-9" stroke-width="2.2" />
        <path :transform="`rotate(${f(Math.floor(t / 500) * 30)})`" d="M0 0 V-12" stroke="#ffd84d" stroke-width="1.6" />
      </g>
    </g>

    <!-- nodding-off: AI agent is idle -> arms folded on desk, head bobbing/nodding with Zzz -->
    <g v-else-if="scene === 'nodding-off'" :transform="`translate(0 ${f((1 - u) * 95)})`">
      <rect x="-22" y="128" width="244" height="14" rx="2" fill="#a85f43" stroke-width="1.6" />
      <!-- Folded arms pillow on the desk -->
      <g :transform="`translate(74 ${f(118 + Math.sin(t / 1000 * 2.4) * 1.2)}) rotate(8)`">
        <ToonHand kind="mitten" :t="t" />
      </g>
      <g :transform="`translate(126 ${f(120 + Math.sin(t / 1000 * 2.4 + 0.8) * 1.2)}) scale(-1 1) rotate(10)`">
        <ToonHand kind="mitten" :t="t" />
      </g>
      <!-- Rising Zzz sleep bubbles -->
      <g v-for="z in 3" :key="z"
         :transform="`translate(${f(152 + z * 11 + Math.sin(t / 600 + z) * 3)} ${f(52 - ((t / 45 + z * 16) % 48))}) scale(${f(0.55 + z * 0.22)})`"
         :opacity="f(1 - (((t / 45 + z * 16) % 48) / 48))">
        <path d="M-6 -5 H5 L-6 5 H5" stroke="#6cc7ff" stroke-width="3" />
      </g>
      <!-- Motion nod arcs beside the head -->
      <path
        :d="`M34 ${f(56 + Math.sin(t / 350) * 4)} Q28 66 34 76`"
        stroke="#ffd84d" stroke-width="1.8"
        :opacity="f(0.25 + 0.55 * Math.abs(Math.sin(t / 350)))"
      />
    </g>

    <!-- coffee-break: two articulated hands holding a warm steaming mug -->
    <g v-else-if="scene === 'coffee-break'" :transform="`translate(0 ${f((1 - u) * 100 + Math.sin(t / 1000 * 2.6) * 2)})`">
      <ellipse cx="100" cy="134" rx="34" ry="6" fill="url(#rb-metal)" stroke-width="1.8" />
      <path d="M78 96 H122 V124 Q122 134 110 134 H90 Q78 134 78 124 Z" fill="url(#rb-mug)" stroke-width="2.4" />
      <ellipse cx="100" cy="96" rx="22" ry="5" fill="#8a4f24" stroke="#fff" stroke-width="2" />
      <path d="M122 103 Q135 103 135 113 Q135 123 122 122" stroke-width="3" />
      <!-- Heart latte art / warm emblem on the mug -->
      <path d="M100 119 C92 112 94 105 98 105 C100 105 100 108 100 108 C100 108 100 105 102 105 C106 105 108 112 100 119 Z" fill="#ff6fa8" stroke="none" />
      <!-- Rising steam curls -->
      <path :d="`M92 ${f(86 - ((t / 60) % 14))} Q88 ${f(78 - ((t / 60) % 14))} 93 ${f(70 - ((t / 60) % 14))}`" stroke="#fff" stroke-width="2.2" opacity="0.75" />
      <path :d="`M106 ${f(84 - ((t / 60 + 7) % 14))} Q110 ${f(76 - ((t / 60 + 7) % 14))} 105 ${f(68 - ((t / 60 + 7) % 14))}`" stroke="#6cc7ff" stroke-width="2" opacity="0.7" />
      <!-- Left and right hands cradling the mug -->
      <g transform="translate(68 115) rotate(12) scale(0.95)"><ToonHand kind="fist" :t="t" /></g>
      <g transform="translate(134 115) scale(-0.95 0.95) rotate(12)"><ToonHand kind="fist" :t="t" /></g>
    </g>

    <!-- facepalm: articulated open hand covering the face in exasperation -->
    <g v-else-if="scene === 'facepalm'" :transform="`translate(${f(-(1 - u) * 90 + Math.sin(t / 1000 * 5) * 1.5)} ${f((1 - u) * 70)})`">
      <g :transform="`translate(94 ${f(86 + Math.sin(t / 1000 * 3.5) * 2)}) rotate(-10) scale(1.32)`">
        <ToonHand kind="facepalm" :t="t" />
      </g>
      <!-- Exasperated stress/sigh ticks -->
      <path d="M148 34 L158 26 M154 46 L166 44 M146 22 L152 12" stroke="#ff9a4d" stroke-width="2.4" :opacity="0.45 + 0.55 * Math.abs(Math.sin(t / 180))" />
    </g>

    <!-- thumbs-up: big articulated cartoon thumb-up with celebratory radial lines -->
    <g v-else-if="scene === 'thumbs-up'" :transform="`translate(${f((1 - u) * 100)} ${f((1 - u) * 70)})`">
      <g :transform="`translate(168 ${f(98 - Math.abs(Math.sin(t / 1000 * 6)) * 6)}) scale(1.3) rotate(${f(-8 + Math.sin(t / 1000 * 6) * 5)})`">
        <ToonHand kind="thumbsup" :t="t" />
      </g>
      <path v-for="(s, i) in SPARKS" :key="i" :d="spark(s[0], s[1], s[2] * (0.75 + 0.25 * Math.sin(t / 1000 * 7 + i * 1.8)))" fill="#ffd84d" stroke="none" />
      <path d="M148 56 L140 46 M168 48 L170 36 M186 56 L196 48" stroke="#ffd84d" stroke-width="2.4" :opacity="0.5 + 0.5 * Math.abs(Math.sin(t / 160))" />
    </g>

    <!-- stretch: both articulated arms stretching high overhead -->
    <g v-else-if="scene === 'stretch'">
      <g :transform="`translate(${f(28 - (1 - u) * 60)} ${f(44 - Math.abs(Math.sin(t / 1000 * 3.5)) * 10)}) scale(1.18) rotate(-22)`">
        <ToonHand kind="stretch" :t="t" :phase="0" />
      </g>
      <g :transform="`translate(${f(172 + (1 - u) * 60)} ${f(44 - Math.abs(Math.sin(t / 1000 * 3.5 + 0.4)) * 10)}) scale(-1.18 1.18) rotate(-22)`">
        <ToonHand kind="stretch" :t="t" :phase="1.2" />
      </g>
      <path d="M12 18 Q22 6 36 12 M188 18 Q178 6 164 12" stroke="#6cc7ff" stroke-width="2" :opacity="0.45 + 0.55 * Math.abs(Math.sin(t / 240))" />
    </g>

    <!-- jamming: upgraded music scene keeping original eyes+mouth clear, with headphone soundwaves, floating notes, articulated grooving hands & live spectrum -->
    <g v-else-if="scene === 'jamming'">
      <!-- Radial soundwaves pulsing out from left & right headphones -->
      <g fill="none" stroke-linecap="round">
        <path :d="`M14 48 Q${f(4 - Math.abs(Math.sin(t / 180)) * 5)} 62 14 76`" stroke="#6cc7ff" stroke-width="2.4" :opacity="f(0.45 + 0.5 * Math.abs(Math.sin(t / 180)))" />
        <path :d="`M4 42 Q${f(-8 - Math.abs(Math.cos(t / 180)) * 6)} 62 4 82`" stroke="#ff6fa8" stroke-width="2" :opacity="f(0.3 + 0.5 * Math.abs(Math.cos(t / 180)))" />
        <path :d="`M186 48 Q${f(196 + Math.abs(Math.sin(t / 180)) * 5)} 62 186 76`" stroke="#ff6fa8" stroke-width="2.4" :opacity="f(0.45 + 0.5 * Math.abs(Math.sin(t / 180)))" />
        <path :d="`M196 42 Q${f(208 + Math.abs(Math.cos(t / 180)) * 6)} 62 196 82`" stroke="#6cc7ff" stroke-width="2" :opacity="f(0.3 + 0.5 * Math.abs(Math.cos(t / 180)))" />
      </g>
      <!-- Floating neon musical notes drifting upward around the sides -->
      <g v-for="n in 4" :key="`note-${n}`"
         :transform="`translate(${f(n % 2 === 1 ? 16 + n * 5 : 162 + n * 5)} ${f(36 - ((t / 38 + n * 14) % 44))}) rotate(${f(Math.sin(t / 300 + n) * 14)})`"
         :opacity="f(1 - (((t / 38 + n * 14) % 44) / 44))">
        <path d="M-4 6 V-6 L6 -8 V4" :stroke="n % 2 === 0 ? '#6cc7ff' : '#ff6fa8'" stroke-width="2.4" />
        <ellipse cx="-6" cy="6" rx="3.2" ry="2.4" :fill="n % 2 === 0 ? '#6cc7ff' : '#ff6fa8'" stroke="none" />
        <ellipse cx="4" cy="4" rx="3.2" ry="2.4" :fill="n % 2 === 0 ? '#6cc7ff' : '#ff6fa8'" stroke="none" />
      </g>
      <!-- Left articulated hand grooving with peace sign -->
      <g :transform="`translate(${f(22 - (1 - u) * 70)} ${f(108 - Math.abs(Math.sin(t / 1000 * 8)) * 9)}) scale(1.12) rotate(${f(-16 + Math.sin(t / 1000 * 8) * 12)})`">
        <ToonHand kind="peace" :t="t" :phase="0" />
      </g>
      <!-- Right articulated hand rocking out / spinning on mini deck -->
      <g :transform="`translate(${f(178 + (1 - u) * 70)} ${f(108 - Math.abs(Math.cos(t / 1000 * 8)) * 9)}) scale(-1.12 1.12) rotate(${f(-16 + Math.cos(t / 1000 * 8) * 12)})`">
        <ToonHand kind="peace" :t="t" :phase="1.5" />
      </g>
      <!-- Sleek curved 9-band audio spectrum visualizer below the mouth -->
      <g transform="translate(0 4)">
        <rect
          v-for="b in 9" :key="b"
          :x="55 + b * 9"
          :y="f(138 - (6 + 18 * amp * Math.abs(Math.sin(t / 130 + b * 0.75))))"
          width="5.2"
          :height="f(6 + 18 * amp * Math.abs(Math.sin(t / 130 + b * 0.75)))"
          rx="2.6"
          :fill="b % 3 === 0 ? '#ffd84d' : b % 2 === 0 ? '#6cc7ff' : '#ff6fa8'"
          stroke="none"
        />
      </g>
    </g>

    <!-- texting (DL-164): WhatsApp-style chat on a phone — incoming bubble with bouncing "typing…" dots,
         then the robot's own green reply typing out, thumbs tapping the screen -->
    <g v-else-if="scene === 'texting'" :transform="`translate(${f((1 - u) * 90)} 0)`">
      <g transform="rotate(7 158 84)">
        <rect x="128" y="22" width="60" height="116" rx="9" fill="#10151d" stroke-width="2.4" />
        <rect x="132" y="30" width="52" height="100" rx="4" fill="#0b141a" stroke-width="1" opacity="0.95" />
        <!-- chat header -->
        <rect x="132" y="30" width="52" height="11" rx="3" fill="#075e54" stroke="none" />
        <circle cx="139" cy="35.5" r="3" fill="#cfd8dc" stroke="none" />
        <path d="M145 34 h14 M145 37.5 h9" stroke="#e6f2f0" stroke-width="1.4" />
        <!-- earlier messages -->
        <rect x="136" y="46" width="24" height="9" rx="3.5" fill="#202c33" stroke="none" />
        <path d="M139 50.5 h14" stroke="#8696a0" stroke-width="1.3" />
        <rect x="150" y="59" width="30" height="9" rx="3.5" fill="#005c4b" stroke="none" />
        <path d="M153 63.5 h18" stroke="#d9fdd3" stroke-width="1.3" />
        <!-- incoming "typing" bubble with bouncing dots (first half of each 4.2 s loop) -->
        <g :opacity="(t % 4200) < 2100 ? 1 : 0">
          <rect x="136" y="73" width="26" height="11" rx="5" fill="#202c33" stroke="none" />
          <circle v-for="i in 3" :key="`td-${i}`" :cx="142 + (i - 1) * 6" :cy="f(78.5 - 2.6 * Math.max(0, Math.sin(t / 170 - i * 0.9)))" r="1.7" fill="#8696a0" stroke="none" />
        </g>
        <!-- the robot's reply grows as it is typed, then sends (second half) -->
        <g :opacity="(t % 4200) >= 2100 ? 1 : 0">
          <rect :x="f(180 - (10 + 24 * Math.min(1, ((t % 4200) - 2100) / 1500)))" y="73" :width="f(10 + 24 * Math.min(1, ((t % 4200) - 2100) / 1500))" height="10" rx="4" fill="#005c4b" stroke="none" />
          <path :d="`M${f(184 - (10 + 24 * Math.min(1, ((t % 4200) - 2100) / 1500)) + 6)} 78 h${f(4 + 18 * Math.min(1, ((t % 4200) - 2100) / 1500))}`" stroke="#d9fdd3" stroke-width="1.3" />
          <path v-if="(t % 4200) > 3700" d="M170 80 l2 2 l4 -4 M173 80 l2 2 l4 -4" stroke="#53bdeb" stroke-width="1.1" />
        </g>
        <!-- input bar -->
        <rect x="135" y="118" width="46" height="9" rx="4.5" fill="#202c33" stroke="none" />
        <path :d="`M139 122.5 h${f(4 + 22 * Math.abs(Math.sin(t / 700)))}`" stroke="#8696a0" stroke-width="1.3" />
        <circle cx="176" cy="122.5" r="3.2" fill="#00a884" stroke="none" />
      </g>
      <!-- thumbs tapping the keyboard area -->
      <g :transform="`translate(${f(150 + Math.sin(t / 150) * 2)} ${f(134 + Math.abs(Math.sin(t / 110)) * -2.5)}) scale(0.82)`">
        <ToonHand kind="typing" :t="t" :phase="0" tap />
      </g>
      <g :transform="`translate(${f(172 + Math.cos(t / 140) * 2)} ${f(136 + Math.abs(Math.cos(t / 100)) * -2.5)}) scale(-0.82 0.82)`">
        <ToonHand kind="typing" :t="t" :phase="2.2" tap />
      </g>
    </g>

    <!-- dj (DL-164): the robot spins a deck — vinyl rotates, hand scratches, EQ bars + sound rings -->
    <g v-else-if="scene === 'dj'" :transform="`translate(0 ${f((1 - u) * 50)})`">
      <rect x="22" y="120" width="156" height="24" rx="5" fill="#23262e" stroke-width="2" />
      <!-- left platter -->
      <ellipse cx="62" cy="128" rx="29" ry="8.5" fill="#0f1116" />
      <ellipse cx="62" cy="128" rx="19" ry="5.4" stroke="#6cc7ff" stroke-width="1.2" :opacity="0.7" />
      <circle :cx="f(62 + Math.cos(t / 260) * 15)" :cy="f(128 + Math.sin(t / 260) * 4.2)" r="2.2" fill="#ff6fa8" stroke="none" />
      <circle cx="62" cy="128" r="2.4" fill="#fff" stroke="none" />
      <!-- right platter (turns the other way) -->
      <ellipse cx="138" cy="128" rx="29" ry="8.5" fill="#0f1116" />
      <ellipse cx="138" cy="128" rx="19" ry="5.4" stroke="#ff6fa8" stroke-width="1.2" :opacity="0.7" />
      <circle :cx="f(138 + Math.cos(-t / 300) * 15)" :cy="f(128 + Math.sin(-t / 300) * 4.2)" r="2.2" fill="#6cc7ff" stroke="none" />
      <circle cx="138" cy="128" r="2.4" fill="#fff" stroke="none" />
      <!-- mixer + crossfader -->
      <rect x="88" y="122" width="24" height="18" rx="3" fill="#323644" stroke-width="1.4" />
      <path d="M92 134 h16" stroke="#9aa0b4" stroke-width="1.4" />
      <rect :x="f(97 + Math.sin(t / 380) * 6)" y="131.5" width="6" height="5" rx="1.5" fill="#ffd84d" stroke="none" />
      <circle cx="94" cy="126.5" r="1.8" fill="#6cc7ff" stroke="none" />
      <circle cx="106" cy="126.5" r="1.8" fill="#ff6fa8" stroke="none" />
      <!-- scratching hand on the left platter, free hand on the fader -->
      <g :transform="`translate(${f(62 + Math.sin(t / 130) * 12)} ${f(112 + Math.abs(Math.sin(t / 130)) * 1.5)}) scale(0.92)`">
        <ToonHand kind="drum" :t="t" :phase="0" />
      </g>
      <g :transform="`translate(${f(144 + Math.sin(t / 380) * 5)} 110) scale(-0.9 0.9)`">
        <ToonHand kind="peace" :t="t" :phase="0.8" />
      </g>
      <!-- EQ bars flanking the face + sound rings -->
      <g stroke="none">
        <rect v-for="b in 5" :key="`dl-${b}`" :x="14 + b * 6" :y="f(96 - (5 + 24 * amp * Math.abs(Math.sin(t / 120 + b))))" width="4" :height="f(5 + 24 * amp * Math.abs(Math.sin(t / 120 + b)))" rx="2" :fill="b % 2 ? '#6cc7ff' : '#ffd84d'" />
        <rect v-for="b in 5" :key="`dr-${b}`" :x="150 + b * 6" :y="f(96 - (5 + 24 * amp * Math.abs(Math.cos(t / 120 + b))))" width="4" :height="f(5 + 24 * amp * Math.abs(Math.cos(t / 120 + b)))" rx="2" :fill="b % 2 ? '#ff6fa8' : '#6cc7ff'" />
      </g>
      <path :d="`M100 20 m-${f(10 + ((t / 30) % 26))} 0 a${f(10 + ((t / 30) % 26))} ${f(10 + ((t / 30) % 26))} 0 0 1 ${f(2 * (10 + ((t / 30) % 26)))} 0`" stroke="#ffd84d" stroke-width="1.8" :opacity="f(1 - ((t / 30) % 26) / 26)" />
    </g>

    <!-- karaoke (DL-164): hand-held mic, bouncing notes and a lyric bar that fills as it is sung -->
    <g v-else-if="scene === 'karaoke'" :transform="`translate(${f((1 - u) * 80)} 0)`">
      <g :transform="`rotate(${f(-18 + Math.sin(t / 420) * 4)} 150 96)`">
        <path d="M150 96 L160 140" stroke="#cfd3dc" stroke-width="6" />
        <path d="M150 96 L160 140" stroke="#2b2f3a" stroke-width="2.4" />
        <circle cx="147" cy="82" r="11" fill="#9aa0b4" />
        <path d="M138 80 h18 M139 85 h16 M147 71 v22" stroke="#4a5062" stroke-width="1.2" />
      </g>
      <g :transform="`translate(${f(158 + Math.sin(t / 420) * 1.5)} 128) scale(-1.0 1.0)`">
        <ToonHand kind="fist" :t="t" :phase="0" />
      </g>
      <!-- notes pouring out towards the audience -->
      <g v-for="n in 4" :key="`kn-${n}`"
         :transform="`translate(${f(120 + ((t / 24 + n * 18) % 70))} ${f(70 - ((t / 40 + n * 12) % 46) + Math.sin(t / 260 + n) * 4)})`"
         :opacity="f(1 - ((t / 24 + n * 18) % 70) / 70)">
        <path d="M-4 6 V-6 L6 -8 V4" :stroke="n % 2 ? '#ff6fa8' : '#6cc7ff'" stroke-width="2.2" />
        <ellipse cx="-6" cy="6" rx="3" ry="2.3" :fill="n % 2 ? '#ff6fa8' : '#6cc7ff'" stroke="none" />
        <ellipse cx="4" cy="4" rx="3" ry="2.3" :fill="n % 2 ? '#ff6fa8' : '#6cc7ff'" stroke="none" />
      </g>
      <!-- karaoke lyric bar -->
      <rect x="30" y="144" width="140" height="9" rx="4.5" stroke-width="1.6" />
      <rect x="30" y="144" :width="f(6 + 134 * (((t / 4400) % 1)))" height="9" rx="4.5" fill="#ffd84d" stroke="none" opacity="0.9" />
      <path d="M38 148.5 h14 M58 148.5 h22 M86 148.5 h12 M104 148.5 h26 M136 148.5 h20" stroke="#14204a" stroke-width="1.6" />
    </g>

    <!-- reading (DL-164): nose in a book, pages turning, eyes sweeping the lines -->
    <g v-else-if="scene === 'reading'" :transform="`translate(0 ${f((1 - u) * 60)})`">
      <!-- open book -->
      <path d="M100 138 Q70 126 26 132 L26 98 Q70 92 100 104 Z" fill="#f4efe0" stroke-width="2" />
      <path d="M100 138 Q130 126 174 132 L174 98 Q130 92 100 104 Z" fill="#ece5d0" stroke-width="2" />
      <path d="M34 108 Q60 104 92 112 M34 115 Q60 111 92 119 M34 122 Q60 118 92 126" stroke="#8a7f66" stroke-width="1.2" />
      <path d="M108 112 Q140 104 166 108 M108 119 Q140 111 166 115 M108 126 Q140 118 166 122" stroke="#8a7f66" stroke-width="1.2" />
      <!-- page turning every 2.6 s -->
      <path v-if="(t % 2600) < 700"
            :d="`M100 138 L100 104 Q${f(100 + 52 * Math.cos(((t % 2600) / 700) * Math.PI))} ${f(92 - 6 * Math.sin(((t % 2600) / 700) * Math.PI))} ${f(100 + 74 * Math.cos(((t % 2600) / 700) * Math.PI))} 98 L${f(100 + 74 * Math.cos(((t % 2600) / 700) * Math.PI))} 132 Q${f(100 + 52 * Math.cos(((t % 2600) / 700) * Math.PI))} 126 100 138 Z`"
            fill="#fffbee" stroke-width="1.6" />
      <!-- hands steadying the book -->
      <g transform="translate(22 124) rotate(-12)"><ToonHand kind="mitten" :t="t" :phase="0" /></g>
      <g transform="translate(178 124) scale(-1 1) rotate(-12)"><ToonHand kind="mitten" :t="t" :phase="1" /></g>
      <!-- tiny floating "idea" sparkles when a good line lands -->
      <path :d="spark(160, 70 - ((t / 50) % 16), 0.8)" fill="#ffd84d" stroke="none" :opacity="(t % 2600) < 700 ? 1 : 0.25" />
    </g>

    <!-- weather-rain: robot buddy under a rain cloud holding an umbrella -->
    <g v-else-if="scene === 'weather-rain'" :transform="`translate(0 ${f(-(1 - u) * 80)})`">
      <!-- Fluffy dark rain clouds at the top -->
      <g :transform="`translate(${f(Math.sin(t / 1000 * 1.4) * 4)} 0)`">
        <path d="M36 6 a14 14 0 0 1 24 -8 a18 18 0 0 1 34 2 a14 14 0 0 1 12 22 H36 a12 12 0 0 1 0 -16 Z" fill="#4a516e" stroke="#fff" stroke-width="2.2" />
        <path d="M108 10 a12 12 0 0 1 20 -6 a15 15 0 0 1 28 2 a12 12 0 0 1 8 18 H108 a10 10 0 0 1 0 -14 Z" fill="#262b40" stroke="#fff" stroke-width="2" />
      </g>
      <!-- Animated diagonal raindrops -->
      <g stroke="#6cc7ff" stroke-width="2" opacity="0.85">
        <line
          v-for="r in 8" :key="`drop-${r}`"
          :x1="f(18 + r * 21 - ((t / 14 + r * 13) % 28) * 0.35)"
          :y1="f(22 + ((t / 9 + r * 19) % 104))"
          :x2="f(15 + r * 21 - ((t / 14 + r * 13) % 28) * 0.35)"
          :y2="f(31 + ((t / 9 + r * 19) % 104))"
        />
      </g>
      <!-- Puddle ripples at the bottom -->
      <ellipse cx="52" cy="136" :rx="f(6 + ((t / 60) % 12))" :ry="f(1.5 + ((t / 60) % 12) * 0.2)" stroke="#6cc7ff" stroke-width="1.4" :opacity="f(1 - (((t / 60) % 12) / 12))" />
      <ellipse cx="144" cy="138" :rx="f(5 + (((t / 60) + 6) % 12))" :ry="f(1.4 + (((t / 60) + 6) % 12) * 0.2)" stroke="#6cc7ff" stroke-width="1.4" :opacity="f(1 - ((((t / 60) + 6) % 12) / 12))" />
      <!-- Articulated hand holding a tilted colorful umbrella over the robot's head (shaft to the right so face is clear) -->
      <g :transform="`translate(${f(146 + Math.sin(t / 1000 * 2.2) * 2.5)} ${f(14 + Math.cos(t / 1000 * 2.2) * 1.5)}) rotate(${f(6 + Math.sin(t / 1000 * 2.2) * 2.5)})`">
        <!-- Umbrella shaft + J-handle on the right side -->
        <path d="M8 6 L18 86 Q19 96 9 95" stroke="#ffd84d" stroke-width="3.4" />
        <!-- Wide umbrella canopy sheltering the robot face -->
        <path d="M-98 10 Q-94 -30 -36 -32 Q22 -30 26 10 Q6 1 -14 10 Q-36 1 -58 10 Q-78 1 -98 10 Z" fill="url(#rb-heart)" stroke="#fff" stroke-width="2.4" />
        <path d="M-58 10 Q-36 1 -14 10 Q-22 -16 -36 -32 Q-50 -16 -58 10 Z" fill="url(#rb-glass)" stroke="#fff" stroke-width="2" />
        <circle cx="-36" cy="-34" r="3" fill="#ffd84d" stroke="none" />
        <!-- Hand gripping umbrella handle at right edge -->
        <g transform="translate(20 76) scale(-0.92 0.92)"><ToonHand kind="fist" :t="t" /></g>
      </g>
    </g>

    <!-- weather-snow: falling snow crystals, frost breath & cozy hands warming up -->
    <g v-else-if="scene === 'weather-snow'" :transform="`translate(0 ${f((1 - u) * 70)})`">
      <!-- Drifting snowflakes across the stage -->
      <g v-for="fl in 7" :key="`snow-${fl}`"
         :transform="`translate(${f(14 + fl * 25 + Math.sin(t / 500 + fl) * 8)} ${f(-10 + ((t / 24 + fl * 23) % 145))}) rotate(${f((t / 20 + fl * 45) % 360)})`"
         stroke="#6cc7ff" stroke-width="1.8">
        <path d="M0 -5 V5 M-4.5 -2.5 L4.5 2.5 M-4.5 2.5 L4.5 -2.5" />
        <circle cx="0" cy="0" r="1.4" fill="#fff" stroke="none" />
      </g>
      <!-- Chilly frost breath puff beside the mouth -->
      <g :transform="`translate(${f(132 + ((t / 55) % 18))} ${f(92 - ((t / 80) % 12))}) scale(${f(0.6 + ((t / 55) % 18) / 28)})`"
         :opacity="f(0.75 * (1 - ((t / 55) % 18) / 18))" fill="url(#rb-ice)" stroke="none">
        <circle cx="0" cy="0" r="6" /><circle cx="7" cy="-2" r="4.5" /><circle cx="4" cy="4" r="4" />
      </g>
      <!-- Hands rubbing together at the sides to stay warm (keeping scarf & mouth visible) -->
      <g :transform="`translate(${f(34 + Math.sin(t / 95) * 3)} ${f(114 + Math.cos(t / 95) * 2.5)}) rotate(-16) scale(0.95)`">
        <ToonHand kind="mitten" :t="t" />
      </g>
      <g :transform="`translate(${f(166 - Math.sin(t / 95) * 3)} ${f(114 - Math.cos(t / 95) * 2.5)}) scale(-0.95 0.95) rotate(-16)`">
        <ToonHand kind="mitten" :t="t" />
      </g>
    </g>

    <!-- weather-sunny: radiant rotating sun in sky + cool hand waving/chilling -->
    <g v-else-if="scene === 'weather-sunny'" :transform="`translate(0 ${f(-(1 - u) * 70)})`">
      <g transform="translate(174 16)">
        <circle cx="0" cy="0" r="22" fill="#ffd84d" stroke="none" opacity="0.22" />
        <g :transform="`rotate(${f((t / 40) % 360)})`" stroke="#ffd84d" stroke-width="3">
          <path d="M0 -24 V-18 M0 18 V24 M-24 0 H-18 M18 0 H24 M-17 -17 L-13 -13 M13 13 L17 17 M-17 17 L-13 13 M13 -13 L17 -17" />
        </g>
        <circle cx="0" cy="0" r="13" fill="url(#rb-sun)" stroke="#fff" stroke-width="2" />
      </g>
      <g :transform="`translate(166 ${f(116 + (1 - u) * 60)})`">
        <g :transform="`rotate(${f(Math.sin(t / 1000 * 6) * 12)} 0 12) scale(1.15)`"><ToonHand kind="peace" :t="t" /></g>
      </g>
    </g>

    <!-- heavy-load: machine working hard (CPU/GPU high) -> lifting heavy bending barbell + cooling fan -->
    <g v-else-if="scene === 'heavy-load'" :transform="`translate(0 ${f((1 - u) * 95)})`">
      <!-- Spinning cooling fan in top-left corner -->
      <g transform="translate(18 18)">
        <circle cx="0" cy="0" r="16" fill="#262b40" stroke="#6cc7ff" stroke-width="2" />
        <g :transform="`rotate(${f((t / 2.2) % 360)})`" fill="#6cc7ff" stroke="none">
          <ellipse cx="0" cy="-7" rx="3.5" ry="6" transform="rotate(20 0 -7)" />
          <ellipse cx="7" cy="0" rx="6" ry="3.5" transform="rotate(20 7 0)" />
          <ellipse cx="0" cy="7" rx="3.5" ry="6" transform="rotate(20 0 7)" />
          <ellipse cx="-7" cy="0" rx="6" ry="3.5" transform="rotate(20 -7 0)" />
        </g>
        <circle cx="0" cy="0" r="3" fill="#fff" stroke="none" />
      </g>
      <!-- Rising heat shimmer waves -->
      <path :d="`M172 ${f(38 - ((t / 45) % 16))} Q168 ${f(30 - ((t / 45) % 16))} 174 ${f(22 - ((t / 45) % 16))}`" stroke="#ff4d4d" stroke-width="2.2" opacity="0.8" />
      <path :d="`M184 ${f(44 - ((t / 45 + 8) % 16))} Q188 ${f(36 - ((t / 45 + 8) % 16))} 182 ${f(28 - ((t / 45 + 8) % 16))}`" stroke="#ff9a4d" stroke-width="2.2" opacity="0.8" />
      <!-- Bending barbell + heavy CPU/GPU weight plates -->
      <g :transform="`translate(${f(Math.sin(t / 45) * 1.4)} ${f(118 - Math.abs(Math.sin(t / 1000 * 3.2)) * 10)})`">
        <!-- Bent steel bar -->
        <path d="M8 8 Q100 -6 192 8" stroke="url(#rb-metal)" stroke-width="4.5" />
        <!-- Left weight plates -->
        <rect x="4" y="-12" width="11" height="38" rx="3" fill="url(#rb-metal-dark)" stroke="#fff" stroke-width="2" />
        <rect x="17" y="-8" width="8" height="30" rx="2.5" fill="url(#rb-red)" stroke="#fff" stroke-width="1.8" />
        <!-- Right weight plates -->
        <rect x="185" y="-12" width="11" height="38" rx="3" fill="url(#rb-metal-dark)" stroke="#fff" stroke-width="2" />
        <rect x="175" y="-8" width="8" height="30" rx="2.5" fill="url(#rb-red)" stroke="#fff" stroke-width="1.8" />
        <!-- Both articulated fists gripping and straining under the bar -->
        <g transform="translate(54 4) scale(1.05)"><ToonHand kind="fist" :t="t" /></g>
        <g transform="translate(146 4) scale(-1.05 1.05)"><ToonHand kind="fist" :t="t" /></g>
      </g>
    </g>

    <!-- brain-overload: high memory/RAM usage -> hands clutching head + spinning gears + RAM meter -->
    <g v-else-if="scene === 'brain-overload'" :transform="`translate(0 ${f((1 - u) * 80)})`">
      <!-- High RAM usage gauge bar + spinning gears above the head -->
      <g transform="translate(100 -12)">
        <rect x="-42" y="-8" width="84" height="12" rx="6" fill="#262b40" stroke="#fff" stroke-width="2" />
        <rect x="-39" y="-5" :width="f(64 + Math.sin(t / 180) * 12)" height="6" rx="3" fill="url(#rb-red)" stroke="none" />
      </g>
      <!-- Spinning cog/sparkle bursts on both sides of head -->
      <path :d="spark(30, 12, 1.2 + 0.3 * Math.sin(t / 120))" fill="#ffd84d" stroke="none" />
      <path :d="spark(170, 12, 1.2 + 0.3 * Math.cos(t / 120))" fill="#ff4d4d" stroke="none" />
      <path d="M22 30 L10 24 M178 30 L190 24" stroke="#ff4d4d" stroke-width="2.4" :opacity="0.5 + 0.5 * Math.abs(Math.sin(t / 110))" />
      <!-- Both articulated hands clutching temples -->
      <g :transform="`translate(${f(14 + Math.sin(t / 60) * 1.5)} 76) rotate(16) scale(1.02)`">
        <ToonHand kind="facepalm" :t="t" />
      </g>
      <g :transform="`translate(${f(188 - Math.sin(t / 60) * 1.5)} 76) scale(-1.02 1.02) rotate(16)`">
        <ToonHand kind="facepalm" :t="t" />
      </g>
    </g>

    <!-- magnifier over the right eye -->
    <g v-else-if="scene === 'inspect'" :transform="`translate(${f((1 - u) * 130 + Math.sin(t / 1000 * 1.6) * 4)} ${f(Math.sin(t / 1000 * 3.2) * 1.6)})`">
      <circle cx="104" cy="56" r="29" fill="#000" stroke="none" />
      <rect x="85" :y="f(29 + magnify)" width="38" height="54" rx="17" fill="#fff" stroke="none" />
      <circle cx="104" cy="56" r="34" stroke-width="3.2" />
      <circle cx="104" cy="56" r="29.5" stroke-width="1.5" />
      <path d="M124 82 L134 116" stroke-width="8" /><path d="M124 82 L134 116" stroke="#000" stroke-width="3.6" />
      <g transform="translate(138 126)"><ToonHand kind="fist" :t="t" /></g>
      <path d="M152 34 L160 28 M156 50 L166 48" stroke-width="2" :opacity="0.5 + 0.5 * Math.sin(t / 150)" />
    </g>
    <!-- phone call, clock on the wall, laptop on the right -->
    <g v-else-if="scene === 'call'">
      <rect x="-22" y="130" width="244" height="14" fill="#a85f43" stroke-width="1.6" />
      <g :transform="`translate(0 ${f(-(1 - u) * 60)})`">
        <circle cx="8" cy="8" r="24" stroke-width="3" /><circle cx="8" cy="8" r="20.5" stroke-width="1.2" />
        <path :transform="`rotate(${f((t / 1000 * 22) % 360)} 8 8)`" d="M8 8 V-4" stroke-width="2.4" />
        <path :transform="`rotate(${f((t / 1000 * 260) % 360)} 8 8)`" d="M8 8 V-9" stroke="#ff4d4d" stroke-width="1.8" />
      </g>
      <g :transform="`translate(${f(-(1 - u) * 90)} ${f(Math.sin(t / 1000 * 6) * 1.2)})`">
        <path d="M2 74 Q-14 100 12 126" stroke-width="10" /><path d="M2 74 Q-14 100 12 126" stroke="#000" stroke-width="5.6" />
        <ellipse cx="6" cy="72" rx="9" ry="12" transform="rotate(-18 6 72)" fill="#000" /><ellipse cx="18" cy="127" rx="10" ry="8" fill="#000" />
        <g transform="translate(24 106) rotate(-12)"><ToonHand kind="fist" :t="t" /></g>
      </g>
      <g :transform="`translate(${f((1 - u) * 90)} 0)`">
        <path d="M150 120 H222 V126 H150 Z" fill="#9a9a9a" stroke-width="1.8" />
        <path d="M196 64 L222 58 V120 H186 Z" fill="#7d7d7d" />
        <g :transform="`translate(166 ${f(112 + Math.sin(t / 1000 * 13) * 1.2)})`"><ToonHand kind="typing" :t="t" tap /></g>
      </g>
    </g>
    <!-- clipboard + pen -->
    <g v-else-if="scene === 'notes'" :transform="`translate(0 ${f((1 - u) * 110)})`">
      <g transform="rotate(-8 44 118)">
        <rect x="10" y="70" width="66" height="90" rx="4" fill="#ffb768" /><rect x="14" y="76" width="58" height="80" rx="2" stroke-width="1" opacity="0.5" />
        <rect x="32" y="64" width="22" height="12" rx="4" fill="#9a9a9a" stroke-width="1.8" />
        <circle cx="26" cy="73" r="1.8" fill="#fff" stroke="none" /><circle cx="58" cy="73" r="1.8" fill="#fff" stroke="none" />
        <path d="M24 100 H62" stroke="#e8884a" stroke-width="2" stroke-dasharray="40 40" :stroke-dashoffset="f(40 - ((t / 40) % 40))" />
      </g>
      <g transform="translate(14 122)"><ToonHand kind="fist" :t="t" /></g>
      <g :transform="`translate(${f(Math.sin(t / 1000 * 14) * 2.5)} ${f(Math.cos(t / 1000 * 9.5) * 2)})`">
        <path d="M134 96 L88 86" stroke-width="9" /><path d="M134 96 L88 86" stroke="#9aa4e8" stroke-width="5" />
        <g transform="translate(138 112)"><ToonHand kind="fist" :t="t" /></g>
      </g>
    </g>
    <!-- waving hand (relax: bottom right, hello: bottom left) -->
    <g v-else-if="scene === 'relax' || scene === 'hello'" :transform="`translate(${scene === 'relax' ? 172 : 26} ${f(122 + (1 - u) * 80)})`">
      <g :transform="`rotate(${f(Math.sin(t / 1000 * 8) * 16)} 0 16) scale(${scene === 'relax' ? 1.25 : -1.25} 1.25)`"><ToonHand kind="open" :t="t" /></g>
      <path :d="scene === 'relax' ? 'M-34 -34 L-40 -42 M-26 -42 L-28 -52 M-16 -46 L-12 -54' : 'M34 -34 L40 -42 M26 -42 L28 -52 M16 -46 L12 -54'" stroke-width="2.2" :opacity="0.4 + 0.6 * Math.abs(Math.sin(t / 220))" />
    </g>
    <!-- red sneakers walking in -->
    <g v-else-if="scene === 'sneakers'" :transform="`translate(100 ${f(104 + (1 - u) * 110)}) scale(1.7)`">
      <RobotArt :def="PROPS.sneakers" :t="t" :level="0" />
    </g>
    <!-- thinking, hand on chin -->
    <g v-else-if="scene === 'chin'" :transform="`translate(${f(-(1 - u) * 90 + Math.sin(t / 1000 * 4) * 1.5)} ${f(Math.sin(t / 1000 * 4))})`">
      <g transform="translate(78 112) scale(1.3) rotate(-18)"><ToonHand kind="point" :t="t" /></g>
    </g>
    <!-- cheering fists + sparkles -->
    <g v-else-if="scene === 'cheer'">
      <g :transform="`translate(${f(28 - (1 - u) * 70)} ${f(108 - Math.abs(Math.sin(t / 1000 * 7)) * 8)}) scale(1.25) rotate(-14)`"><ToonHand kind="fist" :t="t" /></g>
      <g :transform="`translate(${f(172 + (1 - u) * 70)} ${f(108 - Math.abs(Math.sin(t / 1000 * 7 + 1)) * 8)}) scale(-1.25 1.25) rotate(-14)`"><ToonHand kind="fist" :t="t" /></g>
      <path v-for="(s, i) in SPARKS" :key="i" :d="spark(s[0], s[1], s[2] * (0.75 + 0.25 * Math.sin(t / 1000 * 6 + i * 2)))" fill="#fff" stroke="none" />
      <path d="M182 -12 L188 -22 M192 2 L202 -4" stroke-width="2.2" :opacity="0.4 + 0.6 * Math.abs(Math.sin(t / 200))" />
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import TypingGloves from './TypingGloves.vue'
import ToonHand from './ToonHand.vue'
import RobotArt from './RobotArt.vue'
import { PROPS } from '@/services/robot/robotArt'
import type { SceneId } from '@/services/robot/scenes'

const props = defineProps<{ scene: SceneId; p: number; t: number; opacity: number; level?: number }>()
const u = computed(() => Math.min(1, Math.max(0, props.p)))
const amp = computed(() => (props.level && props.level > 0 ? 0.55 + 0.75 * Math.min(1, props.level) : 1))
// the magnified eye wobbles a little as the lens sweeps
const magnify = computed(() => Math.sin(props.t / 1000 * 3) * 2)
const f = (n: number) => Math.round(n * 100) / 100

const SPARKS = [[16, 18, 1.5], [44, -6, 1.1], [190, 26, 1.4], [168, -10, 0.9]] as const
const spark = (x: number, y: number, s: number) =>
  `M${x} ${y - 8 * s} Q${x + s} ${y - s} ${x + 8 * s} ${y} Q${x + s} ${y + s} ${x} ${y + 8 * s} Q${x - s} ${y + s} ${x - 8 * s} ${y} Q${x - s} ${y - s} ${x} ${y - 8 * s} Z`
</script>
