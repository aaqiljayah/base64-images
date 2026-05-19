"""
fix_base64_images.py
====================
Replace base64-encoded images embedded in an HTML file's JavaScript wine/product
data objects with lightweight relative file paths.

Useful when you've generated an HTML file that inlines images as base64 strings,
making the file bloated (often tens of MBs). This script swaps those strings out
for local file references so the HTML stays small and images load from disk.

Usage
-----
Run interactively (prompts you for all inputs):
    python fix_base64_images.py

Or supply arguments directly:
    python fix_base64_images.py \
        --input  path/to/input.html \
        --output path/to/output.html \
        --images-dir "Wine Images" \
        --map    map.json

See README.md for the map.json format and more details.
"""

import re
import os
import sys
import json
import argparse


# ── DEFAULT IMAGE MAP ──────────────────────────────────────────────────────
# Edit this dict OR supply an external JSON file via --map.
# Keys   = product names as they appear in the HTML's JS objects
# Values = image filenames inside your images directory
DEFAULT_IMAGE_MAP: dict[str, str] = {
    # "Product Name": "filename.jpeg",
}
# ──────────────────────────────────────────────────────────────────────────


def load_map(map_path: str) -> dict[str, str]:
    """Load an image map from a JSON file."""
    with open(map_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Map file must be a JSON object (key/value pairs).")
    return data


def replace_base64_with_paths(html: str, image_map: dict[str, str], images_dir: str):
    """
    Scan the HTML for JS object blocks that contain:
        name: "Some Product Name"
        img:  "data:image/...base64..."
    and replace the base64 img value with a relative file path.

    Returns (new_html, replaced_count, not_found_names)
    """
    not_found: list[str] = []
    counter = [0]

    def replacer(match: re.Match) -> str:
        full_match = match.group(0)
        product_name = match.group(1)

        # Case-insensitive substring match against the map keys
        img_file = None
        for key, filename in image_map.items():
            if key.lower() in product_name.lower() or product_name.lower() in key.lower():
                img_file = filename
                break

        if not img_file:
            not_found.append(product_name)
            return full_match  # leave unchanged

        counter[0] += 1
        new_path = f"{images_dir}/{img_file}".replace("\\", "/")
        result = re.sub(r'(img\s*:\s*")[^"]*(")', rf'\g<1>{new_path}\2', full_match)
        return result

    # Match each JS object block that has both a name and a base64 img field
    pattern = r'\{[^}]*name\s*:\s*"([^"]+)"[^}]*img\s*:\s*"data:image/[^"]*"[^}]*\}'
    new_html = re.sub(pattern, replacer, html, flags=re.DOTALL)
    return new_html, counter[0], not_found


def prompt_input(label: str, default: str = "") -> str:
    """Prompt the user for a value, showing an optional default."""
    if default:
        value = input(f"{label} [{default}]: ").strip()
        return value if value else default
    value = input(f"{label}: ").strip()
    return value


def run_interactive() -> argparse.Namespace:
    """Collect all required inputs interactively from the terminal."""
    print("\n=== fix_base64_images (interactive mode) ===\n")
    args = argparse.Namespace()
    args.input      = prompt_input("Input HTML file path")
    args.output     = prompt_input("Output HTML file path", args.input.replace(".html", "_fixed.html"))
    args.images_dir = prompt_input("Images directory (relative path used in HTML)", "images")
    map_path        = prompt_input("Path to JSON image map file (leave blank to use DEFAULT_IMAGE_MAP)", "")
    args.map        = map_path if map_path else None
    return args


def main():
    parser = argparse.ArgumentParser(
        description="Replace base64 images in an HTML file with local file paths.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input",      "-i", help="Path to the input HTML file.")
    parser.add_argument("--output",     "-o", help="Path for the fixed output HTML file.")
    parser.add_argument("--images-dir", "-d", default="images",
                        help="Relative directory path used in the HTML for images (default: 'images').")
    parser.add_argument("--map",        "-m", help="Path to a JSON file mapping product names to image filenames.")

    args = parser.parse_args()

    # Fall back to interactive mode if required args are missing
    if not args.input or not args.output:
        args = run_interactive()

    # ── Validate input file ────────────────────────────────────────────────
    if not os.path.isfile(args.input):
        sys.exit(f"Error: input file not found: {args.input}")

    # ── Load image map ─────────────────────────────────────────────────────
    if args.map:
        if not os.path.isfile(args.map):
            sys.exit(f"Error: map file not found: {args.map}")
        image_map = load_map(args.map)
        print(f"Loaded {len(image_map)} entries from {args.map}")
    elif DEFAULT_IMAGE_MAP:
        image_map = DEFAULT_IMAGE_MAP
        print(f"Using built-in DEFAULT_IMAGE_MAP ({len(image_map)} entries).")
    else:
        sys.exit(
            "Error: no image map provided.\n"
            "Either edit DEFAULT_IMAGE_MAP in the script, or supply a --map JSON file.\n"
            "See README.md for the expected format."
        )

    # ── Read input ─────────────────────────────────────────────────────────
    print(f"\nReading: {args.input}")
    with open(args.input, "r", encoding="utf-8") as f:
        html = f.read()
    print(f"File size: {len(html) / 1024 / 1024:.2f} MB")

    # ── Process ────────────────────────────────────────────────────────────
    print("Replacing base64 images with file paths...")
    new_html, count, not_found = replace_base64_with_paths(html, image_map, args.images_dir)
    print(f"New file size:  {len(new_html) / 1024 / 1024:.2f} MB")

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\n✓ Replaced {count} image(s) successfully.")
    if not_found:
        print(f"\n⚠  Could not find image mapping for {len(not_found)} product(s):")
        for name in not_found:
            print(f"   - {name}")
        print(
            "\n  To fix this, add the missing entries to your map file (or DEFAULT_IMAGE_MAP)\n"
            '  e.g.  "Product Name Here": "product-image.jpeg"'
        )

    # ── Write output ───────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"\nFixed HTML saved to:\n  {args.output}")


if __name__ == "__main__":
    main()
