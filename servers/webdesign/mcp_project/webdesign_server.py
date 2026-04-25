"""
MCP Server for Web Design Automation

This server automates React website creation by:
1. Analyzing use cases and generating design specifications
2. Applying established design patterns and component libraries
3. Scaffolding projects with modern tooling (React, Tailwind, shadcn/ui)
4. Generating design tokens and style guides
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("webdesign-mcp")

# Default output directory for generated projects
OUTPUT_DIR = os.environ.get("WEBDESIGN_OUTPUT_DIR", "../generated_projects")

# Design System - Based on user's established patterns
DESIGN_SYSTEM = {
    "name": "M2Lab Design System",
    "version": "1.0.0",
    "philosophy": "Modern, clean, professional web experiences with focus on usability and visual appeal",
    
    "color_palettes": {
        "corporate": {
            "primary": "#1E40AF",      # Deep blue
            "secondary": "#3B82F6",    # Bright blue
            "accent": "#F59E0B",       # Amber
            "background": "#FFFFFF",
            "surface": "#F8FAFC",
            "text": {
                "primary": "#0F172A",
                "secondary": "#475569",
                "muted": "#94A3B8"
            }
        },
        "energy": {
            "primary": "#059669",      # Green
            "secondary": "#10B981",    # Emerald
            "accent": "#F97316",       # Orange
            "background": "#FFFFFF",
            "surface": "#ECFDF5",
            "text": {
                "primary": "#064E3B",
                "secondary": "#065F46",
                "muted": "#6B7280"
            }
        },
        "dark_modern": {
            "primary": "#6366F1",      # Indigo
            "secondary": "#8B5CF6",    # Purple
            "accent": "#14B8A6",       # Teal
            "background": "#0F172A",
            "surface": "#1E293B",
            "text": {
                "primary": "#F8FAFC",
                "secondary": "#CBD5E1",
                "muted": "#64748B"
            }
        },
        "minimal": {
            "primary": "#18181B",      # Zinc
            "secondary": "#27272A",    # Dark zinc
            "accent": "#E11D48",       # Rose
            "background": "#FAFAFA",
            "surface": "#FFFFFF",
            "text": {
                "primary": "#18181B",
                "secondary": "#52525B",
                "muted": "#A1A1AA"
            }
        },
        "zen": {
            "primary": "#1a1a2e",      # Deep ink
            "secondary": "#3d3d56",    # Ink light
            "accent": "#c0392b",       # Vermilion — torii red
            "background": "#fafaf8",   # Warm paper
            "surface": "#f5f4f0",      # Parchment
            "text": {
                "primary": "#1a1a2e",
                "secondary": "#3d3d56",
                "muted": "#8888a0"
            },
            "extra": {
                "accent_soft": "#e8d5c4",  # Warm beige
                "accent_ink": "#2d4a3e",   # Deep forest
                "paper_cool": "#f0f1f5"    # Cool paper
            }
        }
    },
    
    "typography": {
        "heading_font": "Inter",
        "body_font": "Inter",
        "scale": {
            "h1": { "size": "3.5rem", "weight": 700, "line_height": 1.1 },
            "h2": { "size": "2.5rem", "weight": 600, "line_height": 1.2 },
            "h3": { "size": "1.875rem", "weight": 600, "line_height": 1.3 },
            "h4": { "size": "1.5rem", "weight": 500, "line_height": 1.4 },
            "body": { "size": "1rem", "weight": 400, "line_height": 1.6 },
            "small": { "size": "0.875rem", "weight": 400, "line_height": 1.5 }
        }
    },
    
    "spacing": {
        "xs": "0.5rem",
        "sm": "1rem",
        "md": "1.5rem",
        "lg": "2rem",
        "xl": "3rem",
        "2xl": "4rem",
        "section": "6rem"
    },
    
    "border_radius": {
        "none": "0",
        "sm": "0.25rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "2xl": "1.5rem",
        "full": "9999px"
    },
    
    "shadows": {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
    },
    
    "components": {
        "button": {
            "variants": ["primary", "secondary", "outline", "ghost"],
            "sizes": ["sm", "md", "lg"],
            "border_radius": "lg"
        },
        "card": {
            "variants": ["default", "elevated", "bordered"],
            "padding": "lg",
            "border_radius": "xl"
        },
        "input": {
            "variants": ["default", "filled", "outline"],
            "border_radius": "md"
        }
    },
    
    "layout_patterns": {
        "container_max_width": "1280px",
        "grid_columns": 12,
        "breakpoints": {
            "sm": "640px",
            "md": "768px",
            "lg": "1024px",
            "xl": "1280px",
            "2xl": "1536px"
        }
    },
    
    "animation": {
        "duration": {
            "fast": "150ms",
            "normal": "300ms",
            "slow": "500ms"
        },
        "easing": {
            "default": "cubic-bezier(0.4, 0, 0.2, 1)",
            "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)"
        }
    }
}

# Website type templates
WEBSITE_TEMPLATES = {
    "landing_page": {
        "name": "Landing Page",
        "description": "Single-page marketing site with hero, features, testimonials, CTA",
        "sections": ["hero", "features", "testimonials", "pricing", "faq", "cta", "footer"],
        "typical_pages": 1,
        "recommended_components": ["Hero", "FeatureGrid", "TestimonialCarousel", "PricingTable", "FAQAccordion", "CTABanner"]
    },
    "corporate_site": {
        "name": "Corporate Website",
        "description": "Multi-page business site with about, services, team, contact",
        "sections": ["home", "about", "services", "team", "careers", "contact"],
        "typical_pages": 6,
        "recommended_components": ["Navigation", "Hero", "ServiceCards", "TeamGrid", "ContactForm", "Footer"]
    },
    "portfolio": {
        "name": "Portfolio",
        "description": "Showcase work with gallery, case studies, about",
        "sections": ["home", "projects", "case-studies", "about", "contact"],
        "typical_pages": 5,
        "recommended_components": ["ProjectGallery", "CaseStudyLayout", "ImageCarousel", "SkillsList", "ContactForm"]
    },
    "dashboard": {
        "name": "Dashboard",
        "description": "Data visualization and management interface",
        "sections": ["overview", "analytics", "settings", "users", "reports"],
        "typical_pages": 5,
        "recommended_components": ["StatCards", "DataTable", "Charts", "Sidebar", "Header", "Filters"]
    },
    "ecommerce": {
        "name": "E-commerce",
        "description": "Product catalog with cart, checkout, account",
        "sections": ["home", "products", "product-detail", "cart", "checkout", "account"],
        "typical_pages": 6,
        "recommended_components": ["ProductGrid", "ProductCard", "ShoppingCart", "FilterSidebar", "SearchBar", "CheckoutForm"]
    },
    "documentation": {
        "name": "Documentation Site",
        "description": "Technical docs with navigation, search, code blocks",
        "sections": ["home", "docs", "api-reference", "guides", "changelog"],
        "typical_pages": 10,
        "recommended_components": ["SidebarNav", "Search", "CodeBlock", "TableOfContents", "Breadcrumbs", "VersionSelector"]
    },
    "zen_command": {
        "name": "Zen Command Interface",
        "description": "Futuristic Japanese minimalist search-centric interface with floating action bars",
        "sections": ["command-bar", "results-grid", "detail-panel", "action-bar"],
        "typical_pages": 1,
        "recommended_components": ["CommandBar", "ResultCard", "DetailPanel", "ActionBar", "ZenLayout"]
    }
}

# Tech stack recommendations
TECH_STACKS = {
    "modern_react": {
        "name": "Modern React",
        "description": "Vite + React + TypeScript + Tailwind + shadcn/ui",
        "framework": "React",
        "build_tool": "Vite",
        "language": "TypeScript",
        "styling": "Tailwind CSS",
        "ui_library": "shadcn/ui",
        "routing": "React Router",
        "state_management": "Zustand",
        "icons": "Lucide React",
        "animation": "Framer Motion"
    },
    "nextjs_fullstack": {
        "name": "Next.js Full-Stack",
        "description": "Next.js 14 + App Router + TypeScript + Tailwind",
        "framework": "Next.js",
        "build_tool": "Next.js",
        "language": "TypeScript",
        "styling": "Tailwind CSS",
        "ui_library": "shadcn/ui",
        "routing": "Next.js App Router",
        "state_management": "React Context + Server Actions",
        "icons": "Lucide React",
        "animation": "Framer Motion"
    }
}


@mcp.tool()
def list_design_templates() -> str:
    """
    List available website design templates.
    
    Returns:
        JSON with available templates for different use cases.
    """
    templates_summary = {}
    for key, template in WEBSITE_TEMPLATES.items():
        templates_summary[key] = {
            "name": template["name"],
            "description": template["description"],
            "typical_pages": template["typical_pages"],
            "key_sections": template["sections"][:4]  # First 4 sections
        }
    
    return json.dumps({
        "available_templates": templates_summary,
        "total_templates": len(templates_summary),
        "usage": "Use analyze_use_case() to get a recommendation, or specify template_key directly"
    }, indent=2)


@mcp.tool()
def list_color_palettes() -> str:
    """
    List available color palettes in the design system.
    
    Returns:
        JSON with color palette options.
    """
    palettes_summary = {}
    for key, palette in DESIGN_SYSTEM["color_palettes"].items():
        palettes_summary[key] = {
            "name": key.replace("_", " ").title(),
            "primary": palette["primary"],
            "secondary": palette["secondary"],
            "accent": palette["accent"],
            "background": palette["background"],
            "vibe": _get_palette_vibe(key)
        }
    
    return json.dumps({
        "available_palettes": palettes_summary,
        "recommendation": "Choose based on brand personality: corporate for B2B, energy for sustainability, dark_modern for tech, minimal for luxury, zen for Japanese minimalist search-centric UI"
    }, indent=2)


def _get_palette_vibe(palette_key: str) -> str:
    """Get the vibe description for a palette."""
    vibes = {
        "corporate": "Professional, trustworthy, business-focused",
        "energy": "Fresh, sustainable, forward-thinking",
        "dark_modern": "Tech-forward, sophisticated, premium",
        "minimal": "Elegant, clean, high-end",
        "zen": "Japanese minimalist, search-centric, futuristic calm"
    }
    return vibes.get(palette_key, "Versatile")


@mcp.tool()
def analyze_use_case(
    project_name: str,
    description: str,
    target_audience: str,
    primary_goal: str,
    must_have_features: Optional[List[str]] = None
) -> str:
    """
    Analyze a web project use case and recommend design specifications.
    
    This tool takes your project requirements and generates:
    - Recommended template type
    - Suggested color palette
    - Tech stack recommendation
    - Component requirements
    - Page structure suggestions
    
    Args:
        project_name: Name of the project
        description: Brief description of what the website does
        target_audience: Who will use this website (e.g., "energy company managers", "job seekers")
        primary_goal: Main purpose (e.g., "generate leads", "showcase portfolio", "provide information")
        must_have_features: Optional list of required features
        
    Returns:
        JSON with comprehensive design specifications.
        
    Example:
        analyze_use_case(
            project_name="EnergyAudit Pro",
            description="Platform for scheduling and managing energy audits for commercial buildings",
            target_audience="facility managers and sustainability officers at large corporations",
            primary_goal="generate audit bookings and showcase audit methodology",
            must_have_features=["booking calendar", "audit report viewer", "team profiles"]
        )
    """
    must_have_features = must_have_features or []
    
    # Analyze and make recommendations
    recommendations = _analyze_requirements(
        description, target_audience, primary_goal, must_have_features
    )
    
    # Generate design specs
    specs = {
        "project_name": project_name,
        "analysis": {
            "description": description,
            "target_audience": target_audience,
            "primary_goal": primary_goal,
            "complexity_score": recommendations["complexity"],
            "estimated_pages": recommendations["pages"]
        },
        "recommendations": {
            "template": recommendations["template"],
            "color_palette": recommendations["palette"],
            "tech_stack": recommendations["stack"],
            "components": recommendations["components"],
            "pages_structure": recommendations["pages_structure"]
        },
        "design_tokens": _generate_design_tokens(recommendations["palette"]),
        "next_steps": [
            "1. Review and approve design specifications",
            "2. Use generate_project_scaffold() to create project files",
            "3. Customize components and content",
            "4. Add your specific business logic"
        ]
    }
    
    return json.dumps(specs, indent=2)


def _analyze_requirements(
    description: str,
    target_audience: str,
    primary_goal: str,
    features: List[str]
) -> Dict[str, Any]:
    """Analyze requirements and generate recommendations."""
    
    # Determine template based on description and goal
    desc_lower = description.lower()
    goal_lower = primary_goal.lower()
    
    if "dashboard" in desc_lower or "analytics" in desc_lower or "data" in desc_lower:
        template_key = "dashboard"
    elif any(word in desc_lower for word in ["shop", "store", "product", "buy", "sell"]):
        template_key = "ecommerce"
    elif "portfolio" in desc_lower or "showcase" in desc_lower or "work" in desc_lower:
        template_key = "portfolio"
    elif "documentation" in desc_lower or "docs" in desc_lower or "api" in desc_lower:
        template_key = "documentation"
    elif "corporate" in desc_lower or "company" in desc_lower or len(features) > 5:
        template_key = "corporate_site"
    else:
        template_key = "landing_page"
    
    # Determine palette based on audience and vibe
    if any(word in desc_lower for word in ["zen", "minimal", "japanese", "search-centric", "command", "futuristic"]):
        palette_key = "zen"
    elif any(word in target_audience.lower() for word in ["energy", "sustainability", "green", "environment"]):
        palette_key = "energy"
    elif any(word in desc_lower for word in ["tech", "software", "app", "platform"]):
        palette_key = "dark_modern"
    elif any(word in desc_lower for word in ["luxury", "premium", "high-end", "fashion"]):
        palette_key = "minimal"
    else:
        palette_key = "corporate"
    
    # Determine tech stack based on complexity
    complexity = len(features)
    if complexity > 8 or template_key == "dashboard":
        stack_key = "nextjs_fullstack"
    else:
        stack_key = "modern_react"
    
    template = WEBSITE_TEMPLATES[template_key]
    stack = TECH_STACKS[stack_key]
    
    # Generate component list
    base_components = template["recommended_components"]
    additional_components = []
    
    for feature in features:
        feature_lower = feature.lower()
        if "form" in feature_lower or "contact" in feature_lower:
            additional_components.append("ContactForm")
        if "calendar" in feature_lower or "booking" in feature_lower:
            additional_components.append("BookingCalendar")
        if "search" in feature_lower:
            additional_components.append("SearchBar")
        if "map" in feature_lower or "location" in feature_lower:
            additional_components.append("MapComponent")
        if "chart" in feature_lower or "graph" in feature_lower:
            additional_components.append("ChartComponent")
    
    all_components = list(set(base_components + additional_components))
    
    # Generate page structure
    pages_structure = _generate_pages_structure(template_key, features)
    
    return {
        "template": {
            "key": template_key,
            "name": template["name"],
            "description": template["description"]
        },
        "palette": {
            "key": palette_key,
            "name": palette_key.replace("_", " ").title()
        },
        "stack": {
            "key": stack_key,
            "name": stack["name"],
            "technologies": stack
        },
        "components": all_components,
        "pages_structure": pages_structure,
        "pages": len(pages_structure),
        "complexity": "high" if complexity > 8 else "medium" if complexity > 4 else "low"
    }


def _generate_pages_structure(template_key: str, features: List[str]) -> List[Dict[str, Any]]:
    """Generate page structure based on template."""
    template = WEBSITE_TEMPLATES[template_key]
    pages = []
    
    for section in template["sections"]:
        page = {
            "name": section.replace("-", " ").title(),
            "route": f"/{section}" if section != "home" else "/",
            "sections": []
        }
        
        # Add appropriate sections based on page type
        if section == "home" or section == "hero":
            page["sections"] = ["Hero", "Features Preview", "CTA"]
        elif section == "about":
            page["sections"] = ["Company Story", "Team", "Values"]
        elif section == "services" or section == "features":
            page["sections"] = ["Service Overview", "Detailed Features", "Benefits"]
        elif section == "contact":
            page["sections"] = ["Contact Info", "Contact Form", "Map"]
        elif section == "projects" or section == "products":
            page["sections"] = ["Filter/Search", "Grid/List", "Pagination"]
        
        pages.append(page)
    
    return pages


def _generate_design_tokens(palette: Dict[str, str]) -> Dict[str, Any]:
    """Generate design tokens from palette."""
    palette_key = palette["key"]
    colors = DESIGN_SYSTEM["color_palettes"][palette_key]
    
    return {
        "colors": colors,
        "typography": DESIGN_SYSTEM["typography"],
        "spacing": DESIGN_SYSTEM["spacing"],
        "border_radius": DESIGN_SYSTEM["border_radius"],
        "shadows": DESIGN_SYSTEM["shadows"],
        "animation": DESIGN_SYSTEM["animation"]
    }


@mcp.tool()
def generate_project_scaffold(
    project_name: str,
    design_specs: str,
    output_directory: Optional[str] = None
) -> str:
    """
    Generate a complete project scaffold based on design specifications.
    
    This creates all the necessary files and folder structure for your project.
    
    Args:
        project_name: Name for the project folder
        design_specs: JSON string from analyze_use_case() containing specifications
        output_directory: Optional custom output directory (defaults to OUTPUT_DIR env var)
        
    Returns:
        JSON with generated file structure and next steps.
        
    Example:
        generate_project_scaffold(
            project_name="my-energy-site",
            design_specs='{"recommendations": {...}}'
        )
    """
    try:
        specs = json.loads(design_specs)
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Invalid JSON in design_specs. Use output from analyze_use_case()"
        }, indent=2)
    
    output_dir = output_directory or OUTPUT_DIR
    project_path = os.path.join(output_dir, project_name)
    
    # Create folder structure
    folders = [
        f"{project_path}/src/components",
        f"{project_path}/src/components/ui",
        f"{project_path}/src/pages",
        f"{project_path}/src/hooks",
        f"{project_path}/src/lib",
        f"{project_path}/src/types",
        f"{project_path}/public",
        f"{project_path}/specs"
    ]
    
    created_folders = []
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            created_folders.append(folder)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to create folder {folder}: {str(e)}"
            }, indent=2)
    
    # Generate files
    generated_files = []
    
    # 1. Design Specs Document
    specs_file = os.path.join(project_path, "specs", "design-specs.md")
    _generate_design_specs_md(specs_file, specs)
    generated_files.append(specs_file)
    
    # 2. Tailwind Config
    tailwind_config = os.path.join(project_path, "tailwind.config.js")
    _generate_tailwind_config(tailwind_config, specs)
    generated_files.append(tailwind_config)
    
    # 3. Package.json
    package_json = os.path.join(project_path, "package.json")
    _generate_package_json(package_json, project_name, specs)
    generated_files.append(package_json)
    
    # 4. Component index
    components_index = os.path.join(project_path, "src/components", "index.ts")
    _generate_components_index(components_index, specs)
    generated_files.append(components_index)
    
    # 5. Main App component
    app_component = os.path.join(project_path, "src", "App.tsx")
    _generate_app_component(app_component, specs)
    generated_files.append(app_component)
    
    # 6. Main entry
    main_entry = os.path.join(project_path, "src", "main.tsx")
    _generate_main_entry(main_entry)
    generated_files.append(main_entry)
    
    # 7. Index HTML
    index_html = os.path.join(project_path, "index.html")
    _generate_index_html(index_html, project_name)
    generated_files.append(index_html)
    
    # 8. Vite config
    vite_config = os.path.join(project_path, "vite.config.ts")
    _generate_vite_config(vite_config)
    generated_files.append(vite_config)
    
    # 9. README
    readme = os.path.join(project_path, "README.md")
    _generate_project_readme(readme, project_name, specs)
    generated_files.append(readme)
    
    # 10. tsconfig.json
    tsconfig = os.path.join(project_path, "tsconfig.json")
    _generate_tsconfig(tsconfig)
    generated_files.append(tsconfig)
    
    return json.dumps({
        "project_name": project_name,
        "project_path": project_path,
        "folders_created": len(created_folders),
        "files_generated": len(generated_files),
        "generated_files": generated_files,
        "next_steps": [
            f"1. cd {project_path}",
            "2. npm install",
            "3. npm run dev",
            "4. Customize components in src/components/",
            "5. Add content to pages in src/pages/"
        ],
        "design_specs_location": specs_file
    }, indent=2)


def _generate_design_specs_md(filepath: str, specs: Dict[str, Any]) -> None:
    """Generate design specifications markdown document."""
    palette = specs.get("design_tokens", {}).get("colors", {})
    typography = specs.get("design_tokens", {}).get("typography", {})
    
    content = f"""# Design Specifications

