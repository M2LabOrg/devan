# WebDesign MCP - Setup Instructions

Complete guide to setting up and using the WebDesign MCP server for automated React website generation.

## Prerequisites

You need either **uv** (recommended) or **pip** with Python 3.10+.

### Install uv (macOS/Linux)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install uv (Windows)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Step 1: Create the MCP Project Folder

Navigate to the webdesign_mcp folder:

```bash
cd /path/to/mcp-design-deploy/servers/webdesign
```

Create the mcp_project folder:
```bash
mkdir -p mcp_project
```

## Step 2: Set Up Environment

Navigate to the mcp_project folder:

```bash
cd mcp_project
```

Initialize the project:
```bash
uv init
```

Create virtual environment:
```bash
uv venv
```

Activate the environment:
```bash
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

Install dependencies:
```bash
uv add mcp
```

## Step 3: Configure in Windsurf

### Option 1: Edit mcp_config.json directly

Add this to your Windsurf MCP config:

```json
{
  "mcpServers": {
    "webdesign-mcp": {
      "command": "bash",
      "args": [
        "-c",
        "cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project && uv run webdesign_server.py"
      ]
    }
  }
}
```

### Option 2: Through Windsurf Settings UI

1. Open Windsurf Settings (Cmd+, on macOS)
2. Search for "MCP" or go to AI → Model Context Protocol
3. Click "Add Server"
4. Fill in:
   - **Name**: `webdesign-mcp`
   - **Transport**: `stdio`
   - **Command**: `bash`
   - **Args**: `-c`, `cd /path/to/mcp-design-deploy/servers/webdesign/mcp_project && uv run webdesign_server.py`

## Step 3a: Test with MCP Inspector (Optional)

Before configuring in Windsurf, you can test the server using the MCP Inspector tool. This helps verify everything is working correctly.

### Launch Inspector

From the mcp_project folder:

```bash
cd mcp_project
npx @modelcontextprotocol/inspector uv run webdesign_server.py
```

You'll see a URL like `http://localhost:5173`. Open it in your browser.

### Test in Inspector

1. **List Templates**
   - Tool: `list_design_templates`
   - Parameters: (empty)
   - Expected: 6 website templates

2. **List Color Palettes**
   - Tool: `list_color_palettes`
   - Parameters: (empty)
   - Expected: 4 palettes with hex codes

3. **Analyze Use Case**
   - Tool: `analyze_use_case`
   - Parameters:
     - `project_name`: `Test Landing`
     - `description`: `Landing page for a test project`
     - `target_audience`: `test users`
     - `primary_goal`: `test the server`

4. **Get Component Template**
   - Tool: `get_component_template`
   - Parameters:
     - `component_name`: `Hero`
     - `variant`: `default`

### Inspector Tips

- The left panel shows available tools
- Click a tool to see its parameters
- Fill in the form and click "Execute"
- Results appear in the right panel
- Great for learning what each tool does before using in Windsurf

Once tested in Inspector, proceed to Step 4 to configure in Windsurf.

## Step 4: Test in Windsurf

Restart Windsurf or reload the window to pick up the new MCP server.

### Test Command 1: List Templates
Ask your AI assistant: "Show me available website templates"

Expected: List of 6 templates (landing_page, corporate_site, portfolio, dashboard, ecommerce, documentation)

### Test Command 2: List Color Palettes
Ask: "What color palettes are available?"

Expected: 4 palettes (corporate, energy, dark_modern, minimal) with hex codes

## Step 5: Create Your First Website

### Example: Solar Panel Company Landing Page

Ask your AI:
> "I need a landing page for a solar panel installation company called 'SolarPro'. Target audience is homeowners in California who want to reduce energy bills. I need a hero section, features, testimonials, and a contact form."

The AI will:
1. Call `analyze_use_case` to generate design specs
2. Recommend **landing_page** template
3. Suggest **energy** color palette (green/sustainable)
4. List required components

### Step 5a: Review Design Specs

The AI will show you:
- **Template**: landing_page
- **Color Palette**: energy (greens, eco-friendly)
- **Tech Stack**: Modern React (Vite + TypeScript + Tailwind)
- **Components**: Hero, FeatureGrid, TestimonialCarousel, ContactForm, CTA Banner
- **Pages**: Single page with sections

Review and approve, or ask for changes:
- "Use corporate palette instead"
- "Make it a multi-page corporate site"
- "Add a pricing section"

### Step 5b: Generate Project Scaffold

Once specs are approved, the AI will:
1. Call `generate_project_scaffold`
2. Create all project files
3. Show you the folder structure

### Step 5c: Get Components

The AI will provide:
- Hero component code
- FeatureCard component
- Testimonial component
- ContactForm component

Each component includes:
- Full TypeScript code
- Props interface
- Usage example
- Styling with Tailwind

### Step 5d: Start Development

The AI will give you commands:

```bash
cd generated_projects/solarpro-landing
npm install
npm run dev
```

Open http://localhost:5173 to see your site!

