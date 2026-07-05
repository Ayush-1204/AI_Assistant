---
name: Aether Intelligence
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#89ceff'
  on-secondary: '#00344d'
  secondary-container: '#00a2e6'
  on-secondary-container: '#00344e'
  tertiary: '#ffb783'
  on-tertiary: '#4f2500'
  tertiary-container: '#d97721'
  on-tertiary-container: '#452000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#c9e6ff'
  secondary-fixed-dim: '#89ceff'
  on-secondary-fixed: '#001e2f'
  on-secondary-fixed-variant: '#004c6e'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#ffb783'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#703700'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  code-sm:
    fontFamily: jetbrainsMono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 24px
  gutter: 16px
  sidebar-width: 280px
  inspector-width: 320px
  radius-main: 24px
  radius-inner: 16px
---

## Brand & Style

The design system is centered on a high-end, futuristic AI Assistant Dashboard. It utilizes a **Glassmorphic** design style to create a sense of depth and lightness within a deep, dark environment. The visual narrative focuses on "clarity through complexity," where the interface feels like a sophisticated lens over a vast data landscape.

**Target Audience:** Power users, developers, and creative professionals who require a high-performance, focused workspace.
**Emotional Response:** Intelligent, calm, precise, and state-of-the-art.
**Key Aesthetic Principles:**
- **Translucency:** Layers are defined by their opacity and backdrop blur rather than solid fills.
- **Precision:** Ultra-thin strokes and crisp typography balance the soft blur effects.
- **Atmospheric Depth:** The use of subtle gradients and glows to simulate an emissive digital environment.

## Colors

The palette is designed for prolonged use in dark environments, using a deep charcoal and slate base to minimize eye strain while allowing vibrant accents to pop.

- **Primary (Electric Violet/Blue):** Used for primary actions, focus states, and active AI indicators.
- **Secondary (Cyan/Sky):** Used for informational accents and secondary interactive elements.
- **Backgrounds:**
  - Base: Deep Slate (`#020617`).
  - Surface: Translucent White (`rgba(255, 255, 255, 0.03)`).
  - Overlay: Translucent White (`rgba(255, 255, 255, 0.08)`).
- **Glass Borders:** 1px solid `rgba(255, 255, 255, 0.1)`.
- **Status Colors:** Success (Emerald), Warning (Amber), Error (Rose), all using desaturated tones to fit the dark theme.

## Typography

This design system employs **Geist** for its technical, minimalist character and exceptional legibility in dark interfaces. 

- **Headlines:** Set with tight letter-spacing and high weights to command attention.
- **Body:** Standardized on 16px for optimal reading of AI-generated content.
- **Code Blocks:** Utilizes **JetBrains Mono** to distinguish technical output from conversational text, ensuring brackets and operators are easily identifiable.
- **Hierarchy:** Use color (White vs Slate-400) rather than just size to establish hierarchy.

## Layout & Spacing

The layout follows a strict **3-pane architecture** designed for productivity:

1.  **Navigation Sidebar (Left):** 280px width, fixed. Contains workspace switching and history.
2.  **Main Workspace (Center):** Fluid width. The primary area for AI interaction and content generation.
3.  **Inspector Panel (Right):** 320px width, collapsible. Contains context, metadata, and configuration tools.

**Grid System:**
- **Desktop:** 12-column grid with 24px gutters.
- **Mobile:** Single column with 16px side margins. 
- **Spacing Scale:** Based on an 8px base unit (8, 16, 24, 32, 48, 64) to maintain rhythmic consistency.

## Elevation & Depth

Depth is achieved through **Backdrop Blurs** and **Tonal Layering** rather than traditional drop shadows.

- **Level 0 (Base):** Solid deep slate.
- **Level 1 (Panels):** Backdrop blur of 16px, background `rgba(255, 255, 255, 0.02)`, 1px border `rgba(255, 255, 255, 0.05)`.
- **Level 2 (Cards/Modals):** Backdrop blur of 32px, background `rgba(255, 255, 255, 0.06)`, 1px border `rgba(255, 255, 255, 0.1)`. 
- **Active State:** A subtle outer glow using the primary color (`rgba(99, 102, 241, 0.15)`) with a 20px spread to indicate focus.

## Shapes

The design system uses a large, friendly radius to soften the technical nature of the AI.

- **Main Containers:** 24px (`rounded-xl` equivalent) for large glass panels and workspace areas.
- **Standard Components:** 12px for buttons, input fields, and small cards.
- **Small Elements:** 6px for tags, chips, and tooltips.
- **Interactive Elements:** Always maintain consistent corner ratios (inner corners should be 4-8px smaller than outer containers).

## Components

### Buttons
- **Primary:** Semi-translucent primary color with a subtle top-down gradient. 1px inner highlight on the top edge.
- **Glass (Secondary):** 1px border, backdrop blur, white text.
- **States:** On hover, increase background opacity by 5% and add a soft 10px glow of the button's accent color.

### Inputs
- **Style:** Background `rgba(0, 0, 0, 0.2)`, 1px border `rgba(255, 255, 255, 0.1)`.
- **Focus:** Border changes to primary color; add a 2px outer ring with 20% opacity of primary color.

### Glass Cards
- **Construction:** `backdrop-filter: blur(16px)`, `background: rgba(255, 255, 255, 0.03)`, `border: 1px solid rgba(255, 255, 255, 0.1)`.
- **Padding:** 24px internal padding for content-heavy cards.

### Markdown & Code Blocks
- **Code Blocks:** Deep black background (`#000000`), syntax highlighting using a vibrant neon palette (Pink, Lime, Cyan).
- **Markdown:** Use `body-md` for text; `##` headers in `headline-md`. Lists use custom primary-colored bullets.

### Skeleton Loaders
- **Animation:** A subtle pulse using a linear gradient from `rgba(255,255,255, 0.03)` to `rgba(255,255,255, 0.08)`.
- **Shape:** Match the exact border-radius of the component being loaded.

### Empty States
- **Visuals:** Use large, thin-line icons (0.5px to 1px stroke) centered in the pane with `text-slate-500`.
- **CTA:** Always provide a clear "Start New Session" or "Import Data" button in the center.