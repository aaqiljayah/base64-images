# fix_base64_images

A small Python utility that replaces inline base64-encoded images in an HTML file's JavaScript data objects with lightweight relative file paths.

## The Problem

When generating HTML files that embed product/item data directly as JavaScript objects, images are sometimes stored as base64 strings:

```js
{ name: "Some Wine", img: "data:image/jpeg;base64,/9j/4AAQSkZJRgAB..." }
```

This bloats the HTML file — often to **tens of megabytes** — making it slow to load and painful to version-control. This script swaps those strings out for simple file paths:

```js
{ name: "Some Wine", img: "images/some-wine.jpeg" }
```

---

## Requirements

- Python 3.7+
- No third-party dependencies (standard library only)

---

## Usage

### Interactive mode

Run the script with no arguments and it will prompt you for everything:

```bash
python fix_base64_images.py
```

### Command-line mode

```bash
python fix_base64_images.py \
  --input  path/to/input.html \
  --output path/to/output_fixed.html \
  --images-dir "images" \
  --map map.json
```

| Flag | Short | Description |
|------|-------|-------------|
| `--input` | `-i` | Path to the HTML file you want to fix |
| `--output` | `-o` | Where to write the fixed HTML (defaults to `<input>_fixed.html`) |
| `--images-dir` | `-d` | The relative directory path used in the HTML to reference images (default: `images`) |
| `--map` | `-m` | Path to a JSON file mapping product names → image filenames |

---

## Image Map

The script needs to know which image file corresponds to which product name. You can provide this in two ways:

### Option A — JSON file (recommended)

Create a `map.json` file:

```json
{
  "Product Name One": "product-one.jpeg",
  "Another Product":  "another-product.png",
  "Yet Another":      "yet-another.jpg"
}
```

Then pass it with `--map map.json`.

### Option B — Edit the script directly

Open `fix_base64_images.py` and fill in the `DEFAULT_IMAGE_MAP` dict near the top:

```python
DEFAULT_IMAGE_MAP = {
    "Product Name One": "product-one.jpeg",
    "Another Product":  "another-product.png",
}
```

### Matching behaviour

Name matching is **case-insensitive and partial** — the map key just needs to appear somewhere in the product name from the HTML (or vice versa). So `"Pinot Grigio"` in your map will match `"Casa Del Vino Pinot Grigio Reserve"` in the HTML.

---

## Example

**Before** (`input.html`, ~18 MB):
```js
{ name: "Trivento Reserve Malbec", img: "data:image/jpeg;base64,/9j/4AAQ..." }
```

**After** (`output_fixed.html`, ~42 KB):
```js
{ name: "Trivento Reserve Malbec", img: "images/trivento-reserve-malbec.jpeg" }
```

---

## Expected HTML structure

The script looks for JavaScript object literals that contain both a `name` field and an `img` field with a base64 data URI:

```js
{
  name: "Product Name",
  img: "data:image/jpeg;base64,..."
}
```

If your HTML uses a different structure (e.g. `title` instead of `name`, or `src` instead of `img`), you'll need to tweak the regex pattern in `replace_base64_with_paths()`.

---

## Project structure

```
fix_base64_images.py   ← the script
map.json               ← your image map (you create this)
images/                ← your image files (you provide these)
  product-one.jpeg
  product-two.jpeg
  ...
```

---

## License

MIT — do whatever you like with it.
