# WebDesign MCP - Automated React Website Generator

An **MCP Server** that automates React website creation by analyzing use cases and generating complete design specifications, component templates, and project scaffolding.

## What It Does

Transform your website ideas into production-ready React projects:

1. **Describe your project** → AI analyzes requirements
2. **Get design specs** → Color palette, typography, layout recommendations  
3. **Generate scaffold** → Complete project structure with files
4. **Get components** → Pre-built React components matching your style

## Perfect For

- **Rapid prototyping** - Go from idea to working site in minutes
- **Consistent design** - Apply your established design patterns
- **Team efficiency** - Standardize component libraries across projects
- **Learning React** - See best practices in generated code

## Quick Start

### 1. Set Up the Server

```bash
cd mcp_project
uv init
uv venv
source .venv/bin/activate
uv add mcp
```

### 2. Configure in Windsurf

Add to your `mcp_config.json`:

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

### 3. Generate Your First Website

Ask your AI assistant:

> "Create a landing page for a solar panel installation company targeting homeowners in California"

The MCP server will:
- Recommend the **landing page template**
- Suggest **energy color palette** (greens, sustainable feel)
- Choose **Modern React stack** (Vite + TypeScript + Tailwind)
- Generate **design specifications** document
- Provide **component templates** (Hero, Features, Testimonials, CTA)

## Tools (11 Total)

### Analysis & Planning
- `analyze_use_case` - Analyze project requirements and generate complete design specs
- `list_design_templates` - View available website templates (landing, corporate, portfolio, etc.)
- `list_color_palettes` - Browse color schemes (corporate, energy, dark_modern, minimal)

### Project Generation
- `generate_project_scaffold` - Create complete project structure with all files
- `get_design_tokens` - Get CSS variables and Tailwind config for your palette

### Components
- `list_available_components` - View all available component templates
- `get_component_template` - Get React component code (Hero, Card, Button, etc.)

## Design System

### Color Palettes

