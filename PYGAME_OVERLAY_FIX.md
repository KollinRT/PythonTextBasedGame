# Fixing Pygame Text Overlap Issues

This document explains the specific problems causing text overlap in `ui/pygame_ui.py` and provides concrete solutions.

---

## The Problem

The current rendering code has **three critical issues**:

### Issue 1: Fixed Y-Position for the Event Log

```python
# Line 394-397 in pygame_ui.py
_render_lines(screen, font, status_lines, 20)      # Status starts at Y=20

log_header = ["Event Log:"] + log
_render_lines(screen, font, log_header, 300)       # Log ALWAYS starts at Y=300
```

**The problem:** The event log always starts at pixel Y=300, regardless of how many lines are in `status_lines`. 

**When it breaks:** During battle, `status_lines` can have 25+ lines:
- 4 base status lines
- 1 "Current turn" line  
- 4+ party member lines (with Rangers having pets)
- 3+ enemy lines
- 5+ action lines
- 9 control hint lines

At 28 pixels per line (default font), 25 lines = 700 pixels. But the log starts at Y=300, so lines 11+ of the status overlap with the log.

### Issue 2: No Maximum Line Limit

```python
# Line 16-21: _render_lines has no bounds checking
def _render_lines(screen: pygame.Surface, font: pygame.font.Font, lines: list[str], start_y: int) -> None:
    y = start_y
    for line in lines:                              # Renders ALL lines
        text = font.render(line, True, TEXT_COLOR)
        screen.blit(text, (20, y))
        y += font.get_linesize()                    # Keeps going past window bottom
```

**The problem:** Text renders beyond the 600-pixel window height and overlaps with content that should be in a different region.

### Issue 3: No Horizontal Clipping

```python
screen.blit(text, (20, y))  # Text can extend beyond window width (900px)
```

**The problem:** Long lines (like battle descriptions) extend past the right edge of the window.

---

## Solution 1: Quick Fix (Minimal Changes)

Add bounds checking to `_render_lines` and calculate log position dynamically.

### Step 1: Modify `_render_lines` to Accept Boundaries

```python
def _render_lines(
    screen: pygame.Surface, 
    font: pygame.font.Font, 
    lines: list[str], 
    start_y: int,
    max_y: int = None,          # NEW: stop rendering at this Y position
    max_width: int = None       # NEW: truncate lines wider than this
) -> int:                       # NEW: return final Y position
    """Render lines of text, respecting optional boundaries."""
    y = start_y
    max_y = max_y or screen.get_height()
    max_width = max_width or screen.get_width() - 40  # 20px padding each side
    
    for line in lines:
        # Stop if we'd render past the boundary
        if y + font.get_linesize() > max_y:
            break
            
        text = font.render(line, True, TEXT_COLOR)
        
        # Truncate if too wide
        if text.get_width() > max_width:
            while len(line) > 0 and font.size(line + "...")[0] > max_width:
                line = line[:-1]
            text = font.render(line + "...", True, TEXT_COLOR)
        
        screen.blit(text, (20, y))
        y += font.get_linesize()
    
    return y  # Return where we stopped
```

### Step 2: Use Dynamic Positioning in the Render Loop

Replace lines 394-397:

```python
# OLD CODE:
_render_lines(screen, font, status_lines, 20)
log_header = ["Event Log:"] + log
_render_lines(screen, font, log_header, 300)

# NEW CODE:
# Define regions
STATUS_REGION_END = 280    # Status panel: Y=20 to Y=280
LOG_REGION_START = 300     # Log panel: Y=300 to Y=580
LOG_REGION_END = 580       # Leave 20px padding at bottom

# Render status with boundary
_render_lines(screen, font, status_lines, 20, max_y=STATUS_REGION_END)

# Render log with boundary  
log_header = ["Event Log:"] + log
_render_lines(screen, font, log_header, LOG_REGION_START, max_y=LOG_REGION_END)
```

### Step 3: Limit Log Length Based on Available Space

```python
# Calculate how many log lines fit
line_height = font.get_linesize()
available_height = LOG_REGION_END - LOG_REGION_START - line_height  # -1 for header
max_log_lines = available_height // line_height

# Trim log to fit (keep most recent)
log = log[-max_log_lines:]
```

---

## Solution 2: Panel-Based Layout (Recommended)

This is what `pygame_ui_refactored.py` implements. The idea is to divide the screen into non-overlapping rectangular regions.

### Define Panel Boundaries

