# Remove the old buggy code that was trying to calculate tile_height before variables were definedimport os
import math
import colorsys
import os
from typing import List, Tuple
from PIL import Image


def get_dominant_color(img):
    """
    Get the dominant color of an image by resizing it to 1x1 pixel.

    Args:
        img (PIL.Image): Input image

    Returns:
        tuple: RGB color tuple
    """
    # Resize to 1x1 to get average color
    color = img.resize((1, 1)).getpixel((0, 0))
    return color if isinstance(color, tuple) else (color, color, color)


def rgb_to_hue(rgb):
    """
    Convert RGB color to HSV hue value for sorting.

    Args:
        rgb (tuple): RGB color tuple

    Returns:
        float: Hue value (0-1)
    """
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h


def calculate_average_aspect_ratio(covers_folder, cover_files):
    """
    Calculate the average aspect ratio of all cover images.

    Args:
        covers_folder (str): Path to folder containing cover images
        cover_files (list): List of cover filenames

    Returns:
        float: Average aspect ratio (width/height)
    """
    ratios = []

    print("Analyzing cover aspect ratios...")
    for i, cover_file in enumerate(cover_files):
        try:
            cover_path = os.path.join(covers_folder, cover_file)
            with Image.open(cover_path) as img:
                width, height = img.size
                ratio = width / height
                ratios.append(ratio)

            if (i + 1) % 20 == 0:
                print(f"Analyzed {i + 1}/{len(cover_files)} covers...")

        except Exception as e:
            print(f"Error analyzing {cover_file}: {e}")
            continue

    if ratios:
        avg_ratio = sum(ratios) / len(ratios)
        print(f"Average aspect ratio: {avg_ratio:.3f} (from {len(ratios)} covers)")
        return avg_ratio
    else:
        print("No valid ratios found, using default 0.75")
        return 0.75


