# Hint Sources

"Hint" sources provide additional metadata or context by reading data alongside the image. 

When hint sources are configured, the output is automatically added to the beginning of your first prompt, providing the VLM with contextual information before it analyzes the image. This can improve caption accuracy and consistency.

This is particularly powerful if you have images that are already categorized or if you have metadata ahead of time, such as webscrape information. The system is easily extensible for even amateur developers.

## Configuration

Enable hint sources in your `caption.yaml` file:

```yaml
hint_sources:
  - "full_path"
  - "metadata"
  - "json"
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

This is useful if you have prepared your data into directories with names that are meaningful. Modern VLM models are pretty smart about ignoring the irrelevant parts of the filename such as mount location, drive letter, or random numbered files or folders.

### - metadata

**Purpose**: Reads **directory-level** metadata from `metadata.json` files and includes it as context.

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
- Provide directory-wide metadata without the constraints of the length of the directory name
- Very useful if you are capturing metadata while web scraping, or have organized your data at a folder level. Drop a metadata.json file into the folder with relevant information about all the images in a given directory.

```
    c:/myimages/mortal kombat/metadata.json
    c:/myimages/mortal kombat/scorpion.webp
    c:/myimages/mortal kombat/...
    c:/myimages/resident evil/metadata.json
    c:/myimages/resident evil/leon.png
    c:/myimages/resident evil/...
```

**Configuration**: Add `"metadata"` to your `hint_sources` list.

### - json

Looks for a .json file with the same directory and basename as each image file. 

This is similar to above metadata but on a **per-image** basis. If you write webscrapers this is particular useful since you can save metadata (title, header, alt-text) as you go

## Extensibility

Developers can easily add new hint sources by:

1. Adding a new function to `registration.py` following the naming pattern `get_[source_name]_hint()`
2. Registering the function in the functions at the bottom with descriptons that are used in the GUI and correlate your hint "name" with the actual python function
3. Adding the "name" you chose to the `caption.yaml`

Use the existing hints as a guide on how to write them.

Each hint function receives the image path and can return formatted text that will be prepended to the first prompt. 

These are generally simple enough that an LLM can write them for you if you just paste the entire `registration.py` file in and tell it you want a new one and what you want it to do.

### Performance Considerations

- Hint sources are processed synchronously before the first API call for a given image
- Consider keeping hints relatively lightweight to avoid adding slowing the captioning process
- Guard against failure cases (missing data source, etc)

## Error Handling

If a configured hint source fails to execute:
- A warning message is printed to the console
- Processing continues with remaining hint sources
- The main captioning process is not interrupted

## Test

You can run `python test_hints.py` to smoke test registration.  It won't catch all errors but will at least error if partially registered. This test script does not and should not be modified as part of adding a new hint source.