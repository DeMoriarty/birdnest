from PIL import Image
from components import process
from util import upscale_to_300_dpi

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <image_path>")
        sys.exit(1)
    
    # Get image path from command-line argument
    image_path = sys.argv[1]
    try:
        # Load the image
        image = Image.open(image_path)
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
        exit()
    
    # Detect lines
    # image = upscale_to_300_dpi(image)
    image, s, article = process(image)
    print(article.as_str())
    print(s.as_str())
    print(s)
    image.show()