## Project Overview

**Project Name:** {specs.get("project_name", "Untitled")}

**Description:** {specs.get("analysis", {}).get("description", "")}

**Target Audience:** {specs.get("analysis", {}).get("target_audience", "")}

**Primary Goal:** {specs.get("analysis", {}).get("primary_goal", "")}

## Design System

### Color Palette

- **Primary:** {palette.get("primary", "#000000")}
- **Secondary:** {palette.get("secondary", "#666666")}
- **Accent:** {palette.get("accent", "#FF0000")}
- **Background:** {palette.get("background", "#FFFFFF")}
- **Surface:** {palette.get("surface", "#F5F5F5")}
- **Text Primary:** {palette.get("text", {}).get("primary", "#000000")}
- **Text Secondary:** {palette.get("text", {}).get("secondary", "#666666")}
- **Text Muted:** {palette.get("text", {}).get("muted", "#999999")}

### Typography

- **Heading Font:** {typography.get("heading_font", "Inter")}
- **Body Font:** {typography.get("body_font", "Inter")}

### Spacing Scale

- xs: 0.5rem
- sm: 1rem
- md: 1.5rem
- lg: 2rem
- xl: 3rem
- 2xl: 4rem
- section: 6rem

## Tech Stack

{json.dumps(specs.get("recommendations", {}).get("stack", {}).get("technologies", {}), indent=2)}