| Palette | Primary | Use Case |
|---------|---------|----------|
| **corporate** | Deep blue (#1E40AF) | B2B, professional services |
| **energy** | Green (#059669) | Sustainability, clean tech |
| **dark_modern** | Indigo (#6366F1) | Tech startups, SaaS |
| **minimal** | Zinc (#18181B) | Luxury, fashion, portfolios |

### Typography
- **Font**: Inter (Google Fonts)
- **Scale**: H1 3.5rem → Body 1rem → Small 0.875rem
- **Weights**: 400 (body), 500 (medium), 600 (semibold), 700 (bold)

### Components Available

- **Hero** - Full-width hero with headline, subtitle, CTA button
- **FeatureCard** - Icon + title + description in card layout
- **Navigation** - Responsive header with mobile menu
- **Footer** - Site footer with links
- **Testimonial** - Quote card with attribution
- **PricingCard** - Pricing tier with feature list
- **ContactForm** - Form with validation
- **Button** - Multiple variants (primary, secondary, outline, ghost)
- **Card** - Container with shadow and rounded corners

## Example Workflow

### Step 1: Analyze Your Project

```
analyze_use_case(
    project_name="SolarPro Landing",
    description="Landing page for residential solar panel installation services",
    target_audience="homeowners aged 35-65 in suburban areas interested in reducing energy bills",
    primary_goal="generate quote requests and phone calls",
    must_have_features=["savings calculator", "service area map", "customer testimonials"]
)
```

**Returns**: Complete design specs including:
- Recommended template: `landing_page`
- Color palette: `energy` (green/sustainable)
- Tech stack: `modern_react`
- Components: Hero, FeatureGrid, TestimonialCarousel, ContactForm
- Page structure: Hero → Features → Calculator → Testimonials → CTA → Footer

### Step 2: Generate Project

```
generate_project_scaffold(
    project_name="solarpro-landing",
    design_specs={...}  # From step 1
)
```

**Creates**:
```
solarpro-landing/
├── specs/
│   └── design-specs.md          # Complete design documentation
├── src/
│   ├── components/
│   │   ├── ui/                  # Button, Card, Input
│   │   └── index.ts
│   ├── pages/                   # Page components
│   ├── hooks/                   # Custom hooks
│   ├── lib/                     # Utilities
│   └── types/                   # TypeScript types
├── public/
├── index.html
├── package.json
├── tailwind.config.js          # With your color palette
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### Step 3: Get Components

```
get_component_template(component_name="Hero")
```

**Returns** ready-to-use React code:
```tsx
export function Hero({ title, subtitle, ctaText }: HeroProps) {
  return (
    <section className="py-20 lg:py-32">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">{title}</h1>
          <p className="text-xl text-muted-foreground mb-8">{subtitle}</p>
          <Button size="lg">{ctaText}</Button>
        </div>
      </div>
    </section>
  );
}
```

### Step 4: Start Developing

```bash
cd solarpro-landing
npm install
npm run dev
```

## Website Templates

| Template | Pages | Use Case |
|----------|-------|----------|
| **landing_page** | 1 | Marketing sites, product launches |
| **corporate_site** | 6 | Business websites, about/services/contact |
| **portfolio** | 5 | Creative work showcase |
| **dashboard** | 5 | Admin panels, data visualization |
| **ecommerce** | 6 | Online stores, product catalogs |
| **documentation** | 10+ | API docs, technical guides |

## Tech Stack

**Modern React Stack** (default):
- Vite - Fast build tool
- React 18 - UI library
- TypeScript - Type safety
- Tailwind CSS - Utility-first CSS
- shadcn/ui - Component primitives
- React Router - Navigation
- Framer Motion - Animations
- Lucide React - Icons
- Zustand - State management

**Next.js Full-Stack** (for complex apps):
- Next.js 14 - Full-stack framework
- App Router - File-based routing
- Server Actions - Backend logic

## Design Philosophy

This MCP server captures design patterns from production websites:

1. **Consistency** - Same spacing, colors, typography across projects
2. **Modern best practices** - React hooks, TypeScript, accessibility
3. **Performance** - Vite for fast builds, optimized bundles
4. **Maintainability** - Clean component structure, typed props
5. **Flexibility** - Easy to customize generated code

## Folder Structure

```
webdesign_mcp/
├── mcp_project/              # MCP server code
│   ├── webdesign_server.py   # Main server (11 tools)
│   └── pyproject.toml        # Dependencies
├── generated_projects/       # Output folder for created projects
├── README.md                # This file
├── demo_instructions.md     # Detailed setup guide
└── demo_notebook.ipynb      # Interactive tutorial
```

## Tips for Best Results

1. **Be specific in descriptions** - "E-commerce for handmade jewelry" vs "online store"
2. **Define target audience** - Helps choose appropriate color palette
3. **List must-have features** - Ensures right components are suggested
4. **Review design specs** - Adjust palette or template before generating
5. **Customize generated code** - Add your specific business logic

## Troubleshooting

**Server won't start**
- Check you're in mcp_project folder
- Verify uv is installed: `uv --version`
- Ensure virtual environment is activated

**Generated project won't run**
- Run `npm install` first
- Check Node.js version: `node --version` (needs 18+)
- Try deleting node_modules and reinstalling

**Components don't match style**
- Review design-specs.md in specs folder
- Update Tailwind config colors
- Override component props

## Next Steps

1. **Generate a test project** - Try the solar panel example above
2. **Explore components** - Use get_component_template for each component
3. **Customize design system** - Edit DESIGN_SYSTEM in webdesign_server.py
4. **Add new templates** - Create custom website templates
5. **Build your portfolio** - Rapidly create showcase sites

## Resources

- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)
- [Framer Motion](https://www.framer.com/motion/)
- [React Router](https://reactrouter.com/)

## License

MIT - Use for personal and commercial projects.
