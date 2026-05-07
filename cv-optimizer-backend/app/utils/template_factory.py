import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

class TemplateFactory:
    """
    Modular Template System to generate 20+ professional CV styles.
    Combines Layout Engines with Design Tokens.
    """
    
    LAYOUTS = {
        "modern-1": "modern_sidebar.html",
        "modern-2": "modern_split.html",
        "classic-1": "classic_minimal.html",
        "executive-1": "executive_serif.html",
        "creative-1": "creative_gradient.html",
        "professional-1": "compact_professional.html",
        "standard-1": "two_column_standard.html",
        "minimal-1": "centered_modern.html",
        "vienna-1": "vienna_luxury.html",
        "tokyo-1": "tokyo_minimal.html"
    }
    
    COLORS = {
        "blue": "#2563eb",
        "slate": "#334155",
        "emerald": "#059669",
        "indigo": "#4f46e5",
        "rose": "#e11d48",
        "amber": "#d97706",
        "violet": "#7c3aed",
        "cyan": "#0891b2"
    }

    @classmethod
    def get_template_config(cls, template_id: str):
        """
        Parses a template ID like 'modern-1-blue' into its components.
        """
        parts = template_id.split("-")
        layout_key = f"{parts[0]}-{parts[1]}"
        color_key = parts[2] if len(parts) > 2 else "blue"
        
        return {
            "layout": cls.LAYOUTS.get(layout_key, "modern_sidebar.html"),
            "color": cls.COLORS.get(color_key, "#2563eb"),
            "id": template_id
        }

    @classmethod
    def render(cls, template_id: str, data: dict) -> str:
        config = cls.get_template_config(template_id)
        template = env.get_template(config["layout"])
        return template.render(data=data, config=config)

template_factory = TemplateFactory()
