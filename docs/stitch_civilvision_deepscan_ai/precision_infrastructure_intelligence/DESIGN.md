---
name: Precision Infrastructure Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3f4850'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#707881'
  outline-variant: '#bfc7d2'
  surface-tint: '#006398'
  primary: '#006194'
  on-primary: '#ffffff'
  primary-container: '#007bb9'
  on-primary-container: '#fdfcff'
  inverse-primary: '#93ccff'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#00628d'
  on-tertiary: '#ffffff'
  tertiary-container: '#007cb1'
  on-tertiary-container: '#fcfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cce5ff'
  primary-fixed-dim: '#93ccff'
  on-primary-fixed: '#001d31'
  on-primary-fixed-variant: '#004b73'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#89ceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-hero:
    fontFamily: Space Grotesk
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: -0.03em
  display-hero-mobile:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.06em
  code-telemetry:
    fontFamily: Space Grotesk
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system blends high-precision civil engineering instrumentation with cutting-edge B2B SaaS product design. Created for structural engineers, municipal DOT inspectors, and asset managers monitoring bridges, dams, tunnels, and highways, the interface prioritizes hyper-legibility, deterministic layout structures, and high-density telemetry.

The aesthetic fuses **Modern Technical Minimalism** with **Instrument-Grade HUD interfaces**:
- **Purity & High Definition**: Crisp chalk-white canvases anchored by cool slate and blueprint-grade zinc neutrals prevent eye strain during multi-hour photogrammetry reviews.
- **Architectural Rigor**: Visual weight is distributed via 1px micro-borders, geometric hairline divisions, and strict spatial alignments rather than heavy drop shadows.
- **Actionable Diagnostic Alerts**: The visual hierarchy reserves pure saturated pigments strictly for structural diagnostics: critical shear cracks, rebar corrosion risks, and sensor anomalies stand out instantly against clinical neutrals.
- **Technical Sophistication**: Subtle backdrop blurs on navigation layers and overlay HUDs introduce spatial depth without compromising enterprise performance or legibility.

## Colors

The palette mirrors optical calibration tools, cleanroom monitors, and diagnostic displays.

### Role Mappings & Functional Logic
- **Primary Canvas (`#ffffff`) & Canvas Sub-tiers (`#f8fafc`, `#f1f5f9`)**: Creates a clean, hospital-grade backdrop. `#f8fafc` serves as the canvas substrate, `#ffffff` for elevated analytical cards, and `#f1f5f9` for docked toolbars and data grid headers.
- **Text & Foreground Gradients**: Core typography uses high-contrast Slate 900 (`#0f172a`), secondary labels rely on Slate 600 (`#475569`), and disabled/hairline states use Slate 400 (`#94a3b8`).
- **Precision Blue Accent Arc (`#0284c7`, `#0ea5e9`, `#2563eb`)**: 
  - Primary Action / Brand Core (`#0284c7`): Primary CTA buttons, active tab indicators, and primary data traces.
  - Electric Cyan (`#0ea5e9`): Interactive bounding boxes, CAD crosshairs, hover state halos, and orthomosaic mesh vertex highlights.
  - Deep Precision Blue (`#2563eb`): High-confidence AI classifications, active filters, and deep-link interactive anchors.
- **Structural Health Telemetry System**:
  - **Nominal / Intact (`#059669`)**: Structural integrity validated; zero micro-fractures detected.
  - **Moderate / Spall Warning (`#d97706`)**: Delamination or moisture ingress risk requiring 30-day reinspection.
  - **Critical Failure / Shear Crack (`#dc2626`)**: Active structural compromise, transverse fatigue cracking, or emergency load-bearing alert.
- **Surface Structural Boundaries**: Subtle borders (`#e2e8f0`) provide sharp structural separation without cluttering dense tabular data.

## Typography

Typography establishes an engineering-first hierarchy. The combination balances geometric industrial character with supreme tabular and micro-scale legibility:

- **Headlines & Metric Data (`Space Grotesk`)**: Provides an authoritative, technical cadence. Used across page titles, stat callouts, chart axes, modal titles, and CAD overlay tags. Tight tracking (`-0.02em` to `-0.03em`) creates a dense, calibrated editorial feel.
- **Narrative, Form UI & Data Logs (`Inter`)**: Deployed for body copy, inspection narrative logs, field notes, and long-form compliance records. Unmatched readability at sub-14px sizes.
- **Uppercase Engineering Labels (`label-sm`)**: Used for spatial coordinates (`LAT/LONG`, `ELEVATION`), sensor statuses, and badge headers, set with `0.06em` letter spacing to reinforce the cockpit instrumentation feel.
- **Font Pairing Rule**: Headings above 18px always use `Space Grotesk`. Dynamic coordinate readouts and vector dimensions borrow `Space Grotesk` with tabular figures (`tnum`) enabled to eliminate layout shift during real-time telemetry streaming.

## Layout & Spacing

The layout model is driven by an 8pt structural rhythm configured within a flexible 12-column engineering grid:
- **Global Layout Structure**:
  - Desktop workspaces (`>= 1280px`): Outer margins set to `margin` (`2rem`), 12-column system, `gutter` (`1.25rem`). Toolbars and side panels dock flush to viewport boundaries, reserving canvas space for high-resolution point-cloud views.
  - Split Workspace HUD: Dual-panel ratio (60% Orthomosaic View / 40% Defect Telemetry Grid) with synchronized micro-scrolling.
  - Tablet (`768px - 1279px`): 8-column layout, collapsible floating overlay for inspection metadata.
  - Mobile (`< 768px`): Single-column stack, outer canvas margin compressed to `1rem`, bottom action tray for one-handed structural defect tagging.
- **Internal Density**: 
  - Standard spacing uses `space-md` (`1rem`) between card headers and analytical graphs.
  - High-density data tables and CAD control strips compress component padding to `space-xs` (`0.25rem`) and `space-sm` (`0.5rem`) to maximize visible information per square inch.

## Elevation & Depth

Visual hierarchy emphasizes surgical surface clarity over heavy drop shadows. Depth is communicated via structured border lines, tinted tonal surfaces, and optical frosted glass:

- **Level 0 (Base Substrate)**: `#f8fafc` canvas background with an optional technical micro-dot grid (`radial-gradient(#cbd5e1 1px, transparent 1px) [size: 24px 24px]`).
- **Level 1 (Card & Module Layer)**: `#ffffff` background with a crisp border: `1px solid #e2e8f0`. Shadow is microscopic: `0 1px 2px 0 rgba(15, 23, 42, 0.04)`.
- **Level 2 (Hovered & Active Workspaces)**: `#ffffff` container with micro-lift: border transitions to `1px solid #0284c7/30`, shadow elevated to `0 4px 12px -2px rgba(2, 132, 199, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.04)`.
- **Level 3 (Diagnostic Floating Modals & HUD Toolbars)**: Frosted glass execution. Background: `rgba(255, 255, 255, 0.82)`, backdrop filter `blur(12px) saturate(180%)`, border: `1px solid rgba(226, 232, 240, 0.8)`. Outer shadow: `0 12px 28px -6px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(255, 255, 255, 0.8) inset`.
- **Level 4 (Critical Alert Popovers & Precision Overlays)**: Border highlighted in alert red (`#dc2626`) or active blue (`#0284c7`) with a localized directional glow: `box-shadow: 0 0 0 1px #0284c7, 0 8px 24px -4px rgba(2, 132, 199, 0.25)`.

## Shapes

The design system maintains a refined, architectural shape language (Level 1: Soft). 

