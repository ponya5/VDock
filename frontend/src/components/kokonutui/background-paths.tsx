"use client"

import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { ShinyButton } from "@/components/ui/shiny-button"
import { useState, useEffect } from "react"

function FloatingPaths({ position }: { position: number }) {
  const paths = Array.from({ length: 36 }, (_, i) => ({
    id: i,
    d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${
      380 - i * 5 * position
    } -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${
      152 - i * 5 * position
    } ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${
      684 - i * 5 * position
    } ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
    color: `rgba(15,23,42,${0.1 + i * 0.03})`,
    width: 0.5 + i * 0.03,
  }))

  return (
    <div className="absolute inset-0 pointer-events-none">
      <svg className="w-full h-full text-[#808080]" viewBox="0 0 696 316" fill="none">
        <title>Background Paths</title>
        {paths.map((path) => (
          <motion.path
            key={path.id}
            d={path.d}
            stroke="currentColor"
            strokeWidth={path.width}
            strokeOpacity={0.1 + path.id * 0.03}
            initial={{ pathLength: 0.3, opacity: 0.6 }}
            animate={{
              pathLength: 1,
              opacity: [0.3, 0.6, 0.3],
              pathOffset: [0, 1, 0],
            }}
            transition={{
              duration: 20 + Math.random() * 10,
              repeat: Number.POSITIVE_INFINITY,
              ease: "linear",
            }}
          />
        ))}
      </svg>
    </div>
  )
}