```python
# At the top of the file, define layout constants
WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
PANEL_MARGIN = 5
PANEL_PADDING = 10

# Calculate panel rectangles
STATUS_PANEL = pygame.Rect(
    PANEL_MARGIN,                           # x
    PANEL_MARGIN,                           # y  
    WINDOW_WIDTH // 3 - PANEL_MARGIN,       # width (1/3 of screen)
    WINDOW_HEIGHT // 2 - PANEL_MARGIN       # height (top half)
)

CONTEXT_PANEL = pygame.Rect(
    WINDOW_WIDTH // 3 + PANEL_MARGIN,       # x (right 2/3)
    PANEL_MARGIN,                           # y
    WINDOW_WIDTH * 2 // 3 - 2 * PANEL_MARGIN,  # width
    WINDOW_HEIGHT // 2 - PANEL_MARGIN       # height
)

LOG_PANEL = pygame.Rect(
    PANEL_MARGIN,                           # x
    WINDOW_HEIGHT // 2 + PANEL_MARGIN,      # y (bottom half)
    WINDOW_WIDTH - 2 * PANEL_MARGIN,        # width (full width)
    WINDOW_HEIGHT // 2 - 2 * PANEL_MARGIN   # height
)
```

### Create a Panel Renderer

```python
def render_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    panel: pygame.Rect,
    title: str,
    lines: list[str],
    bg_color: tuple = (40, 40, 55),
    border_color: tuple = (80, 80, 100),
    text_color: tuple = (230, 230, 230)
) -> None:
    """Render text inside a bounded panel."""
    
    # Draw background
    pygame.draw.rect(screen, bg_color, panel)
    pygame.draw.rect(screen, border_color, panel, 2)
    
    # Calculate content area (inside padding)
    content_x = panel.left + PANEL_PADDING
    content_y = panel.top + PANEL_PADDING
    content_width = panel.width - 2 * PANEL_PADDING
    content_bottom = panel.bottom - PANEL_PADDING
    
    # Draw title
    if title:
        title_surf = font.render(title, True, text_color)
        screen.blit(title_surf, (content_x, content_y))
        content_y += font.get_linesize() + 5
    
    # Draw lines (respecting boundaries)
    for line in lines:
        if content_y + font.get_linesize() > content_bottom:
            break  # Stop if we'd overflow
            
        # Truncate long lines
        text_surf = font.render(line, True, text_color)
        if text_surf.get_width() > content_width:
            while len(line) > 0 and font.size(line + "...")[0] > content_width:
                line = line[:-1]
            text_surf = font.render(line + "...", True, text_color)
        
        screen.blit(text_surf, (content_x, content_y))
        content_y += font.get_linesize()
```

### Use Panels in the Render Loop

```python
# Clear screen
screen.fill(BACKGROUND)

# Render each panel independently - they can't overlap!
render_panel(screen, font, STATUS_PANEL, "Status", status_lines)
render_panel(screen, font, CONTEXT_PANEL, "Battle" if engine.in_battle() else "Explore", context_lines)
render_panel(screen, font, LOG_PANEL, "Event Log", log)

pygame.display.flip()
```

---

## Solution 3: Scrollable Regions (Advanced)

For very long content (like battle logs), implement scrolling:

```python
class ScrollablePanel:
    def __init__(self, rect: pygame.Rect, font: pygame.font.Font):
        self.rect = rect
        self.font = font
        self.scroll_offset = 0  # Lines scrolled from top
        self.lines: list[str] = []
    
    def set_content(self, lines: list[str]) -> None:
        self.lines = lines
        # Auto-scroll to bottom for new content
        visible_lines = self._visible_line_count()
        if len(lines) > visible_lines:
            self.scroll_offset = len(lines) - visible_lines
    
    def scroll(self, delta: int) -> None:
        """Scroll by delta lines (positive = down, negative = up)."""
        max_scroll = max(0, len(self.lines) - self._visible_line_count())
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + delta))
    
    def _visible_line_count(self) -> int:
        content_height = self.rect.height - 2 * PANEL_PADDING
        return content_height // self.font.get_linesize()
    
    def render(self, screen: pygame.Surface) -> None:
        # Draw background
        pygame.draw.rect(screen, (40, 40, 55), self.rect)
        pygame.draw.rect(screen, (80, 80, 100), self.rect, 2)
        
        # Get visible slice of lines
        visible_count = self._visible_line_count()
        start = self.scroll_offset
        end = start + visible_count
        visible_lines = self.lines[start:end]
        
        # Render visible lines
        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING
        for line in visible_lines:
            text = self.font.render(line, True, TEXT_COLOR)
            screen.blit(text, (x, y))
            y += self.font.get_linesize()
        
        # Draw scroll indicator if needed
        if len(self.lines) > visible_count:
            self._draw_scrollbar(screen, visible_count)
    
    def _draw_scrollbar(self, screen: pygame.Surface, visible_count: int) -> None:
        total = len(self.lines)
        bar_height = self.rect.height - 2 * PANEL_PADDING
        thumb_height = max(20, bar_height * visible_count // total)
        thumb_pos = bar_height * self.scroll_offset // total
        
        bar_rect = pygame.Rect(
            self.rect.right - 12,
            self.rect.top + PANEL_PADDING + thumb_pos,
            8,
            thumb_height
        )
        pygame.draw.rect(screen, (100, 100, 120), bar_rect)
```

