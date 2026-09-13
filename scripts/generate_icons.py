"""
Generate clean, modern isometric 3D vector SVG icons for the 5 classes.
"""

from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "app" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 1. Cardboard Box SVG
box_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="boxTop" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f5c792"/>
      <stop offset="100%" stop-color="#dfa166"/>
    </linearGradient>
    <linearGradient id="boxLeft" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#d48c48"/>
      <stop offset="100%" stop-color="#ad6929"/>
    </linearGradient>
    <linearGradient id="boxRight" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#bd7733"/>
      <stop offset="100%" stop-color="#8c4e16"/>
    </linearGradient>
    <linearGradient id="tape" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#947048"/>
      <stop offset="100%" stop-color="#735432"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#shadow)">
    <!-- Top Face -->
    <polygon points="60,25 95,45 60,65 25,45" fill="url(#boxTop)"/>
    <!-- Left Face -->
    <polygon points="25,45 60,65 60,100 25,80" fill="url(#boxLeft)"/>
    <!-- Right Face -->
    <polygon points="60,65 95,45 95,80 60,100" fill="url(#boxRight)"/>
    <!-- Center Flap Crease -->
    <line x1="60" y1="25" x2="60" y2="65" stroke="#ba7f47" stroke-width="1.5"/>
    <!-- Packing Tape Strip -->
    <polygon points="56,27 64,23 64,67 56,63" fill="url(#tape)" opacity="0.85"/>
    <polygon points="56,63 64,67 64,101 56,97" fill="url(#tape)" opacity="0.85"/>
  </g>
</svg>"""

# 2. Forklift SVG
forklift_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="forkYellow" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#fcd34d"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <linearGradient id="darkMetal" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#475569"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <filter id="shadowF" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#shadowF)">
    <!-- Chassis Body -->
    <path d="M 28 65 L 75 65 L 78 52 L 60 52 L 54 40 L 32 40 L 26 50 Z" fill="url(#forkYellow)"/>
    <!-- Cabin Cage -->
    <path d="M 36 40 L 40 22 L 62 22 L 66 40" fill="none" stroke="#334155" stroke-width="4" stroke-linecap="round"/>
    <line x1="42" y1="22" x2="60" y2="22" stroke="#64748b" stroke-width="2"/>
    <!-- Front Mast (Vertical Rails) -->
    <rect x="76" y="16" width="5" height="60" fill="url(#darkMetal)" rx="1"/>
    <rect x="83" y="16" width="5" height="60" fill="url(#darkMetal)" rx="1"/>
    <line x1="75" y1="35" x2="88" y2="35" stroke="#94a3b8" stroke-width="2"/>
    <!-- Forks (Horizontal Prongs) -->
    <polygon points="80,68 108,68 108,72 80,72" fill="#94a3b8"/>
    <!-- Back Wheel -->
    <circle cx="38" cy="74" r="11" fill="#0f172a"/>
    <circle cx="38" cy="74" r="5" fill="#64748b"/>
    <!-- Front Wheel -->
    <circle cx="70" cy="74" r="11" fill="#0f172a"/>
    <circle cx="70" cy="74" r="5" fill="#64748b"/>
    <!-- Counterweight -->
    <path d="M 26 52 Q 22 62 26 70 L 32 70 L 32 52 Z" fill="#b45309"/>
    <!-- Warning Beacon -->
    <rect x="48" y="18" width="6" height="4" fill="#ef4444" rx="1"/>
  </g>
</svg>"""

# 3. Freight Container SVG
container_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="cntTop" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ef4444"/>
      <stop offset="100%" stop-color="#b91c1c"/>
    </linearGradient>
    <linearGradient id="cntSide" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#b91c1c"/>
      <stop offset="100%" stop-color="#7f1d1d"/>
    </linearGradient>
    <linearGradient id="cntFront" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#991b1b"/>
    </linearGradient>
    <filter id="shadowC" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#shadowC)">
    <!-- Isometric Container -->
    <!-- Top Roof -->
    <polygon points="45,30 105,42 75,55 15,43" fill="url(#cntTop)"/>
    <!-- Front Door Face -->
    <polygon points="15,43 75,55 75,90 15,78" fill="url(#cntFront)"/>
    <!-- Side Corrugated Wall -->
    <polygon points="75,55 105,42 105,77 75,90" fill="url(#cntSide)"/>
    <!-- Front Door Vertical Seam & Locking Rods -->
    <line x1="45" y1="49" x2="45" y2="84" stroke="#450a0a" stroke-width="2"/>
    <line x1="38" y1="47" x2="38" y2="82" stroke="#fca5a5" stroke-width="1"/>
    <line x1="52" y1="50" x2="52" y2="85" stroke="#fca5a5" stroke-width="1"/>
    <!-- Side Ribs (Corrugations) -->
    <line x1="81" y1="52" x2="81" y2="87" stroke="#450a0a" stroke-width="1.5"/>
    <line x1="87" y1="49" x2="87" y2="84" stroke="#450a0a" stroke-width="1.5"/>
    <line x1="93" y1="46" x2="93" y2="81" stroke="#450a0a" stroke-width="1.5"/>
    <line x1="99" y1="44" x2="99" y2="79" stroke="#450a0a" stroke-width="1.5"/>
    <!-- Corner Castings -->
    <circle cx="16" cy="44" r="2" fill="#fff" opacity="0.6"/>
    <circle cx="74" cy="56" r="2" fill="#fff" opacity="0.6"/>
    <circle cx="104" cy="43" r="2" fill="#fff" opacity="0.6"/>
  </g>
