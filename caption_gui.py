"""
Gradio GUI for the Caption Generator Script.
Provides a user-friendly interface for configuring and running the image captioning process.
"""

import gradio as gr
import yaml
import os
import threading, subprocess
import time
import sys
import asyncio
from io import StringIO
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from hints.registration import get_available_hint_sources, get_hint_source_descriptions


class CaptionGUI:
    def __init__(self):
        self.config_file = "caption.yaml"
        self.current_process = None
        self.stop_requested = False
        self.current_config = {}
        
    def load_yaml_config(self) -> str:
        """Load the current YAML configuration file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Also load into current_config for form population
                self.current_config = yaml.safe_load(content) or {}
                return content
        except FileNotFoundError:
            self.current_config = {}
            return "# Configuration file not found - please create caption.yaml"
        except Exception as e:
            self.current_config = {}
            return f"# Error loading configuration: {str(e)}"
    
    def save_yaml_config(self, yaml_content: str) -> Tuple[str, str]:
        """Save YAML configuration and return status message and updated content."""
        try:
            # Validate YAML syntax
            parsed = yaml.safe_load(yaml_content)
            if parsed is None:
                return "⚠️ Warning: YAML file is empty", yaml_content
            
            # Save to file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            return "✅ Configuration saved successfully!", yaml_content
        except yaml.YAMLError as e:
            return f"❌ YAML Syntax Error: {str(e)}", yaml_content
        except Exception as e:
            return f"❌ Error saving configuration: {str(e)}", yaml_content
    
    def get_current_hint_sources(self) -> List[str]:
        """Get currently enabled hint sources from YAML config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('hint_sources', [])
        except:
            return []
    
    def update_hint_sources_in_yaml(self, yaml_content: str, selected_hints: List[str]) -> str:
        """Update the hint_sources section in YAML content."""
        try:
            config = yaml.safe_load(yaml_content)
            if config is None:
                config = {}
            
            config['hint_sources'] = selected_hints
            
            # Convert back to YAML string
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return yaml_content  # Return original if update fails
    
    def update_base_directory_in_yaml(self, yaml_content: str, directory: str) -> str:
        """Update the base_directory in YAML content."""
        try:
            config = yaml.safe_load(yaml_content)
            if config is None:
                config = {}
            
            config['base_directory'] = directory
            
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return yaml_content
    
    def update_recursive_in_yaml(self, yaml_content: str, recursive: bool) -> str:
        """Update the recursive setting in YAML content."""
        try:
            config = yaml.safe_load(yaml_content)
            if config is None:
                config = {}
            
            config['recursive'] = recursive
            
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return yaml_content
    
    def update_config_field_in_yaml(self, yaml_content: str, field_name: str, value) -> str:
        """Generic method to update any config field in YAML content."""
        try:
            config = yaml.safe_load(yaml_content)
            if config is None:
                config = {}
            
            config[field_name] = value
            
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return yaml_content
    
    def get_current_base_directory(self) -> str:
        """Get current base directory from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('base_directory', '')
        except:
            return ''
    
    def get_current_recursive_setting(self) -> bool:
        """Get current recursive setting from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('recursive', False)
        except:
            return False
    
    def get_current_base_url(self) -> str:
        """Get current base URL from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('base_url', '')
        except:
            return ''
    
    def get_current_model(self) -> str:
        """Get current model from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('model', '')
        except:
            return ''
    
    def get_current_max_tokens(self) -> int:
        """Get current max_tokens from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('max_tokens', 16384)
        except:
            return 16384
    
    def get_current_system_prompt(self) -> str:
        """Get current system prompt from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('system_prompt', '')
        except:
            return ''
    
    def get_current_global_metadata_file(self) -> str:
        """Get current global metadata file from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('global_metadata_file', '')
        except:
            return ''
    
    def get_current_prompts(self) -> List[str]:
        """Get current prompts list from config."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('prompts', [])
        except:
            return []
    
    def run_caption_script(self):
        """Run the caption script in a subprocess and stream its stdout."""
        if not os.path.exists(self.config_file):
            yield "❌ Error: caption.yaml not found. Please save your configuration first."
            return

        # Validate configuration file
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            base_dir = config.get("base_directory")
            if not base_dir:
                yield "❌ Error: base_directory not set in configuration."
                return
            if not os.path.exists(base_dir):
                yield f"❌ Error: Directory '{base_dir}' does not exist."
                return
        except Exception as e:
            yield f"❌ Error validating configuration: {str(e)}"
            return

        # Reset stop flag and current process
        self.stop_requested = False
        self.current_process = None

        output_buffer: List[str] = []

        def reader():
            """Read lines from the subprocess and push them to the buffer."""
            try:
                # Use the same interpreter to preserve the active virtual environment
                cmd = [sys.executable, "-u", "-m", "caption_openai"]
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                # Continuously read stdout
                for line in self.current_process.stdout:
                    if self.stop_requested:
                        break
                    if line.rstrip():
                        output_buffer.append(line.rstrip())

                # Wait for the subprocess to finish
                self.current_process.wait()
                if self.current_process.returncode == 0:
                    output_buffer.append("✅ Caption generation completed successfully!")
                else:
                    output_buffer.append(f"❌ Process exited with code {self.current_process.returncode}")

            except Exception as e:
                output_buffer.append(f"❌ Error running script: {str(e)}")
            finally:
                self.current_process = None
        # Start reader thread
        t = threading.Thread(target=reader, daemon=True)
        t.start()

        last_len = 0
        # Stream output as it arrives
        while t.is_alive():
            if len(output_buffer) > last_len:
                yield "\n".join(output_buffer)
                last_len = len(output_buffer)
            time.sleep(0.3)

        # Final flush
        yield "\n".join(output_buffer) if output_buffer else "No output received."
    
    def stop_caption_script(self) -> str:
        """Request to stop the currently running caption script."""
        if self.current_process and self.current_process.poll() is None:
            self.stop_requested = True
            try:
                self.current_process.terminate()  # Graceful termination
            except Exception:
                pass
            return "🛑 Stop requested – terminating process..."
        return "ℹ️ No running process to stop."
    
    def create_interface(self):
        """Create and return the Gradio interface."""
        available_hints = get_available_hint_sources()
        hint_descriptions = get_hint_source_descriptions()
        
        with gr.Blocks(title="Caption Generator GUI", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🖼️ Image Caption Generator")
            gr.Markdown("Configure and run the image captioning script with an easy-to-use interface.")
            
            with gr.Tabs():
                # Configuration Tab
                with gr.TabItem("📝 Configuration"):
                    
                    with gr.Tabs():
                        # Form Configuration Sub-tab
                        with gr.TabItem("🔧 Settings"):
                            gr.Markdown("## Basic API Settings")
                            
                            with gr.Row():
                                base_url_input = gr.Textbox(
                                    label="Base URL",
                                    value=self.get_current_base_url(),
                                    placeholder="http://localhost:1234/v1",
                                    info="API endpoint URL",
                                    scale=2
                                )
                                
                                model_input = gr.Textbox(
                                    label="Model",
                                    value=self.get_current_model(),
                                    placeholder="gemma-3-27b-it",
                                    info="Model name/identifier",
                                    scale=2
                                )
                                
                                max_tokens_input = gr.Number(
                                    label="Max Tokens",
                                    value=self.get_current_max_tokens(),
                                    minimum=1,
                                    maximum=32768,
                                    step=1,
                                    info="Maximum tokens for model response",
                                    scale=1
                                )
                            
                            gr.Markdown("## File Settings")
                            
                            with gr.Row():
                                global_metadata_input = gr.Textbox(
                                    label="Global Metadata File",
                                    value=self.get_current_global_metadata_file(),
                                    placeholder="character_info.txt",
                                    info="Path to global metadata file (optional)",
                                    scale=1
                                )
                                
                                base_dir = gr.Textbox(
                                    label="Base Directory",
                                    value=self.get_current_base_directory(),
                                    placeholder="Path to directory containing images",
                                    info="Directory to search for images",
                                    scale=2
                                )
                                
                                recursive_check = gr.Checkbox(
                                    label="Recursive Search",
                                    value=self.get_current_recursive_setting(),
                                    info="Search subdirectories recursively"
                                )
                            
                            gr.Markdown("## System Prompt")
                            
                            system_prompt_input = gr.Textbox(
                                label="System Prompt",
                                value=self.get_current_system_prompt(),
                                lines=4,
                                placeholder="You are to analyze an image and provide information...",
                                info="System-level instructions for the AI model"
                            )
                            
                            gr.Markdown("## Prompts Configuration")
                            gr.Markdown("Configure the sequence of prompts sent to the model:")
                            
                            # Dynamic prompts section
                            current_prompts = self.get_current_prompts()
                            prompt_components = []
                            
                            # Create initial prompt inputs
                            for i, prompt in enumerate(current_prompts):
                                prompt_components.append(gr.Textbox(
                                    label=f"Prompt {i+1}",
                                    value=prompt,
                                    lines=2,
                                ))
                            
                            # If no prompts exist, create one empty one
                            if not prompt_components:
                                prompt_components.append(gr.Textbox(
                                    label="Prompt 1",
                                    value="",
                                    lines=3,
                                    info="Prompt step 1"
                                ))
                            
                            with gr.Row():
                                add_prompt_btn = gr.Button("➕ Add Prompt", size="sm")
                                remove_prompt_btn = gr.Button("➖ Remove Last Prompt", size="sm")
                            
                            gr.Markdown("## Hint Sources")
                            gr.Markdown("Select which hint sources to enable:")
                            
                            current_hints = self.get_current_hint_sources()
                            hint_checkboxes = {}
                            
                            # Organize hint sources in columns for better layout
                            with gr.Row():
                                for hint_key, hint_name in available_hints.items():
                                    description = hint_descriptions.get(hint_key, "")
                                    hint_checkboxes[hint_key] = gr.Checkbox(
                                        label=hint_name,
                                        value=hint_key in current_hints,
                                        info=description
                                    )
                        
                        # YAML Editor Sub-tab
                        with gr.TabItem("📝 YAML Editor"):
                            gr.Markdown("## YAML Configuration")
                            gr.Markdown("Edit your caption.yaml configuration file directly:")
                            
                            yaml_editor = gr.Code(
                                label="Configuration (YAML)",
                                value=self.load_yaml_config(),
                                language="yaml",
                                lines=25
                            )
                            
                            with gr.Row():
                                save_btn = gr.Button("💾 Save Configuration", variant="primary")
                                reload_btn = gr.Button("🔄 Reload from File")
                                sync_from_form_btn = gr.Button("🔄 Sync from Form", variant="secondary")
                            
                            config_status = gr.Textbox(
                                label="Status",
                                interactive=False,
                                max_lines=2
                            )
                
                # Execution Tab
                with gr.TabItem("▶️ Run Caption Generator"):
                    gr.Markdown("## Execute Caption Generation")
                    
                    with gr.Row():
                        run_btn = gr.Button("🚀 Start Caption Generation", variant="primary", scale=2)
                        stop_btn = gr.Button("🛑 Stop", variant="stop", scale=1)
                    
                    output_display = gr.Textbox(
                        label="Output",
                        lines=20,
                        max_lines=25,
                        interactive=False,
                        info="Live output from the caption generation process"
                    )
                    
                    gr.Markdown("### Status")
                    status_display = gr.Textbox(
                        label="Process Status",
                        interactive=False,
                        max_lines=2
                    )
                
                # Help Tab
                with gr.TabItem("❓ Help"):

                    gr.Markdown("## Usage Instructions")
                    gr.Markdown("""
                    1. **Configure**: Edit the YAML configuration in the Configuration tab
                    2. **Set Directory**: Specify the base directory containing your images
                    3. **Select Hints**: Choose which hint sources to enable
                    4. **Save**: Save your configuration before running
                    5. **Run**: Execute the caption generation process
                    6. **Monitor**: Watch the live output for progress and results
                    """)
                    gr.Markdown("## Available Hint Sources")
                    
                    for hint_key, hint_name in available_hints.items():
                        description = hint_descriptions.get(hint_key, "No description available")
                        gr.Markdown(f"### {hint_name} (`{hint_key}`)")
                        gr.Markdown(description)
                        gr.Markdown("---")
                    
            
            # Event handlers
            def save_config_handler(yaml_content):
                status, updated_content = self.save_yaml_config(yaml_content)
                return status, updated_content
            
            def reload_config_handler():
                content = self.load_yaml_config()
                return content, "🔄 Configuration reloaded from file"
            
            def sync_from_form_handler(base_url, model, max_tokens, global_metadata, base_directory, 
                                     recursive, system_prompt, *args):
                """Sync configuration from form inputs to YAML"""
                try:
                    # Extract prompts from args (they come after hint values)
                    num_hints = len(hint_checkboxes)
                    hint_values = args[:num_hints]
                    prompt_values = args[num_hints:]
                    
                    # Build config from form inputs
                    config = {
                        'base_url': base_url,
                        'model': model,
                        'max_tokens': int(max_tokens) if max_tokens else 16384,
                        'global_metadata_file': global_metadata,
                        'base_directory': base_directory,
                        'recursive': recursive,
                        'system_prompt': system_prompt,
                        'prompts': [p.strip() for p in prompt_values if p.strip()],
                        'hint_sources': [hint_key for i, hint_key in enumerate(hint_checkboxes.keys()) if hint_values[i]]
                    }
                    
                    # Add the fixed api_key_env_vars from existing config
                    try:
                        with open(self.config_file, 'r', encoding='utf-8') as f:
                            existing_config = yaml.safe_load(f) or {}
                            if 'api_key_env_vars' in existing_config:
                                config['api_key_env_vars'] = existing_config['api_key_env_vars']
                            if 'api_key' in existing_config:
                                config['api_key'] = existing_config['api_key']
                    except:
                        # Use defaults if file doesn't exist
                        config['api_key_env_vars'] = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'MY_API_KEY_ENV_VAR_NAME']
                        config['api_key'] = ""
                    
                    yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
                    return yaml_content
                except Exception as e:
                    return f"# Error syncing from form: {str(e)}"
            
            def update_yaml_with_hints(*hint_values):
                # Get selected hints
                selected_hints = []
                for i, (hint_key, checkbox) in enumerate(hint_checkboxes.items()):
                    if hint_values[i]:  # If checkbox is checked
                        selected_hints.append(hint_key)
                
                # Update YAML content
                current_yaml = yaml_editor.value if hasattr(yaml_editor, 'value') else self.load_yaml_config()
                updated_yaml = self.update_hint_sources_in_yaml(current_yaml, selected_hints)
                return updated_yaml
            
            def update_yaml_with_field(yaml_content, field_name, value):
                return self.update_config_field_in_yaml(yaml_content, field_name, value)
            
            # Bind events
            save_btn.click(
                save_config_handler,
                inputs=[yaml_editor],
                outputs=[config_status, yaml_editor]
            )
            
            reload_btn.click(
                reload_config_handler,
                outputs=[yaml_editor, config_status]
            )
            
            # Sync from form to YAML
            all_form_inputs = [
                base_url_input, model_input, max_tokens_input, global_metadata_input,
                base_dir, recursive_check, system_prompt_input
            ] + list(hint_checkboxes.values()) + prompt_components
                
            sync_from_form_btn.click(
                sync_from_form_handler,
                inputs=all_form_inputs,
                outputs=[yaml_editor]
            )
            
            # Update YAML when form fields change
            base_url_input.change(
                lambda yaml_content, value: update_yaml_with_field(yaml_content, 'base_url', value),
                inputs=[yaml_editor, base_url_input],
                outputs=[yaml_editor]
            )
            
            model_input.change(
                lambda yaml_content, value: update_yaml_with_field(yaml_content, 'model', value),
                inputs=[yaml_editor, model_input],
                outputs=[yaml_editor]
            )
            
            max_tokens_input.change(
                lambda yaml_content, value: update_yaml_with_field(yaml_content, 'max_tokens', int(value) if value else 16384),
                inputs=[yaml_editor, max_tokens_input],
                outputs=[yaml_editor]
            )
            
            global_metadata_input.change(
                lambda yaml_content, value: update_yaml_with_field(yaml_content, 'global_metadata_file', value),
                inputs=[yaml_editor, global_metadata_input],
                outputs=[yaml_editor]
            )
            
            system_prompt_input.change(
                lambda yaml_content, value: update_yaml_with_field(yaml_content, 'system_prompt', value),
                inputs=[yaml_editor, system_prompt_input],
                outputs=[yaml_editor]
            )
            
            # Update YAML when hint checkboxes change
            for checkbox in hint_checkboxes.values():
                checkbox.change(
                    update_yaml_with_hints,
                    inputs=list(hint_checkboxes.values()),
                    outputs=[yaml_editor]
                )
            
            # Update YAML when directory changes
            base_dir.change(
                lambda yaml_content, directory: self.update_base_directory_in_yaml(yaml_content, directory),
                inputs=[yaml_editor, base_dir],
                outputs=[yaml_editor]
            )
            
            # Update YAML when recursive setting changes
            recursive_check.change(
                lambda yaml_content, recursive: self.update_recursive_in_yaml(yaml_content, recursive),
                inputs=[yaml_editor, recursive_check],
                outputs=[yaml_editor]
            )
            
            # Update YAML when prompts change
            def update_prompts_in_yaml(yaml_content, *prompt_values):
                prompts = [p.strip() for p in prompt_values if p.strip()]
                return self.update_config_field_in_yaml(yaml_content, 'prompts', prompts)
            
            for prompt_input in prompt_components:
                prompt_input.change(
                    update_prompts_in_yaml,
                    inputs=[yaml_editor] + prompt_components,
                    outputs=[yaml_editor]
                )
            
            # Add/Remove prompt functionality
            def add_prompt_handler():
                return "ℹ️ To add prompts: Edit the YAML directly or use 'Sync from Form' after adding text to existing prompt fields"
            
            def remove_prompt_handler():
                return "ℹ️ To remove prompts: Clear the content and use 'Sync from Form', or edit the YAML directly"
            
            add_prompt_btn.click(
                add_prompt_handler,
                outputs=[config_status]
            )
            
            remove_prompt_btn.click(
                remove_prompt_handler,
                outputs=[config_status]
            )
            
            # Run script
            run_btn.click(
                self.run_caption_script,
                outputs=[output_display]
            )
            
            # Stop script
            stop_btn.click(
                self.stop_caption_script,
                outputs=[status_display]
            )
        
        return interface


def main():
    """Main entry point for the GUI application."""
    app = CaptionGUI()
    interface = app.create_interface()
    
    print("🚀 Starting Caption Generator GUI...")
    print("📝 The GUI will be available at: http://localhost:7860")
    print("🔧 Make sure caption.yaml is configured before running the generator.")
    
    interface.launch(
        server_name="0.0.0.0",  # Allow access from other machines
        server_port=7860,
        share=False,  # Set to True to create a public link
        show_error=True
    )


if __name__ == "__main__":
    main()