## Understanding the Output

### Generated Files

1. **specs/design-specs.md** - Complete design documentation
   - Color palette with hex codes
   - Typography scale
   - Tech stack details
   - Page structure
   - Component checklist

2. **tailwind.config.js** - Pre-configured with your colors
   - Primary, secondary, accent colors
   - Custom border radius
   - Animation keyframes

3. **package.json** - All dependencies ready
   - React 18, TypeScript, Vite
   - Tailwind CSS, shadcn/ui utilities
   - Framer Motion, Lucide icons

4. **src/App.tsx** - Main app with routing
   - React Router setup
   - Page components
   - Basic layout

5. **Component files** - Ready to customize
   - Button, Card, Input primitives
   - Placeholder for your custom components

### Design Tokens

Your design specs include:

```json
{
  "colors": {
    "primary": "#059669",
    "secondary": "#10B981",
    "accent": "#F97316",
    "background": "#FFFFFF",
    "surface": "#ECFDF5"
  },
  "typography": {
    "heading_font": "Inter",
    "body_font": "Inter",
    "scale": {
      "h1": "3.5rem",
      "body": "1rem"
    }
  },
  "spacing": {
    "section": "6rem",
    "component": "2rem"
  }
}
```

## Customizing Your Site

### Change Colors

Edit `tailwind.config.js`:
```javascript
colors: {
  primary: '#your-color',
  secondary: '#your-secondary',
}
```

Or regenerate with a different palette:
> "Regenerate with the dark_modern palette"

### Add New Components

Ask: "Give me a PricingCard component"

The AI will call `get_component_template` and provide ready-to-use code.

### Add New Pages

For multi-page sites, the AI creates:
- Home page
- About page
- Services page
- Contact page

Each with proper routing in App.tsx.

## Advanced Usage

### Custom Component Variants

Components support variants:

```
get_component_template(
    component_name="Hero",
    variant="gradient"  # or "minimal", "centered"
)
```

Variants include:
- **Hero**: default, gradient, minimal, split
- **Button**: default, secondary, outline, ghost
- **Card**: default, elevated, bordered

### Design Tokens Only

Get CSS variables without generating a project:

```
get_design_tokens(palette_key="energy")
```

Returns CSS variables and Tailwind config snippet.

### Multiple Projects

Each call to `generate_project_scaffold` creates a new folder:
- `generated_projects/solarpro-landing/`
- `generated_projects/tech-dashboard/`
- `generated_projects/corporate-site/`

## Tips for Success

### 1. Good Project Descriptions

**Good**: "Landing page for B2B SaaS analytics platform targeting marketing teams at mid-size companies"

**Vague**: "Website for a company"

### 2. Specify Target Audience

Helps choose the right color palette:
- "Young professionals" → dark_modern
- "Corporate executives" → corporate
- "Eco-conscious consumers" → energy
- "Luxury buyers" → minimal

### 3. List Must-Have Features

The AI will ensure components support:
- "Need a booking calendar" → Adds BookingCalendar component
- "Showcase portfolio" → Adds ProjectGallery
- "Collect leads" → Adds ContactForm

### 4. Review Before Generating

The design specs include:
- Complexity score
- Estimated pages
- Component checklist

Review these and iterate before creating files.

## Troubleshooting

**"uv command not found"**
```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**"Server not connecting"**
- Check the path in mcp_config.json is correct
- Ensure webdesign_server.py exists in mcp_project/
- Restart Windsurf

**"npm install fails"**
- Check Node.js version: `node --version` (needs 18+)
- Delete node_modules and package-lock.json
- Run npm install again

**"Components look wrong"**
- Check tailwind.config.js has your colors
- Verify index.html includes Inter font
- Check CSS imports in main.tsx

## Example Projects

Try these prompts with your AI assistant:

### 1. Portfolio Site
> "Create a portfolio website for a UX designer. Needs project showcase, about section, and contact. Use minimal palette."

### 2. SaaS Dashboard
> "I need a dashboard for a project management tool. Target audience is remote teams. Needs task list, charts, and team overview."

### 3. E-commerce Store
> "Build an e-commerce site for handmade pottery. Product grid, cart, checkout flow. Energy palette for artisan/craft feel."

### 4. Documentation Site
> "Create documentation site for an API. Needs navigation sidebar, search, code examples. Corporate palette."

## Next Steps

1. **Create 3 test projects** - Get familiar with the workflow
2. **Customize components** - Add your specific styling
3. **Build a component library** - Save favorite components
4. **Iterate on design** - Use AI to refine layouts
5. **Deploy** - Build with `npm run build` and deploy to Vercel/Netlify

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [React Router](https://reactrouter.com/en/main)
- [Vite Guide](https://vitejs.dev/guide/)

## Getting Help

If something isn't working:

1. Check generated `specs/design-specs.md` for details
2. Review `package.json` for correct dependencies
3. Check browser console for errors
4. Verify Tailwind classes are being applied
5. Ask your AI assistant to debug specific issues
