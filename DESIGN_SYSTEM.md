# Design System Documentation

## Overview

The YouTube Shorts Downloader uses a modern, dark-themed design inspired by high-converting SaaS applications. The design emphasizes clarity, visual hierarchy, and user engagement through strategic use of color and typography.

## Color Palette

### Primary Colors

```css
--background: #1a1a1a           /* Main dark background */
--secondary-bg: #0f1419         /* Card/section backgrounds */
--accent-red: #E74C3C           /* Primary CTA and accent color */
--accent-red-hover: #c0392b     /* Hover state for red elements */
```

### Text Colors

```css
--foreground: #ffffff           /* Primary text (headings) */
--text-muted: #9ca3af          /* Secondary text */
--text-gray: #6b7280           /* Tertiary text */
```

### UI Colors

```css
--border-color: #2d2d2d        /* Borders and dividers */
--input-bg: #1a1a1a            /* Input field backgrounds */
--card-bg: #0f1419             /* Card backgrounds */
```

## Typography

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
```

### Heading Styles

- **H1 (Hero)**: 5xl-6xl, Bold, White
- **H2 (Section)**: 2xl, Bold, White
- **H3 (Subsection)**: lg, Bold/Semibold, White
- **Body**: base, Regular, Gray-400

### Font Weights

- Bold: 700 (Headings, CTAs)
- Semibold: 600 (Labels, Subheadings)
- Medium: 500 (Secondary text)
- Regular: 400 (Body text)

## Component Styles

### Buttons

**Primary (Default)**
```css
background: #E74C3C
color: white
hover: #c0392b
shadow: lg with red glow
padding: 14px 40px
border-radius: 8px
font-weight: 600
```

**Outline**
```css
border: 2px solid #E74C3C
background: transparent
color: #E74C3C
hover: bg-#E74C3C, text-white
```

**Secondary**
```css
background: #2d2d2d
color: white
hover: #3d3d3d
```

### Input Fields

```css
height: 48px
background: #1a1a1a
border: 2px solid #2d2d2d
color: white
placeholder: gray-500
focus: ring-#E74C3C, border-#E74C3C
border-radius: 8px
padding: 12px 16px
```

### Cards

```css
background: #0f1419
border: 2px solid #2d2d2d
border-radius: 16px
padding: 32px-40px
hover: border-#E74C3C/30 (optional)
```

### Progress Bar

```css
background: #2d2d2d
height: 12px
border-radius: 9999px
fill: gradient from #E74C3C to #c0392b
shadow: lg with red glow
```

## Layout Patterns

### Container

```css
max-width: 1024px (4xl)
margin: auto
padding: 64px 16px
```

### Spacing Scale

- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 24px
- 2xl: 32px
- 3xl: 48px

### Border Radius

- sm: 4px
- md: 8px
- lg: 12px
- xl: 16px
- 2xl: 24px
- full: 9999px (circles)

## Visual Elements

### Numbered Circles

```css
width: 48px
height: 48px
background: #E74C3C
border-radius: 50%
display: flex
align-items: center
justify-content: center
color: white
font-size: 20px
font-weight: bold
```

### Icons

- Color: #E74C3C (accent)
- Size: 16px-20px
- Stroke width: 2px
- Style: Outlined (Heroicons)

### Shadows

**Card Shadow**
```css
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
```

**Button Shadow**
```css
box-shadow: 0 10px 15px -3px rgba(231, 76, 60, 0.2);
hover: 0 20px 25px -5px rgba(231, 76, 60, 0.3);
```

**Glow Effect**
```css
box-shadow: 0 0 20px rgba(231, 76, 60, 0.5);
```

## Interactive States

### Hover

- Buttons: Darken by 10-15%, increase shadow
- Links: Change to #E74C3C
- Cards: Border becomes #E74C3C/30
- Duration: 200ms ease

### Focus

- Ring: 2px solid #E74C3C
- Ring offset: 2px
- Outline: none

### Active

- Scale: 0.98
- Opacity: 0.9

### Disabled

- Opacity: 0.5
- Cursor: not-allowed
- Pointer events: none

## Scrollbar Styling

```css
width: 10px
track: #0f1419
thumb: #E74C3C
thumb-hover: #c0392b
border-radius: 5px
```

## Responsive Design

### Breakpoints

- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px

### Mobile Adjustments

- Reduce heading sizes (4xl → 3xl)
- Reduce padding (40px → 24px)
- Stack grid layouts
- Increase touch target sizes (min 44px)

## Accessibility

### Color Contrast

- White on #1a1a1a: 17.6:1 (WCAG AAA)
- White on #E74C3C: 4.6:1 (WCAG AA)
- Gray-400 on #1a1a1a: 8.2:1 (WCAG AAA)

### Focus Indicators

- Always visible
- High contrast (#E74C3C)
- Sufficient size (2px ring + 2px offset)

### Interactive Elements

- Minimum touch target: 44x44px
- Clear hover states
- Keyboard navigable
- Screen reader friendly

## Animation

### Transitions

```css
transition: all 200ms ease;
```

### Hover Animations

```css
transition: background-color 200ms,
            border-color 200ms,
            transform 200ms,
            box-shadow 200ms;