## Pages Structure

"""
    
    pages = specs.get("recommendations", {}).get("pages_structure", [])
    for page in pages:
        content += f"\\n### {page.get('name', 'Page')}\\n"
        content += f"**Route:** {page.get('route', '/')}\\n"
        content += "**Sections:**\\n"
        for section in page.get("sections", []):
            content += f"- {section}\\n"
    
    content += "\\n## Components Required\\n\\n"
    components = specs.get("recommendations", {}).get("components", [])
    for component in components:
        content += f"- [ ] {component}\\n"
    
    with open(filepath, "w") as f:
        f.write(content)


def _generate_tailwind_config(filepath: str, specs: Dict[str, Any]) -> None:
    """Generate Tailwind CSS configuration."""
    palette = specs.get("design_tokens", {}).get("colors", {})
    
    config = f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  darkMode: ["class"],
  content: [
    './pages/**/*/{{ts,tsx}}',
    './components/**/*/{{ts,tsx}}',
    './app/**/*/{{ts,tsx}}',
    './src/**/*/{{ts,tsx}}',
  ],
  prefix: "",
  theme: {{
    container: {{
      center: true,
      padding: "2rem",
      screens: {{
        "2xl": "1400px",
      }},
    }},
    extend: {{
      colors: {{
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {{
          DEFAULT: "{palette.get('primary', '#1E40AF')}",
          foreground: "#FFFFFF",
        }},
        secondary: {{
          DEFAULT: "{palette.get('secondary', '#3B82F6')}",
          foreground: "#FFFFFF",
        }},
        accent: {{
          DEFAULT: "{palette.get('accent', '#F59E0B')}",
          foreground: "#000000",
        }},
        muted: {{
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        }},
        card: {{
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        }},
      }},
      borderRadius: {{
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      }},
      keyframes: {{
        "accordion-down": {{
          from: {{ height: "0" }},
          to: {{ height: "var(--radix-accordion-content-height)" }},
        }},
        "accordion-up": {{
          from: {{ height: "var(--radix-accordion-content-height)" }},
          to: {{ height: "0" }},
        }},
      }},
      animation: {{
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      }},
    }},
  }},
  plugins: [require("tailwindcss-animate")],
}}
"""
    
    with open(filepath, "w") as f:
        f.write(config)


