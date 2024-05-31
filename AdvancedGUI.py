import tkinter as tk
from tkinter import filedialog, messagebox, Canvas, Frame, Scrollbar
from threading import Thread
import os
import numpy as np
import glob
import imageio
import imagej
from PIL import Image, ImageTk

# Initialize ImageJ
ij = imagej.init('sc.fiji:fiji')


# Function to load cubes
def load_cubes_im3(data_path):
    cube_files = glob.glob(os.path.join(data_path, '*.im3'))
    cubes = {}
    for filepath in cube_files:
        img = ij.io().open(filepath)
        cube = np.array(ij.py.from_java(img))
        ex = os.path.basename(filepath)[:-4]
        cube_data = {
            'num_rows': cube.shape[0],
            'num_cols': cube.shape[1],
            'num_bands': cube.shape[2],
            'ex': ex,
            'data': cube,
        }
        cubes[os.path.basename(filepath)] = cube_data
    return cubes


# Function to combine cubes into RGB
def combine_cubes_to_rgb(cube_list):
    blue_bands = range(3, 9)
    green_bands = range(13, 19)
    red_bands = range(23, 29)

    combined_red = None
    combined_green = None
    combined_blue = None

    for cube in cube_list:
        red_data = np.mean(cube[:, :, red_bands], axis=-1)
        green_data = np.mean(cube[:, :, green_bands], axis=-1)
        blue_data = np.mean(cube[:, :, blue_bands], axis=-1)

        if combined_red is None:
            combined_red = np.zeros_like(red_data)
            combined_green = np.zeros_like(green_data)
            combined_blue = np.zeros_like(blue_data)

        combined_red += red_data
        combined_green += green_data
        combined_blue += blue_data

    normalized_red = (combined_red - np.min(combined_red)) / (np.max(combined_red) - np.min(combined_red))
    normalized_green = (combined_green - np.min(combined_green)) / (np.max(combined_green) - np.min(combined_green))
    normalized_blue = (combined_blue - np.min(combined_blue)) / (np.max(combined_blue) - np.min(combined_blue))

    rgb_image = np.stack([normalized_red, normalized_green, normalized_blue], axis=-1)
    rgb_image_uint8 = (rgb_image * 255).astype(np.uint8)

    return rgb_image_uint8


class IM3AnalyzerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IM3 Analyzer")
        self.geometry("1000x700")  # Increased height to accommodate the thick part

        self.cubes = {}
        self.current_rgb_image = None
        self.current_selected_files = None
        self.check_vars = {}

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.files_panel = tk.Frame(self.main_frame, width=150, bd=2, relief="solid", bg="lightgray")
        self.files_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.directory_frame = tk.Frame(self.files_panel, bg="lightgray")
        self.directory_frame.pack(pady=10)

        self.dir_label = tk.Label(self.directory_frame, text="IM3 Files Directory:", bg="lightgray")
        self.dir_label.pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(self.directory_frame, width=30)
        self.dir_entry.pack(side=tk.LEFT, padx=10)

        self.load_button = tk.Button(self.directory_frame, text="Load", command=self.start_load_directory)
        self.load_button.pack(side=tk.LEFT)

        self.files_frame = tk.Frame(self.files_panel, bg="lightgray")
        self.files_frame.pack(fill=tk.BOTH, expand=True)

        # Create a canvas with a scrollbar
        self.canvas = Canvas(self.files_frame, bg="lightgray")
        self.scrollbar = Scrollbar(self.files_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg="lightgray")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.display_panel = tk.Frame(self.main_frame, bd=2, relief="solid", bg="white")
        self.display_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.image_canvas = Canvas(self.display_panel, bg="white")
        self.image_canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom part of the display panel for buttons
        self.button_panel = tk.Frame(self.display_panel, height=50, bg="lightgray")
        self.button_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.display_button = tk.Button(self.button_panel, text="Display", command=self.display_rgb_image)
        self.display_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.save_button = tk.Button(self.button_panel, text="Save", command=self.save_image)
        self.save_button.pack(side=tk.LEFT, padx=10, pady=5)

        # Bind mouse events to the image canvas for zoom and panning
        self.image_canvas.bind("<MouseWheel>", self.zoom)
        self.image_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.image_canvas.bind("<B1-Motion>", self.do_pan)

        self.zoom_level = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0

    def start_load_directory(self):
        self.clear_checkbuttons()
        self.loading_label = tk.Label(self.files_panel, text="Loading...", fg="red", bg="lightgray")
        self.loading_label.pack(side=tk.TOP, padx=10, pady=5)
        self.update_idletasks()  # Ensure the GUI updates before starting the loading process
        Thread(target=self.load_directory).start()

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.cubes = load_cubes_im3(directory)
            self.create_checkbuttons()
        self.loading_label.destroy()

    def create_checkbuttons(self):
        self.clear_checkbuttons()
        for filename in self.cubes.keys():
            var = tk.IntVar()
            checkbutton = tk.Checkbutton(self.scrollable_frame, text=filename, variable=var, bg="lightgray",
                                         font=("Helvetica", 12))
            checkbutton.pack(anchor='w', pady=2)
            self.check_vars[filename] = var

    def clear_checkbuttons(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()

    def display_rgb_image(self):
        selected_files = [filename for filename, var in self.check_vars.items() if var.get() == 1]
        if not selected_files:
            messagebox.showwarning("No files selected", "Please select one or more files to display.")
            return

        selected_cubes = [self.cubes[file]['data'] for file in selected_files]
        rgb_image = combine_cubes_to_rgb(selected_cubes)

        self.current_rgb_image = rgb_image
        self.current_selected_files = selected_files

        self.show_image(rgb_image)

    def show_image(self, rgb_image):
        self.zoom_level = 1.0
        self.img = Image.fromarray(rgb_image)
        self.tk_image = ImageTk.PhotoImage(self.img)
        self.image_id = self.image_canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.image_canvas.config(scrollregion=self.image_canvas.bbox(self.image_id))

    def zoom(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1

        # Resize image
        width, height = self.img.size
        new_width, new_height = int(width * self.zoom_level), int(height * self.zoom_level)
        resized_img = self.img.resize((new_width, new_height), Image.ANTIALIAS)

        self.tk_image = ImageTk.PhotoImage(resized_img)
        self.image_canvas.itemconfig(self.image_id, image=self.tk_image)
        self.image_canvas.config(scrollregion=self.image_canvas.bbox(self.image_id))

    def start_pan(self, event):
        self.image_canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.image_canvas.scan_dragto(event.x, event.y, gain=1)

    def save_image(self):
        if self.current_rgb_image is None or self.current_selected_files is None:
            messagebox.showwarning("No image to save", "Please display an image before saving.")
            return

        save_filename = "_".join([os.path.splitext(file)[0] for file in self.current_selected_files]) + ".png"
        save_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=save_filename,
                                                 filetypes=[("PNG files", "*.png")])

        if save_path:
            imageio.imwrite(save_path, self.current_rgb_image)
            messagebox.showinfo("Image Saved", f"Image saved as {save_path}")


if __name__ == "__main__":
    app = IM3AnalyzerGUI()
    app.mainloop()