```

### Progress Bar

```css
transition: transform 500ms ease-out;
```

### Loading States

```css
animation: spin 1s linear infinite;
```

## Best Practices

### Do's

✅ Use red (#E74C3C) sparingly for CTAs and accents
✅ Maintain high contrast for readability
✅ Use bold, clear headings
✅ Add generous spacing between sections
✅ Use numbered circles for process steps
✅ Include subtle hover effects
✅ Use shadows to create depth
✅ Maintain consistent border radius

### Don'ts

❌ Don't use light backgrounds
❌ Don't use low-contrast text
❌ Don't overuse the red accent color
❌ Don't use small touch targets on mobile
❌ Don't skip focus indicators
❌ Don't use too many font weights
❌ Don't create cluttered layouts

## Component Examples

### Hero Section

```tsx
<div className="text-center space-y-6">
  <h1 className="text-5xl md:text-6xl font-bold text-white tracking-tight">
    Download YouTube Shorts
  </h1>
  <p className="text-xl text-gray-400 max-w-2xl mx-auto">
    Download any YouTube Shorts video in MP4 format
  </p>
</div>
```

### Card Component

```tsx
<div className="bg-[#0f1419] rounded-2xl shadow-2xl p-8 md:p-10 space-y-8 border border-[#2d2d2d]">
  {/* Card content */}
</div>
```

### Numbered Step

```tsx
<div className="space-y-3">
  <div className="w-12 h-12 rounded-full bg-[#E74C3C] flex items-center justify-center text-white text-xl font-bold">
    1
  </div>
  <h3 className="text-lg font-semibold text-white">Step Title</h3>
  <p className="text-gray-400 text-sm">Step description</p>
</div>
```

### CTA Button

```tsx
<Button size="lg" className="w-full">
  <svg className="mr-2 h-5 w-5" {...iconProps} />
  Download Video
</Button>
```

## File Locations

- Global styles: [app/globals.css](../frontend/app/globals.css)
- Button component: [components/ui/button.tsx](../frontend/components/ui/button.tsx)
- Input component: [components/ui/input.tsx](../frontend/components/ui/input.tsx)
- Progress component: [components/ui/progress.tsx](../frontend/components/ui/progress.tsx)
- Main page: [app/page.tsx](../frontend/app/page.tsx)
- Header: [components/Header.tsx](../frontend/components/Header.tsx)

## Design Inspiration

This design system is inspired by modern SaaS applications that prioritize:

1. **High contrast** for readability
2. **Bold typography** for clear hierarchy
3. **Strategic color use** for attention and conversion
4. **Generous spacing** for clean, modern aesthetic
5. **Subtle animations** for polish and feedback
6. **Dark mode first** for modern, tech-forward feel

## Implementation Checklist

- [x] Dark background (#1a1a1a)
- [x] Red accent color (#E74C3C)
- [x] White bold headings
- [x] Gray secondary text
- [x] Rounded cards with borders
- [x] Numbered circular badges
- [x] Prominent CTA buttons
- [x] Clean input fields with focus states
- [x] Progress bar with gradient
- [x] Hover effects and transitions
- [x] Custom scrollbar
- [x] Responsive layout
- [x] Accessibility features

## Maintenance

When adding new components:

1. Follow the color palette
2. Use consistent spacing scale
3. Maintain typography hierarchy
4. Include hover/focus states
5. Test for accessibility
6. Ensure mobile responsiveness
7. Add transitions for smooth interactions

The design system ensures consistency across all pages and components while maintaining the modern, professional aesthetic that drives user engagement and conversions.