def _generate_package_json(filepath: str, project_name: str, specs: Dict[str, Any]) -> None:
    """Generate package.json."""
    stack = specs.get("recommendations", {}).get("stack", {})
    
    package = {
        "name": project_name.lower().replace(" ", "-"),
        "private": True,
        "version": "0.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.20.0",
            "lucide-react": "^0.294.0",
            "class-variance-authority": "^0.7.0",
            "clsx": "^2.0.0",
            "tailwind-merge": "^2.0.0",
            "framer-motion": "^10.16.0"
        },
        "devDependencies": {
            "@types/react": "^18.2.37",
            "@types/react-dom": "^18.2.15",
            "@typescript-eslint/eslint-plugin": "^6.10.0",
            "@typescript-eslint/parser": "^6.10.0",
            "@vitejs/plugin-react": "^4.2.0",
            "autoprefixer": "^10.4.16",
            "eslint": "^8.53.0",
            "eslint-plugin-react-hooks": "^4.6.0",
            "eslint-plugin-react-refresh": "^0.4.4",
            "postcss": "^8.4.31",
            "tailwindcss": "^3.3.5",
            "tailwindcss-animate": "^1.0.7",
            "typescript": "^5.2.2",
            "vite": "^5.0.0"
        }
    }
    
    with open(filepath, "w") as f:
        json.dump(package, f, indent=2)


