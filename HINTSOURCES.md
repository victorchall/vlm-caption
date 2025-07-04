# Hint Sources

"Hint" sources provide additional metadata or context. 

When hint sources are configured, their output is automatically added to the beginning of your first prompt, providing the VLM with contextual information before it analyzes the image. This can improve caption accuracy and consistency.

This is particularly powerful if you have images that are already categorized or if you have metadata ahead of time, such as webscrape information. The system is easily extensible for even amateur developers.

## Configuration

Enable hint sources in your `caption.yaml` file:

```yaml
hint_sources:
  - "full_path"
  - "metadata"
```

Multiple hint sources can be enabled simultaneously. They will be combined and prepended to your first prompt in the order they appear in the configuration.

## Available Hint Sources

### - full_path

**Purpose**: Provides the complete file path and filename to the VLM.

**Output Format**:
```
Image file information:
- Full path: R:\games\final fantasy vii rebrith screenshots\cloud strife\image_001.png
```

This is useful if you have prepared your data into directories with names that are meaningful.

### - metadata

**Purpose**: Reads directory-level metadata from `metadata.json` files and includes it as context.

**How it Works**:
- Looks for a `metadata.json` file in the same directory as each image
- Metadata is cached to read each directory's metadata only once
- Adds nothing to prompt if no metadata.json exists
- Prints warnings if the metadata is malformed

**Output Format**:
```
Directory metadata:
- scene_type: outdoor
- characters: ["character1", "character2"]
- setting: forest clearing
- mood: cheerful
```

**Example metadata.json Structure**:
```json
{
  "scene_type": "outdoor",
  "characters": ["character1", "character2"],
  "setting": "forest clearing",
  "mood": "cheerful",
  "tags": ["nature", "adventure"]
}
```

**Use Cases**:
- Provide directory-wide metadata without the constraints of a directory name
- Very useful if you are capturing metadata while web scraping.

**Configuration**: Add `"metadata"` to your `hint_sources` list.

## Extensibility

Developers can easily add new hint sources by:

1. Adding a new function to `hint_sources.py` following the naming pattern `get_[source_name]_hint()`
2. Registering the function in the `hint_functions` dictionary
3. Adding the source name to the configuration

Each hint function receives the image path and can return formatted text that will be prepended to the first prompt.

These are generally simple enough that an LLM can write them for you.

### Performance Considerations

- Hint sources are processed synchronously before the first API call for a given image
- Keep hint processing lightweight to avoid delays

## Error Handling

If a configured hint source fails to execute:
- A warning message is printed to the console
- Processing continues with remaining hint sources
- The main captioning process is not interrupted

