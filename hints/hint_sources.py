"""
Hint sources module for providing additional context to image captioning prompts.
Each hint source can provide specific information that gets prepended to the first prompt.
"""

from typing import List, Optional
from .registration import HINT_FUNCTIONS


def get_hints(hint_sources_config: List[str], image_path: str, **kwargs) -> Optional[str]:
    """
    Main function to collect all hints based on configuration.
    
    Args:
        hint_sources_config: List of hint source names from configuration
        image_path: Path to the image being processed
        **kwargs: Additional parameters for hint sources
        
    Returns:
        Combined hint text to prepend to the first prompt, or None if no hints
    """
    if not hint_sources_config:
        return None
        
    hints = []
    
    # Use the centralized hint functions registry
    for hint_source in hint_sources_config:
        if hint_source in HINT_FUNCTIONS:
            try:
                hint_text = HINT_FUNCTIONS[hint_source](image_path, **kwargs)
                if hint_text:
                    hints.append(hint_text)
            except Exception as e:
                print(f"Warning: Failed to get hint from '{hint_source}': {e}")
        else:
            print(f"Warning: Unknown hint source '{hint_source}' - skipping")
    
    if hints:
        return "\n".join(hints)
    return None