def sort_covers_by_color(covers_folder, cover_files):
    """
    Sort cover files by their dominant color to create a gradient effect.

    Args:
        covers_folder (str): Path to folder containing cover images
        cover_files (list): List of cover filenames

    Returns:
        list: Sorted list of cover filenames
    """
    print("Analyzing cover colors for gradient sorting...")
    cover_colors = []

    for i, cover_file in enumerate(cover_files):
        try:
            cover_path = os.path.join(covers_folder, cover_file)
            with Image.open(cover_path) as img:
                # Get dominant color
                dominant_color = get_dominant_color(img)
                hue = rgb_to_hue(dominant_color)
                cover_colors.append((cover_file, hue))

            if (i + 1) % 20 == 0:
                print(f"Analyzed colors {i + 1}/{len(cover_files)} covers...")

        except Exception as e:
            print(f"Error analyzing color for {cover_file}: {e}")
            # Add with default hue if error
            cover_colors.append((cover_file, 0.0))
            continue

    # Sort by hue value to create color gradient
    cover_colors.sort(key=lambda x: x[1])
    sorted_covers = [cover_file for cover_file, _ in cover_colors]

    print("Covers sorted by color for gradient effect!")
    return sorted_covers
    """
    Resize and crop an image to fit the target dimensions while preserving aspect ratio.
    The image is scaled so that it completely fills the target area, then cropped if necessary.

    Args:
        img: Input image
        target_width: Target width
        target_height: Target height

    Returns:
        Resized and cropped image
    """
    original_width, original_height = img.size
    original_ratio = original_width / original_height
    target_ratio = target_width / target_height

    if original_ratio > target_ratio:
        # Image is wider than target ratio, scale by height and crop width
        new_height = target_height
        new_width = int(original_ratio * new_height)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop width (center crop)
        left = (new_width - target_width) // 2
        img = img.crop((left, 0, left + target_width, target_height))
    else:
        # Image is taller than target ratio, scale by width and crop height
        new_width = target_width
        new_height = int(new_width / original_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop height (center crop)
        top = (new_height - target_height) // 2
        img = img.crop((0, top, target_width, top + target_height))


def resize_and_crop_to_fit(img, target_width, target_height):
    return img


def create_cover_mosaic(covers_folder: str = "covers", output_file: str = "mosaic_wallpaper.jpg",
                        tile_width: int = 100, generation_mode: str = "flat") -> None:
    """
    Create a mosaic wallpaper from cover images in a folder.

    Args:
        covers_folder: Path to folder containing cover images
        output_file: Output filename for the mosaic
        tile_width: Width of each cover tile in pixels (height will be calculated from actual covers)
        generation_mode: "flat" for normal order, "colorful" for gradient color sorting
    """

    # Standard book cover aspect ratio (width:height = 3:4, or 0.75)
    book_ratio = 0.75
    tile_height = int(tile_width / book_ratio)  # Calculate height to maintain book proportions

    # Check if covers folder exists
    if not os.path.exists(covers_folder):
        print(f"Error: Folder '{covers_folder}' not found!")
        return

    # Get all jpg files from the covers folder
    cover_files = [f for f in os.listdir(covers_folder)
                   if f.lower().endswith(('.jpg', '.jpeg'))]

    if not cover_files:
        print(f"No JPG files found in '{covers_folder}' folder!")
        return

    print(f"Found {len(cover_files)} cover images")

    # Calculate average aspect ratio from all covers
    avg_ratio = calculate_average_aspect_ratio(covers_folder, cover_files)
    tile_height = int(tile_width / avg_ratio)

    # Sort covers based on generation mode
    if generation_mode.lower() == "colorful":
        cover_files = sort_covers_by_color(covers_folder, cover_files)
        print("Using colorful gradient mode")
    else:
        print("Using flat mode (original order)")

    # Remove the duplicate print statement that was causing confusion

    # Calculate grid dimensions for 16:9 aspect ratio
    num_covers = len(cover_files)
    screen_ratio = 16 / 9

    # Calculate optimal grid size considering actual cover tiles
    # We want (cols * tile_width) / (rows * tile_height) ≈ 16/9
    # This means cols/rows ≈ (16/9) * (tile_height/tile_width) = (16/9) * (1/avg_ratio)
    target_grid_ratio = screen_ratio / avg_ratio

    # Calculate optimal grid size
    cols = math.ceil(math.sqrt(num_covers * target_grid_ratio))
    rows = math.ceil(num_covers / cols)

    # Adjust to ensure we have enough space
    while cols * rows < num_covers:
        cols += 1

    print(f"Creating {cols}x{rows} grid ({cols * rows} total slots)")
    print(f"Each tile: {tile_width}x{tile_height} pixels (avg ratio: {avg_ratio:.3f})")

    # Calculate final image dimensions
    width = cols * tile_width
    height = rows * tile_height

    print(f"Final image size: {width}x{height} pixels")

    # Create the mosaic image
    mosaic = Image.new('RGB', (width, height), color='black')

    # Process each cover image
    for i, cover_file in enumerate(cover_files):
        try:
            # Calculate position in grid
            col = i % cols
            row = i // cols

            # Load and resize the cover image
            cover_path = os.path.join(covers_folder, cover_file)
            cover_img = Image.open(cover_path)

            # Resize while preserving aspect ratio and crop to fit book cover dimensions
            cover_img = resize_and_crop_to_fit(cover_img, tile_width, tile_height)

            # Calculate position to paste
            x = col * tile_width
            y = row * tile_height

            # Paste the cover onto the mosaic
            mosaic.paste(cover_img, (x, y))

            if (i + 1) % 50 == 0:  # Progress indicator
                print(f"Processed {i + 1}/{len(cover_files)} covers...")

        except Exception as e:
            print(f"Error processing {cover_file}: {e}")
            continue

    # Save the final mosaic
    print(f"Saving mosaic to {output_file}...")
    mosaic.save(output_file, 'JPEG', quality=95)
    print(f"Mosaic wallpaper created successfully!")
    print(f"Final dimensions: {width}x{height} pixels")
    print(f"Aspect ratio: {width / height:.2f} (target was {screen_ratio:.2f})")


def main() -> None:
    """Main function to run the script"""
    # You can customize these parameters
    covers_folder = "covers"  # Folder containing your cover images
    output_file = "mosaic_wallpaper.jpg"  # Output filename
    tile_width = 100  # Width of each cover in the mosaic (height calculated from actual covers)
    generation_mode = "flat"  # "flat" for normal order, "colorful" for gradient

    create_cover_mosaic(covers_folder, output_file, tile_width, generation_mode)


if __name__ == "__main__":
    main()