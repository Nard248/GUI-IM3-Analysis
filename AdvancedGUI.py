import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, MULTIPLE
from threading import Thread
import os
import numpy as np
import glob
import imageio
import imagej
import spectral as spy
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
        self.geometry("1000x600")

        self.cubes = {}
        self.current_rgb_image = None
        self.current_selected_files = None

        self.directory_frame = tk.Frame(self)
        self.directory_frame.pack(pady=10)

        self.dir_label = tk.Label(self.directory_frame, text="IM3 Files Directory:")
        self.dir_label.pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(self.directory_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=10)

        self.load_button = tk.Button(self.directory_frame, text="Load", command=self.start_load_directory)
        self.load_button.pack(side=tk.LEFT)

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.files_frame = tk.Frame(self.main_frame)
        self.files_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.files_listbox = Listbox(self.files_frame, selectmode=MULTIPLE, width=30, height=25)
        self.files_listbox.pack(side=tk.TOP, padx=10, pady=10)

        self.display_button = tk.Button(self.files_frame, text="Display", command=self.display_rgb_image)
        self.display_button.pack(side=tk.TOP, padx=10, pady=5)

        self.save_button = tk.Button(self.files_frame, text="Save", command=self.save_image)
        self.save_button.pack(side=tk.TOP, padx=10, pady=5)

        self.loading_label = tk.Label(self.files_frame, text="", fg="red")
        self.loading_label.pack(side=tk.TOP, padx=10, pady=5)

        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.image_label = tk.Label(self.display_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)

    def start_load_directory(self):
        self.loading_label.config(text="Loading...")
        self.update_idletasks()  # Ensure the GUI updates before starting the loading process
        self.files_listbox.delete(0, tk.END)
        Thread(target=self.load_directory).start()

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.cubes = load_cubes_im3(directory)
            self.files_listbox.delete(0, tk.END)
            for filename in self.cubes.keys():
                self.files_listbox.insert(tk.END, filename)
        self.loading_label.config(text="")

    def display_rgb_image(self):
        selected_files = [self.files_listbox.get(idx) for idx in self.files_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("No files selected", "Please select one or more files to display.")
            return

        selected_cubes = [self.cubes[file]['data'] for file in selected_files]
        rgb_image = combine_cubes_to_rgb(selected_cubes)

        self.current_rgb_image = rgb_image
        self.current_selected_files = selected_files

        self.show_image(rgb_image)

    def show_image(self, rgb_image):
        img = Image.fromarray(rgb_image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.image_label.config(image=imgtk)
        self.image_label.image = imgtk

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