def _generate_components_index(filepath: str, specs: Dict[str, Any]) -> None:
    """Generate components index file."""
    components = specs.get("recommendations", {}).get("components", [])
    
    content = """// Component exports
export { Button } from './ui/Button';
export { Card } from './ui/Card';
export { Input } from './ui/Input';
"""
    
    for component in components:
        content += f'export {{ {component} }} from "./{component}";\n'
    
    with open(filepath, "w") as f:
        f.write(content)


def _generate_app_component(filepath: str, specs: Dict[str, Any]) -> None:
    """Generate main App component with Zen Command Bar support."""
    palette = specs.get("design_tokens", {}).get("colors", {})
    palette_key = specs.get("palette_key", "corporate")
    pages = specs.get("recommendations", {}).get("pages_structure", [])
    
    is_zen = palette_key == "zen"
    
    imports = "import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';\nimport './App.css';\n"
    if is_zen:
        imports += "import { ZenLayout } from './components/ZenLayout';\n"
        imports += "import { CommandBar } from './components/CommandBar';\n"
        imports += "import { useState } from 'react';\n"

    content = imports + f"""
function App() {{
"""
    if is_zen:
        content += """  const [searchQuery, setSearchQuery] = useState('');
  
  const actions = [
    { label: 'Home', category: 'Navigation', onClick: () => window.location.href = '/' },
    { label: 'Documentation', category: 'Resources', onClick: () => console.log('Docs clicked') },
  ];

  return (
    <Router>
      <ZenLayout>
        <div className="pt-12 pb-24 px-4">
          <div className="mb-12">
            <CommandBar 
              placeholder="Search or navigate..." 
              actions={actions}
              onSearch={(q) => setSearchQuery(q)}
            />
          </div>
          
          <Routes>
            <Route path="/" element={<Home searchQuery={searchQuery} />} />
"""
    else:
        content += f"""  return (
    <Router>
      <div className="min-h-screen bg-[{palette.get('background', '#FFFFFF')}]">
        <Routes>
          <Route path="/" element={{<Home />}} />
"""
    
    for page in pages[1:] if len(pages) > 1 else []:
        route = page.get("route", "/")
        name = page.get("name", "Page").replace(" ", "")
        content += f'          <Route path="{route}" element={{<{name} />}} />\n'
    
    if is_zen:
        content += """          </Routes>
        </div>
      </ZenLayout>
    </Router>
  );
}

// Placeholder components with Zen support
const Home = ({ searchQuery }: { searchQuery?: string }) => (
  <div className="max-w-4xl mx-auto">
    <h1 className="text-5xl font-serif mb-6 text-[#1a1a2e]">Welcome</h1>
    <p className="text-xl text-[#3d3d56] font-light leading-relaxed mb-12">
      {searchQuery ? `Searching for: ${searchQuery}` : "Experience the future of minimalist design."}
    </p>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="p-8 bg-white border border-black/[0.04] rounded-3xl shadow-sm">
        <h3 className="text-lg font-medium mb-2">Japanese Minimalism</h3>
        <p className="text-sm text-[#8888a0] font-light">Subtle ink tones and generous white space define this experience.</p>
      </div>
      <div className="p-8 bg-[#f5f4f0] border border-black/[0.04] rounded-3xl shadow-sm">
        <h3 className="text-lg font-medium mb-2">Command Centric</h3>
        <p className="text-sm text-[#8888a0] font-light">Focus on what matters. Everything is just a few keystrokes away.</p>
      </div>
    </div>
  </div>
);
"""
    else:
        content += """        </Routes>
      </div>
    </Router>
  );
}

const Home = () => <div className="p-8"><h1 className="text-4xl font-bold">Home Page</h1></div>;
"""
    
    for page in pages[1:] if len(pages) > 1 else []:
        name = page.get("name", "Page").replace(" ", "")
        content += f'const {name} = () => <div className="p-8"><h1 className="text-4xl font-bold">{name}</h1></div>;\n'
    
    content += "\nexport default App;\n"
    
    with open(filepath, "w") as f:
        f.write(content)


def _generate_main_entry(filepath: str) -> None:
    """Generate main.tsx entry point."""
    content = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
    with open(filepath, "w") as f:
        f.write(content)


def _generate_index_html(filepath: str, project_name: str) -> None:
    """Generate index.html."""
    content = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Noto+Sans+JP:wght@300;400;500&family=Noto+Serif+JP:wght@300;400;500&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
    with open(filepath, "w") as f:
        f.write(content)


def _generate_vite_config(filepath: str) -> None:
    """Generate Vite configuration."""
    content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
"""
    with open(filepath, "w") as f:
        f.write(content)


def _generate_project_readme(filepath: str, project_name: str, specs: Dict[str, Any]) -> None:
    """Generate project README."""
    content = f"""# {project_name}

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

## Project Structure

```
src/
├── components/     # React components
│   ├── ui/        # UI primitives (Button, Card, Input)
│   └── ...        # Feature components
├── pages/         # Page components
├── hooks/         # Custom React hooks
├── lib/           # Utility functions
└── types/         # TypeScript types
```

## Design System