</svg>"""

# 4. Wood Pallet SVG
pallet_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="woodLight" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#d4a373"/>
      <stop offset="100%" stop-color="#b07d4b"/>
    </linearGradient>
    <linearGradient id="woodDark" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8a5a36"/>
      <stop offset="100%" stop-color="#5c381e"/>
    </linearGradient>
    <filter id="shadowP" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#shadowP)">
    <!-- Top Deckboards (Isometric Planks) -->
    <!-- Plank 1 -->
    <polygon points="60,40 95,54 85,58 50,44" fill="url(#woodLight)"/>
    <!-- Plank 2 -->
    <polygon points="46,45 81,59 71,63 36,49" fill="url(#woodLight)"/>
    <!-- Plank 3 -->
    <polygon points="32,50 67,64 57,68 22,54" fill="url(#woodLight)"/>
    <!-- Cross Stringer Blocks -->
    <polygon points="25,56 40,50 40,65 25,71" fill="url(#woodDark)"/>
    <polygon points="50,66 65,60 65,75 50,81" fill="url(#woodDark)"/>
    <polygon points="75,76 90,70 90,85 75,91" fill="url(#woodDark)"/>
    <!-- Bottom Skid Runner Planks -->
    <polygon points="25,71 85,95 75,98 15,74" fill="url(#woodLight)"/>
    <polygon points="35,67 95,91 85,94 25,70" fill="#9c6644"/>
  </g>
</svg>"""

# 5. Delivery Truck SVG
truck_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="100%" height="100%">
  <defs>
    <linearGradient id="truckBody" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#cbd5e1"/>
    </linearGradient>
    <linearGradient id="truckCab" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e2e8f0"/>
      <stop offset="100%" stop-color="#94a3b8"/>
    </linearGradient>
    <linearGradient id="truckGlass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <filter id="shadowT" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#shadowT)">
    <!-- Cargo Box Body -->
    <rect x="20" y="32" width="56" height="38" rx="2" fill="url(#truckBody)"/>
    <!-- Cargo Door Seam -->
    <line x1="48" y1="32" x2="48" y2="70" stroke="#94a3b8" stroke-width="1.5"/>
    <!-- Chassis Rail -->
    <rect x="18" y="70" width="84" height="6" fill="#334155"/>
    <!-- Cab -->
    <path d="M 76 44 L 88 44 L 98 56 L 98 70 L 76 70 Z" fill="url(#truckCab)"/>
    <!-- Windshield Glass -->
    <polygon points="86,47 95,57 80,57 80,47" fill="url(#truckGlass)" opacity="0.9"/>
    <!-- Front Bumper & Headlight -->
    <rect x="96" y="65" width="4" height="5" fill="#f59e0b" rx="1"/>
    <!-- Wheels -->
    <!-- Rear Duals -->
    <circle cx="32" cy="76" r="9" fill="#0f172a"/>
    <circle cx="32" cy="76" r="4" fill="#94a3b8"/>
    <circle cx="48" cy="76" r="9" fill="#0f172a"/>
    <circle cx="48" cy="76" r="4" fill="#94a3b8"/>
    <!-- Front Steer Wheel -->
    <circle cx="88" cy="76" r="9" fill="#0f172a"/>
    <circle cx="88" cy="76" r="4" fill="#94a3b8"/>
  </g>
</svg>"""

(STATIC_DIR / "box.svg").write_text(box_svg, encoding="utf-8")
(STATIC_DIR / "forklift.svg").write_text(forklift_svg, encoding="utf-8")
(STATIC_DIR / "container.svg").write_text(container_svg, encoding="utf-8")
(STATIC_DIR / "pallet.svg").write_text(pallet_svg, encoding="utf-8")
(STATIC_DIR / "truck.svg").write_text(truck_svg, encoding="utf-8")

print(f"Generated 5 isometric 3D SVGs in {STATIC_DIR}")