export default function BackgroundPaths({
  title = "Background Paths",
}: {
  title?: string
}) {
  const router = useRouter()
  const [mouseGradientStyle, setMouseGradientStyle] = useState({
    left: "0px",
    top: "0px",
    opacity: 0,
  })
  const [ripples, setRipples] = useState([])
  const [wordsAnimated, setWordsAnimated] = useState(false)

  // Mouse tracking effect
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMouseGradientStyle({
        left: `${e.clientX}px`,
        top: `${e.clientY}px`,
        opacity: 1,
      })
    }
    const handleMouseLeave = () => {
      setMouseGradientStyle((prev) => ({ ...prev, opacity: 0 }))
    }
    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseleave", handleMouseLeave)
    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseleave", handleMouseLeave)
    }
  }, [])

  // Ripple effect on click
  useEffect(() => {
    const handleClick = (e) => {
      const newRipple = { id: Date.now(), x: e.clientX, y: e.clientY }
      setRipples((prev) => [...prev, newRipple])
      setTimeout(() => setRipples((prev) => prev.filter((r) => r.id !== newRipple.id)), 1000)
    }
    document.addEventListener("click", handleClick)
    return () => document.removeEventListener("click", handleClick)
  }, [])

  // Word animation trigger
  useEffect(() => {
    const timer = setTimeout(() => {
      setWordsAnimated(true)
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  const handleOnboardingClick = () => {
    router.push("/onboarding")
  }

  const pageStyles = `
    .mouse-gradient {
      position: fixed;
      pointer-events: none;
      border-radius: 9999px;
      background-image: radial-gradient(circle, rgba(74, 0, 224, 0.08), rgba(107, 70, 193, 0.05), transparent 70%);
      transform: translate(-50%, -50%);
      will-change: left, top, opacity;
      transition: left 70ms linear, top 70ms linear, opacity 300ms ease-out;
      z-index: 1;
    }
    
    @keyframes word-appear { 
      0% { opacity: 0; transform: translateY(30px) scale(0.8); filter: blur(10px); } 
      50% { opacity: 0.8; transform: translateY(10px) scale(0.95); filter: blur(2px); } 
      100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); } 
    }
    
    @keyframes pulse-glow { 
      0%, 100% { opacity: 0.1; transform: scale(1); } 
      50% { opacity: 0.3; transform: scale(1.1); } 
    }
    
    @keyframes float { 
      0%, 100% { transform: translateY(0) translateX(0); opacity: 0.2; } 
      25% { transform: translateY(-10px) translateX(5px); opacity: 0.6; } 
      50% { transform: translateY(-5px) translateX(-3px); opacity: 0.4; } 
      75% { transform: translateY(-15px) translateX(7px); opacity: 0.8; } 
    }
    
    .word-animate { 
      display: inline-block; 
      opacity: 0; 
      margin: 0 0.1em; 
      transition: color 0.3s ease, transform 0.3s ease; 
    }
    
    .word-animate.animate { 
      animation: word-appear 0.8s ease-out forwards; 
    }
    
    .word-animate:hover { 
      color: #a855f7; 
      transform: translateY(-2px); 
    }
    
    .floating-element { 
      position: absolute; 
      width: 3px; 
      height: 3px; 
      background: #4A00E0; 
      border-radius: 50%; 
      opacity: 0.3; 
      animation: float 4s ease-in-out infinite; 
    }
    
    .ripple-effect { 
      position: fixed; 
      width: 6px; 
      height: 6px; 
      background: rgba(74, 0, 224, 0.6); 
      border-radius: 50%; 
      transform: translate(-50%, -50%); 
      pointer-events: none; 
      animation: pulse-glow 1s ease-out forwards; 
      z-index: 9999; 
    }

    .grid-line { 
      stroke: #4A00E0; 
      stroke-width: 0.5; 
      opacity: 0; 
      stroke-dasharray: 5 5; 
      stroke-dashoffset: 1000; 
      animation: grid-draw 2s ease-out forwards; 
    }
    
    @keyframes grid-draw { 
      0% { stroke-dashoffset: 1000; opacity: 0; } 
      50% { opacity: 0.2; } 
      100% { stroke-dashoffset: 0; opacity: 0.1; } 
    }
  `

  return (
    <>
      <style>{pageStyles}</style>
      <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#F5F5F5]">
        {/* Animated Grid Background */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="boomeGrid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(74, 0, 224, 0.05)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#boomeGrid)" />
          <line x1="0" y1="20%" x2="100%" y2="20%" className="grid-line" style={{ animationDelay: "0.5s" }} />
          <line x1="0" y1="80%" x2="100%" y2="80%" className="grid-line" style={{ animationDelay: "1s" }} />
          <line x1="20%" y1="0" x2="20%" y2="100%" className="grid-line" style={{ animationDelay: "1.5s" }} />
          <line x1="80%" y1="0" x2="80%" y2="100%" className="grid-line" style={{ animationDelay: "2s" }} />
        </svg>

        {/* Floating Elements */}
        <div className="floating-element" style={{ top: "25%", left: "15%", animationDelay: "0.5s" }}></div>
        <div className="floating-element" style={{ top: "60%", left: "85%", animationDelay: "1s" }}></div>
        <div className="floating-element" style={{ top: "40%", left: "10%", animationDelay: "1.5s" }}></div>
        <div className="floating-element" style={{ top: "75%", left: "90%", animationDelay: "2s" }}></div>
        <div className="floating-element" style={{ top: "30%", left: "70%", animationDelay: "2.5s" }}></div>
        <div className="floating-element" style={{ top: "80%", left: "20%", animationDelay: "3s" }}></div>

        {/* Original Floating Paths */}
        <div className="absolute inset-0">
          <FloatingPaths position={1} />
          <FloatingPaths position={-1} />
        </div>

        <div className="relative z-10 container mx-auto px-4 md:px-6 text-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 2 }}
            className="max-w-4xl mx-auto"
          >
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 2.5, type: "spring", stiffness: 60, damping: 15 }}
              className="mb-8 flex items-center justify-center"
            >
              <img
                src="/images/boome-logo-new.png"
                alt="Boome Performance Digital"
                className="w-auto h-32 sm:h-40 md:h-48 lg:h-56 mx-auto object-contain"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 1.8 }}
              className="flex justify-center"
            >
              <ShinyButton
                onClick={handleOnboardingClick}
                className="bg-gradient-to-r from-[#4A00E0] to-[#6B46C1] hover:from-[#4A00E0]/90 hover:to-[#6B46C1]/90 
                           px-8 py-4 text-lg font-semibold rounded-2xl 
                           shadow-lg hover:shadow-xl hover:shadow-[#4A00E0]/30 
                           transition-all duration-300 hover:-translate-y-1
                           border border-white/20"
              >
                <span className="flex items-center space-x-3 text-white">
                  <span className="text-white font-semibold">Iniciar Onboarding</span>
                  <span className="text-white opacity-70 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300">
                    →
                  </span>
                </span>
              </ShinyButton>
            </motion.div>

            {/* Animated bottom text */}
            <div className="mt-12">
              <div className="mb-4 w-16 h-px bg-gradient-to-r from-transparent via-[#4A00E0] to-transparent opacity-30 mx-auto"></div>
              <h3 className="text-sm font-mono font-light text-[#4A00E0] uppercase tracking-[0.2em] opacity-80">
                <span className={`word-animate ${wordsAnimated ? "animate" : ""}`} style={{ animationDelay: "2000ms" }}>
                  Estratégia,
                </span>
                <span className={`word-animate ${wordsAnimated ? "animate" : ""}`} style={{ animationDelay: "2200ms" }}>
                  Execução,
                </span>
                <span className={`word-animate ${wordsAnimated ? "animate" : ""}`} style={{ animationDelay: "2400ms" }}>
                  Resultados
                </span>
              </h3>
            </div>
          </motion.div>
        </div>

        {/* Mouse Gradient Effect */}
        <div
          className="mouse-gradient w-96 h-96 blur-3xl"
          style={{
            left: mouseGradientStyle.left,
            top: mouseGradientStyle.top,
            opacity: mouseGradientStyle.opacity,
          }}
        ></div>

        {/* Ripple Effects */}
        {ripples.map((ripple) => (
          <div key={ripple.id} className="ripple-effect" style={{ left: `${ripple.x}px`, top: `${ripple.y}px` }}></div>
        ))}
      </div>
    </>
  )
}