See `specs/design-specs.md` for complete design specifications.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Framer Motion
- Lucide Icons
"""
    with open(filepath, "w") as f:
        f.write(content)


def _generate_tsconfig(filepath: str) -> None:
    """Generate tsconfig.json."""
    config = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True,
            "baseUrl": ".",
            "paths": {
                "@/*": ["./src/*"]
            }
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}]
    }
    
    with open(filepath, "w") as f:
        json.dump(config, f, indent=2)


@mcp.tool()
def get_component_template(component_name: str, variant: str = "default") -> str:
    """
    Get a React component template with proper styling.
    
    Args:
        component_name: Name of the component (e.g., "Hero", "FeatureCard")
        variant: Style variant (default, minimal, gradient, etc.)
        
    Returns:
        JSON with component code and usage example.
    """
    templates = {
        "Hero": _get_hero_template(variant),
        "FeatureCard": _get_feature_card_template(variant),
        "Button": _get_button_template(variant),
        "Card": _get_card_template(variant),
        "Navigation": _get_navigation_template(variant),
        "Footer": _get_footer_template(variant),
        "Testimonial": _get_testimonial_template(variant),
        "PricingCard": _get_pricing_card_template(variant),
        "ContactForm": _get_contact_form_template(variant),
        "CommandBar": _get_command_bar_template(variant),
        "ResultCard": _get_result_card_template(variant),
        "DetailPanel": _get_detail_panel_template(variant),
        "ActionBar": _get_action_bar_template(variant),
        "ZenLayout": _get_zen_layout_template(variant),
    }
    
    if component_name not in templates:
        return json.dumps({
            "error": f"Component '{component_name}' not found",
            "available_components": list(templates.keys())
        }, indent=2)
    
    return json.dumps({
        "component_name": component_name,
        "variant": variant,
        "code": templates[component_name],
        "usage": f"import {{ {component_name} }} from './components/{component_name}';",
        "file_name": f"{component_name}.tsx"
    }, indent=2)


def _get_hero_template(variant: str) -> str:
    return '''import { Button } from './ui/Button';
import { ArrowRight } from 'lucide-react';

interface HeroProps {
  title: string;
  subtitle: string;
  ctaText: string;
  ctaAction?: () => void;
}

export function Hero({ title, subtitle, ctaText, ctaAction }: HeroProps) {
  return (
    <section className="relative py-20 lg:py-32 overflow-hidden">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
            {title}
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            {subtitle}
          </p>
          <Button size="lg" onClick={ctaAction}>
            {ctaText}
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </section>
  );
}
'''


def _get_feature_card_template(variant: str) -> str:
    return '''import { LucideIcon } from 'lucide-react';
import { Card } from './ui/Card';

interface FeatureCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <Card className="p-6">
      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-primary" />
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </Card>
  );
}
'''


def _get_button_template(variant: str) -> str:
    return '''import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 py-2 px-4',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
'''


def _get_card_template(variant: str) -> str:
    return '''import { forwardRef, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

const Card = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      className
    )}
    {...props}
  />
));
Card.displayName = 'Card';

export { Card };
'''


def _get_navigation_template(variant: str) -> str:
    return '''import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { Button } from './ui/Button';

interface NavItem {
  label: string;
  href: string;
}

interface NavigationProps {
  items: NavItem[];
  logo?: string;
}

export function Navigation({ items, logo }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="font-bold text-xl">
            {logo || 'Logo'}
          </Link>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {items.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className="text-sm font-medium hover:text-primary transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t">
            {items.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className="block py-2 text-sm font-medium hover:text-primary"
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
'''


def _get_footer_template(variant: str) -> str:
    return '''import { Link } from 'react-router-dom';

interface FooterProps {
  companyName: string;
  links: { label: string; href: string }[];
}

export function Footer({ companyName, links }: FooterProps) {
  return (
    <footer className="border-t py-12">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground mb-4 md:mb-0">
            © {new Date().getFullYear()} {companyName}. All rights reserved.
          </p>
          <div className="flex space-x-6">
            {links.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
'''


def _get_testimonial_template(variant: str) -> str:
    return '''import { Card } from './ui/Card';
import { Quote } from 'lucide-react';

interface TestimonialProps {
  quote: string;
  author: string;
  role: string;
  company: string;
}

export function Testimonial({ quote, author, role, company }: TestimonialProps) {
  return (
    <Card className="p-6">
      <Quote className="h-8 w-8 text-primary/40 mb-4" />
      <p className="text-lg mb-4 italic">"{quote}"</p>
      <div>
        <p className="font-semibold">{author}</p>
        <p className="text-sm text-muted-foreground">
          {role}, {company}
        </p>
      </div>
    </Card>
  );
}
'''


def _get_pricing_card_template(variant: str) -> str:
    return '''import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Check } from 'lucide-react';

interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  features: string[];
  ctaText: string;
  popular?: boolean;
}

export function PricingCard({
  name,
  price,
  period = '/month',
  features,
  ctaText,
  popular = false,
}: PricingCardProps) {
  return (
    <Card className={`p-6 ${popular ? 'border-primary ring-2 ring-primary' : ''}`}>
      {popular && (
        <span className="inline-block bg-primary text-white text-xs font-semibold px-3 py-1 rounded-full mb-4">
          Popular
        </span>
      )}
      <h3 className="text-xl font-semibold mb-2">{name}</h3>
      <div className="mb-4">
        <span className="text-4xl font-bold">{price}</span>
        <span className="text-muted-foreground">{period}</span>
      </div>
      <ul className="space-y-2 mb-6">
        {features.map((feature, i) => (
          <li key={i} className="flex items-center text-sm">
            <Check className="h-4 w-4 text-primary mr-2" />
            {feature}
          </li>
        ))}
      </ul>
      <Button className="w-full" variant={popular ? 'default' : 'outline'}>
        {ctaText}
      </Button>
    </Card>
  );
}
'''


def _get_contact_form_template(variant: str) -> str:
    return '''import { useState } from 'react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Send } from 'lucide-react';

export function ContactForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission
    console.log('Form submitted:', formData);
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-2">
            Name
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2">
            Email
          </label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
        </div>
        <div>
          <label htmlFor="message" className="block text-sm font-medium mb-2">
            Message
          </label>
          <textarea
            id="message"
            rows={4}
            value={formData.message}
            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
        </div>
        <Button type="submit" className="w-full">
          Send Message
          <Send className="ml-2 h-4 w-4" />
        </Button>
      </form>
    </Card>
  );
}
'''


def _get_command_bar_template(variant: str) -> str:
    return '''import { useState, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface ActionChip {
  label: string;
  icon?: React.ReactNode;
  category: string;
  onClick?: () => void;
}

interface CommandBarProps {
  placeholder?: string;
  actions?: ActionChip[];
  onSearch?: (query: string) => void;
}

export function CommandBar({
  placeholder = "Design something beautiful...",
  actions = [],
  onSearch,
}: CommandBarProps) {
  const [active, setActive] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      if (e.key === 'Escape') {
        setActive(false);
        inputRef.current?.blur();
      }
    };
    const handleClick = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) {
        setActive(false);
      }
    };
    document.addEventListener('keydown', handleKey);
    document.addEventListener('click', handleClick);
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.removeEventListener('click', handleClick);
    };
  }, []);

  const categories = [...new Set(actions.map(a => a.category))];

  return (
    <div className="w-full max-w-[680px] mx-auto relative z-50" ref={barRef}>
      <div className={`
        bg-white/85 backdrop-blur-xl border border-black/[0.06] transition-all duration-300
        ${active
          ? 'rounded-2xl shadow-[0_8px_40px_rgba(26,26,46,0.08),0_0_60px_rgba(192,57,43,0.06)] border-[rgba(192,57,43,0.12)]'
          : 'rounded-[28px] shadow-[0_4px_20px_rgba(26,26,46,0.06)] hover:shadow-[0_8px_40px_rgba(26,26,46,0.08)]'
        }
        overflow-hidden
      `}>
        {/* Input row */}
        <div className="flex items-center gap-3 px-6 py-4">
          <Search className={`w-5 h-5 shrink-0 transition-colors ${active ? 'text-[#c0392b]' : 'text-[#8888a0]'}`} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              onSearch?.(e.target.value);
            }}
            onFocus={() => setActive(true)}
            placeholder={placeholder}
            className="flex-1 bg-transparent outline-none text-[#1a1a2e] placeholder:text-[#8888a0] placeholder:font-light text-base"
            autoComplete="off"
            spellCheck={false}
          />
          {query && (
            <button onClick={() => { setQuery(''); onSearch?.(''); }} className="p-1 hover:bg-black/5 rounded-full">
              <X className="w-4 h-4 text-[#8888a0]" />
            </button>
          )}
          <div className="flex items-center gap-1 opacity-40">
            <kbd className="px-1.5 py-0.5 text-[10px] font-medium text-[#8888a0] bg-[#f0f1f5] border border-black/[0.08] rounded">⌘</kbd>
            <kbd className="px-1.5 py-0.5 text-[10px] font-medium text-[#8888a0] bg-[#f0f1f5] border border-black/[0.08] rounded">K</kbd>
          </div>
        </div>

        {/* Expandable actions */}
        <div className={`transition-all duration-500 overflow-hidden ${active ? 'max-h-[400px] opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="h-px mx-6 bg-gradient-to-r from-transparent via-black/[0.06] to-transparent" />
          <div className="px-6 py-4 pb-6 space-y-4">
            {categories.map(cat => (
              <div key={cat}>
                <div className="text-[10px] font-medium text-[#8888a0] uppercase tracking-[0.15em] mb-2 pl-1">{cat}</div>
                <div className="flex flex-wrap gap-2">
                  {actions.filter(a => a.category === cat).map(action => (
                    <button
                      key={action.label}
                      onClick={() => {
                        action.onClick?.();
                        setActive(false);
                      }}
                      className="inline-flex items-center gap-2 px-3 py-2 bg-[#f5f4f0] rounded-full text-sm text-[#3d3d56] hover:bg-white hover:border-black/[0.08] hover:shadow-sm hover:-translate-y-px transition-all border border-transparent"
                    >
                      {action.icon}
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
'''


def _get_result_card_template(variant: str) -> str:
    return '''import { ReactNode } from 'react';

interface ResultCardProps {
  tag?: string;
  title: string;
  description: string;
  badges?: string[];
  featured?: boolean;
  visual?: ReactNode;
  onClick?: () => void;
}

export function ResultCard({
  tag,
  title,
  description,
  badges = [],
  featured = false,
  visual,
  onClick,
}: ResultCardProps) {
  return (
    <div
      onClick={onClick}
      className={`
        group bg-white border border-black/[0.06] rounded-[20px] cursor-pointer
        transition-all duration-300 relative overflow-hidden
        hover:-translate-y-0.5 hover:shadow-[0_8px_40px_rgba(26,26,46,0.08)] hover:border-black/[0.08]
        ${featured ? 'col-span-full grid grid-cols-2 gap-8 p-8' : 'p-6'}
      `}
    >
      {/* Top accent line on hover */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-[#c0392b] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div>
        {tag && (
          <span className="inline-block text-[10px] font-medium text-[#8888a0] uppercase tracking-[0.12em] mb-3">
            {tag}
          </span>
        )}
        <h3 className={`font-medium text-[#1a1a2e] mb-2 leading-snug ${featured ? 'text-lg' : 'text-base'}`}>
          {title}
        </h3>
        <p className="text-sm font-light text-[#3d3d56] leading-relaxed mb-4">
          {description}
        </p>
        <div className="flex items-center gap-3 flex-wrap">
          {badges.map((badge, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-medium
                ${i === 0 ? 'bg-[rgba(192,57,43,0.06)] text-[#c0392b]' : 'bg-[#f5f4f0] text-[#8888a0]'}`}
            >
              {badge}
            </span>
          ))}
        </div>
      </div>

      {featured && visual && (
        <div className="bg-[#f5f4f0] rounded-xl flex items-center justify-center min-h-[200px]">
          {visual}
        </div>
      )}
    </div>
  );
}
'''


def _get_detail_panel_template(variant: str) -> str:
    return '''import { ReactNode } from 'react';

interface Spec {
  label: string;
  value: string;
}

interface DetailPanelProps {
  open: boolean;
  onClose: () => void;
  tag?: string;
  title: string;
  body: string;
  specs?: Spec[];
  sections?: { title: string; content: string }[];
  actions?: ReactNode;
}

export function DetailPanel({
  open,
  onClose,
  tag,
  title,
  body,
  specs = [],
  sections = [],
  actions,
}: DetailPanelProps) {
  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        className={`fixed inset-0 bg-[#1a1a2e]/20 backdrop-blur-sm z-[200] transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      />

      {/* Panel */}
      <div className={`
        fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[720px] max-h-[85vh]
        bg-white rounded-t-[28px] shadow-[0_-10px_60px_rgba(26,26,46,0.12)]
        z-[201] overflow-y-auto transition-transform duration-500
        ${open ? 'translate-y-0' : 'translate-y-full'}
      `} style={{ transitionTimingFunction: 'cubic-bezier(0.22, 1, 0.36, 1)' }}>
        {/* Handle */}
        <div className="flex justify-center py-3 cursor-pointer" onClick={onClose}>
          <span className="w-10 h-1 bg-[#f0f1f5] rounded-full" />
        </div>

        <div className="px-8 pb-12">
          {tag && (
            <div className="text-[10px] font-medium text-[#c0392b] uppercase tracking-[0.15em] mb-3">{tag}</div>
          )}
          <h2 className="text-3xl font-serif text-[#1a1a2e] mb-4">{title}</h2>
          <p className="text-base text-[#3d3d56] leading-relaxed mb-8 font-light">{body}</p>

          {specs.length > 0 && (
            <div className="grid grid-cols-2 gap-6 mb-8 py-6 border-y border-black/[0.04]">
              {specs.map(spec => (
                <div key={spec.label}>
                  <div className="text-[10px] text-[#8888a0] uppercase tracking-[0.1em] mb-1">{spec.label}</div>
                  <div className="text-sm font-medium text-[#1a1a2e]">{spec.value}</div>
                </div>
              ))}
            </div>
          )}

          {sections.map(section => (
            <div key={section.title} className="mb-8">
              <h3 className="text-xs font-semibold text-[#1a1a2e] uppercase tracking-wider mb-3">{section.title}</h3>
              <p className="text-sm text-[#3d3d56] leading-relaxed font-light">{section.content}</p>
            </div>
          ))}

          {actions && (
            <div className="flex gap-3 pt-4">
              {actions}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
'''


def _get_action_bar_template(variant: str) -> str:
    return '''import { ReactNode } from 'react';

interface ActionBarProps {
  children: ReactNode;
}

export function ActionBar({ children }: ActionBarProps) {
  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-40">
      <div className="bg-[#1a1a2e]/90 backdrop-blur-xl border border-white/10 rounded-full px-2 py-2 shadow-2xl flex items-center gap-1">
        {children}
      </div>
    </div>
  );
}
'''


def _get_zen_layout_template(variant: str) -> str:
    return '''import { ReactNode } from 'react';

interface ZenLayoutProps {
  children: ReactNode;
}

export function ZenLayout({ children }: ZenLayoutProps) {
  return (
    <div className="min-h-screen bg-[#fafaf8] text-[#1a1a2e] font-sans selection:bg-[#c0392b]/10 selection:text-[#c0392b]">
      {/* Soft background grid or patterns could go here */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]" 
           style={{ backgroundImage: 'radial-gradient(#1a1a2e 1px, transparent 0)', backgroundSize: '40px 40px' }} />
      
      <main className="relative z-10">
        {children}
      </main>
    </div>
  );
}
'''


@mcp.tool()
def list_available_components() -> str:
    """
    List all available component templates.
    
    Returns:
        JSON with available components and their descriptions.
    """
    components = {
        "Hero": "Full-width hero section with headline, subtitle, and CTA",
        "FeatureCard": "Card with icon, title, and description for features grid",
        "Button": "Styled button with variants (primary, secondary, outline, ghost)",
        "Card": "Container with rounded corners and shadow",
        "Navigation": "Responsive header navigation with mobile menu",
        "Footer": "Site footer with links and copyright",
        "Testimonial": "Quote card with author attribution",
        "PricingCard": "Pricing tier card with features list",
        "ContactForm": "Contact form with name, email, and message fields",
        "CommandBar": "Expandable search/command bar with action chips (Zen)",
        "ResultCard": "Modern floating card for displaying items (Zen)",
        "DetailPanel": "Slide-up panel for focused content viewing (Zen)",
        "ActionBar": "Floating bottom bar for contextual actions (Zen)",
        "ZenLayout": "Minimalist layout wrapper with soft patterns (Zen)"
    }
    
    return json.dumps({
        "available_components": components,
        "total_components": len(components),
        "usage": "Use get_component_template(component_name) to get the code"
    }, indent=2)


@mcp.tool()
def get_design_tokens(palette_key: str = "corporate") -> str:
    """
    Get CSS design tokens for a specific color palette.
    
    Args:
        palette_key: Color palette name (corporate, energy, dark_modern, minimal, zen)
        
    Returns:
        JSON with CSS variables and design tokens.
    """
    if palette_key not in DESIGN_SYSTEM["color_palettes"]:
        return json.dumps({
            "error": f"Palette '{palette_key}' not found",
            "available_palettes": list(DESIGN_SYSTEM["color_palettes"].keys())
        }, indent=2)
    
    palette = DESIGN_SYSTEM["color_palettes"][palette_key]
    
    css_variables = f""":root {{
  /* Primary Colors */
  --primary: {palette['primary']};
  --secondary: {palette['secondary']};
  --accent: {palette['accent']};
  
  /* Background */
  --background: {palette['background']};
  --surface: {palette['surface']};
  
  /* Text */
  --text-primary: {palette['text']['primary']};
  --text-secondary: {palette['text']['secondary']};
  --text-muted: {palette['text']['muted']};
  
  /* Spacing */
  --space-xs: 0.5rem;
  --space-sm: 1rem;
  --space-md: 1.5rem;
  --space-lg: 2rem;
  --space-xl: 3rem;
  --space-section: 6rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
}}
"""
    
    return json.dumps({
        "palette": palette_key,
        "css_variables": css_variables,
        "tailwind_config": _generate_tailwind_theme_config(palette_key),
        "usage": "Add to your CSS or Tailwind config"
    }, indent=2)


def _generate_tailwind_theme_config(palette_key: str) -> str:
    """Generate Tailwind theme configuration snippet."""
    palette = DESIGN_SYSTEM["color_palettes"][palette_key]
    
    return f"""theme: {{
  extend: {{
    colors: {{
      primary: '{palette['primary']}',
      secondary: '{palette['secondary']}',
      accent: '{palette['accent']}',
      background: '{palette['background']}',
      surface: '{palette['surface']}',
    }},
    fontFamily: {{
      sans: ['Inter', 'system-ui', 'sans-serif'],
    }},
  }},
}},"""


if __name__ == "__main__":
    mcp.run(transport='stdio')