- **Primary Geometry**: Roundedness is strictly constrained to **4px (`0.25rem`)** on inputs, buttons, and badges, expanding to **8px (`0.5rem`)** on larger telemetry containers and pricing tiers.
- **Rationale**: Overly circular surfaces diminish the instrument-grade authority of engineering platforms and consume valuable viewport pixels in dense grid views. The compact 4px radius guarantees visual precision while eliminating harsh raw corners.
- **HUD Reticles & Markers**: Photogrammetry defect pins, bounding box markers, and point-cloud vertex targets employ crisp 0px or 2px micro-radii to maintain spatial accuracy on structural surfaces.

## Components

### Buttons
- **Primary**: Background `#0284c7`, text `#ffffff`, border `1px solid #0369a1`, font `Space Grotesk` medium (`14px`), border-radius `4px`. Hover: Background `#0ea5e9` with a subtle cyan ambient bloom (`box-shadow: 0 0 12px rgba(14, 165, 233, 0.35)`). Active: `#0369a1`.
- **Secondary / Technical Outlined**: Background `#ffffff`, text `#0f172a`, border `1px solid #e2e8f0`. Hover: Border `#94a3b8`, background `#f8fafc`.
- **Destructive / Hazard Acknowledge**: Background `#dc2626`, text `#ffffff`, border `1px solid #b91c1c`. Hover: Background `#ef4444`.

### Telemetry Cards & Metric Indicators
- Built on `#ffffff` with a `1px solid #e2e8f0` frame.
- Metric headline in `Space Grotesk` bold (`28px`), paired with a top-aligned tracking label (`label-sm`) in `#64748b`.
- Incorporates a bottom hairline accent stripe color-coded to the asset's structural health index (Emerald for nominal, Amber for strain, Crimson for critical).

### Structural Health Diagnostic Badges
- **Nominal Badge**: Background `rgba(5, 150, 105, 0.08)`, text `#047857`, border `1px solid rgba(5, 150, 105, 0.25)`. Leading 6px circular pulse dot.
- **Moderate Risk Badge**: Background `rgba(217, 119, 6, 0.08)`, text `#b45309`, border `1px solid rgba(217, 119, 6, 0.25)`.
- **Critical Shear Alert**: Background `rgba(220, 38, 38, 0.08)`, text `#b91c1c`, border `1px solid rgba(220, 38, 38, 0.3)`. Rapid micro-pulse dot.

### CAD / Photogrammetry HUD Panels
- Floats over 3D point-cloud or orthomosaic raster canvases.
- Background: `rgba(255, 255, 255, 0.88)` with `backdrop-filter: blur(12px)`.
- Features coordinates readout (`LAT/LON`, `STATIONING: MP 142.8`, `CONFIDENCE: 98.4%`) in `code-telemetry` typography with Slate 500 hairline dividers.
- Action icons (Measure, Slice, Stress Gradient, AI Mask) are square 32x32px buttons with 4px border radius.

### Enterprise Data Grids
- Header row: Background `#f1f5f9`, border-bottom `1px solid #cbd5e1`, typography `Space Grotesk` 11px uppercase bold (`#475569`).
- Data rows: Alternate background between `#ffffff` and `#fafafa`. Height: 40px compact. Border bottom `1px solid #f1f5f9`. Row hover: `#f0f9ff` (Ice Blue tint) with a 2px vertical indicator bar on the left edge (`#0284c7`).

### Input Fields
- Background `#ffffff`, border `1px solid #cbd5e1`, font `Inter` 14px, height 36px, radius 4px.
- Focus: Border `#0284c7`, outline `2px solid rgba(2, 132, 199, 0.2)`.
- Prefix/Suffix integration: Monospace units (`mm`, `kN/m²`, `PSI`) anchored in a Slate 100 recessed right cap.

### Modern SaaS Tier & Pricing Cards
- Standard Tier: `#ffffff` background, `1px solid #e2e8f0`, soft hover elevation.
- Enterprise AI Tier (Featured): Highlighted with a top gradient rim (`linear-gradient(90deg, #0284c7, #0ea5e9)`), an outer cyan ambient aura, a badge reading "MISSION-CRITICAL INFRASTRUCTURE", and an electric blue primary CTA.