---

## Applying the Fix: Step-by-Step

Here's the minimal change to fix the overlap in the existing `pygame_ui.py`:

### 1. Replace the `_render_lines` function (lines 16-21):

```python
def _render_lines(
    screen: pygame.Surface, 
    font: pygame.font.Font, 
    lines: list[str], 
    start_y: int,
    max_y: int = 600,
    max_width: int = 860
) -> int:
    y = start_y
    for line in lines:
        if y + font.get_linesize() > max_y:
            break
        text = font.render(line, True, TEXT_COLOR)
        if text.get_width() > max_width:
            while len(line) > 3 and font.size(line + "...")[0] > max_width:
                line = line[:-1]
            text = font.render(line + "...", True, TEXT_COLOR)
        screen.blit(text, (20, y))
        y += font.get_linesize()
    return y
```

### 2. Replace the rendering section (lines 394-397):

```python
        # Render status (top region: Y=20 to Y=280)
        _render_lines(screen, font, status_lines, 20, max_y=280)

        # Render log (bottom region: Y=300 to Y=580)
        log_header = ["Event Log:"] + log[-10:]  # Limit to 10 recent entries
        _render_lines(screen, font, log_header, 300, max_y=580)
```

This ensures:
- Status lines stop before Y=280
- Log lines stop before Y=580  
- There's a 20-pixel gap between regions
- Long lines get truncated with "..."

---

## Visual Comparison

### Before (Overlapping)
```
┌────────────────────────────────────────┐
│ Location: A5                           │ Y=20
│ Map: Beginner's Path                   │
│ HP: 85/120                             │
│ Level: 3  EXP: 450  Gold: 127          │
│ Current turn: Hero                     │
│ Party:                                 │
│ -> Hero - HP 85/120                    │
│    Hawk - HP 32/40                     │
│ Battle:                         ───────│─── Y=280 (where status SHOULD end)
│ -> 1. Goblin 1 - 45/50 HP              │
│    2. Goblin 2 - defeated        ──────│─── Y=300 (log starts here!)
│ Event Log:                  <-- OVERLAP│
│ Actions:                    <-- OVERLAP│
│   1. attack                 <-- OVERLAP│
│   ...                                  │
└────────────────────────────────────────┘
```

### After (Bounded)
```
┌────────────────────────────────────────┐
│ Location: A5                           │ Y=20
│ Map: Beginner's Path                   │
│ HP: 85/120                             │
│ Level: 3  EXP: 450  Gold: 127          │
│ Current turn: Hero                     │
│ Party:                                 │
│ -> Hero - HP 85/120                    │
│    Hawk - HP 32/40                     │
│ Battle:                                │
│ -> 1. Goblin 1 - 45/50 HP              │ Y=280 (status stops here)
├────────────────────────────────────────┤ 
│ Event Log:                             │ Y=300 (log starts here)
│ Hero attacks for 18 damage             │
│ Goblin 1 attacks for 12 damage         │
│ ...                                    │
│                                        │ Y=580 (log stops here)
└────────────────────────────────────────┘
```

---

## Summary

| Approach | Effort | Best For |
|----------|--------|----------|
| Quick Fix (bounds in `_render_lines`) | 10 min | Immediate fix |
| Panel-Based Layout | 1-2 hours | Clean architecture |
| Scrollable Regions | 2-3 hours | Long content like logs |

The refactored version (`pygame_ui_refactored.py`) implements the Panel-Based approach with proper separation of concerns. You can use it as a drop-in replacement or as a reference for modifying the original.
