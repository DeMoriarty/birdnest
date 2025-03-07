import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
# from spellchecker import SpellChecker

from components import process
from util import upscale_to_300_dpi

# Replace this with your image processing function
def process_image(image):
    # Your image processing logic here
    processed_image, s, tesserect_article = process(
        image, 
        indent_check=indent_check_var.get() > 0, 
        spell_check=spell_check_var.get() > 0, 
    )
    return processed_image, s.as_str()

def select_image():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.bmp")])
    if path:
        try:
            image = Image.open(path)
            original_size = image.size
            # image = upscale_to_300_dpi(image)
            # processed_image.resize(original_size, Image.LANCZOS)
            
            processed_image, processed_text = process_image(image)
            canvas.original_image = image  # Store original image
            canvas.processed_image = processed_image.copy()  # Store processed image
            update_image_display()  # Initial display
            display_text(processed_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process image: {e}")

def update_image_display(event=None):
    if not hasattr(canvas, 'original_image') or canvas.original_image is None:
        return
    if not hasattr(canvas, 'processed_image') or canvas.processed_image is None:
        canvas.processed_image = canvas.original_image.copy()
    canvas_width = event.width if event else canvas.winfo_width()
    processed_image = canvas.processed_image
    
    orig_w, orig_h = processed_image.size
    if orig_w == 0 or orig_h == 0:
        return
    scale = canvas_width / orig_w
    new_height = int(orig_h * scale)
    # Use Image.LANCZOS instead of Image.ANTIALIAS
    resized_image = processed_image.resize((canvas_width, new_height), Image.LANCZOS)
    photo = ImageTk.PhotoImage(resized_image)
    canvas.delete("all")
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo  # Keep reference
    canvas.displayed_image = resized_image  # Store for saving
    canvas.config(scrollregion=canvas.bbox(tk.ALL))

def display_text(text):
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, text)
    text_widget.config(state=tk.DISABLED)

def save_image():
    if hasattr(canvas, 'displayed_image'):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")], initialfile="processed.png")
        if path:
            try:
                canvas.displayed_image.save(path)
                # messagebox.showinfo("Success", "Image saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")
    else:
        messagebox.showwarning("Warning", "No image to save.")

def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def toggle_wrap():
    if wrap_var.get():
        text_widget.config(wrap=tk.WORD)  # Wrap text at word boundaries
    else:
        text_widget.config(wrap=tk.NONE)  # No wrapping, enables horizontal scroll

def toggle_checks():
    if not hasattr(canvas, 'original_image') or canvas.original_image is None:
        return
    new_image, _ = process_image(canvas.original_image)
    canvas.processed_image = new_image
    update_image_display()


# Initialize the main window
root = tk.Tk()
root.title("BirdNest")

indent_check_var = tk.IntVar(value=1)
spell_check_var = tk.IntVar(value=0)

# Button frame
button_frame = tk.Frame(root)
button_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Notebook for panels
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Image frame (first panel)
image_frame = tk.Frame(notebook)
canvas = tk.Canvas(image_frame, width=800, height=600)
scrollbar_y = tk.Scrollbar(image_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollbar_x = tk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=canvas.xview)
canvas.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
canvas.grid(row=0, column=0, sticky="nsew")
scrollbar_y.grid(row=0, column=1, sticky="ns")
scrollbar_x.grid(row=1, column=0, sticky="ew")
image_frame.grid_rowconfigure(0, weight=1)
image_frame.grid_columnconfigure(0, weight=1)
notebook.add(image_frame, text="Image")
canvas.bind("<Configure>", update_image_display)
canvas.bind("<MouseWheel>", on_mousewheel)
canvas.original_image = None

# Text frame (second panel)
text_frame = tk.Frame(notebook)
text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
scrollbar_text_y = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
scrollbar_text_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
text_widget.config(yscrollcommand=scrollbar_text_y.set, xscrollcommand=scrollbar_text_x.set)
text_widget.grid(row=0, column=0, sticky="nsew")
scrollbar_text_y.grid(row=0, column=1, sticky="ns")
scrollbar_text_x.grid(row=1, column=0, sticky="ew")
text_frame.grid_rowconfigure(0, weight=1)
text_frame.grid_columnconfigure(0, weight=1)
notebook.add(text_frame, text="Detected Text")

# About frame (third pannel)
about_frame = tk.Frame(notebook)
about_text = tk.Text(about_frame, wrap=tk.WORD, state=tk.NORMAL, font=("Rockwell", 11))
about_text.grid(row=0, column=0, sticky="nsew")
scrollbar_y = tk.Scrollbar(about_frame, orient=tk.VERTICAL, command=about_text.yview)
scrollbar_y.grid(row=0, column=1, sticky="ns")
about_text.config(yscrollcommand=scrollbar_y.set)
about_frame.grid_rowconfigure(0, weight=1)
about_frame.grid_columnconfigure(0, weight=1)
# about_frame.grid(row=0, column=0, sticky="nsew")
# about_frame.grid_rowconfigure(0, weight=1)
# about_frame.grid_columnconfigure(0, weight=1)
notebook.add(about_frame, text="About")
about = """
About BirdNest v1.0

Automatic indentation checking and spell checking for documents.

Developed by DeMoriarty
Email: sahbanjan@gmail.com

This tool may produce inaccurate results. The developer is not responsible for any errors, omissions, or damages arising from its use.

© 2025 DeMoriarty. All rights reserved.
"""
about_text.insert(tk.END, about)
about_text.config(state=tk.DISABLED)
# Add to notebook (only once)
notebook.add(about_frame, text="About")


# Buttons
select_button = tk.Button(button_frame, text="Select Image", command=select_image)
select_button.pack(side=tk.LEFT, padx=10, pady=10)
save_button = tk.Button(button_frame, text="Save Image", command=save_image)
save_button.pack(side=tk.LEFT, padx=10, pady=10)

# Wrap toggle checkbox
wrap_var = tk.IntVar(value=1)  # Default: wrap enabled
wrap_checkbox = tk.Checkbutton(button_frame, text="Wrap Text", variable=wrap_var, command=toggle_wrap)
wrap_checkbox.pack(side=tk.LEFT, padx=10, pady=10)
toggle_wrap()  # Set initial wrap state

# Wrap indent check
indent_check_checkbox = tk.Checkbutton(button_frame, text="Check Indent", variable=indent_check_var, command=toggle_checks)
indent_check_checkbox.pack(side=tk.LEFT, padx=10, pady=10)
toggle_checks()  # Set initial wrap state

# Wrap indent check
spell_check_checkbox = tk.Checkbutton(button_frame, text="Check Spelling", variable=spell_check_var, command=toggle_checks)
spell_check_checkbox.pack(side=tk.LEFT, padx=10, pady=10)
toggle_checks()  # Set initial wrap state


root.mainloop()