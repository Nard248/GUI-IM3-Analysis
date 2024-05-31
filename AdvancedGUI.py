import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, MULTIPLE
import os
import numpy as np
import glob
import imageio
import imagej
import spectral as spy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.geometry("800x600")

        self.cubes = {}

        self.directory_frame = tk.Frame(self)
        self.directory_frame.pack(pady=10)

        self.dir_label = tk.Label(self.directory_frame, text="IM3 Files Directory:")
        self.dir_label.pack(side=tk.LEFT)

        self.dir_entry = tk.Entry(self.directory_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=10)

        self.load_button = tk.Button(self.directory_frame, text="Load", command=self.load_directory)
        self.load_button.pack(side=tk.LEFT)

        self.files_frame = tk.Frame(self)
        self.files_frame.pack(pady=10)

        self.files_listbox = Listbox(self.files_frame, selectmode=MULTIPLE, width=50, height=15)
        self.files_listbox.pack(side=tk.LEFT, padx=10)

        self.display_button = tk.Button(self.files_frame, text="Display", command=self.display_rgb_image)
        self.display_button.pack(side=tk.LEFT, padx=10)

        self.display_frame = tk.Frame(self)
        self.display_frame.pack(pady=10)

        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.display_frame)
        self.canvas.get_tk_widget().pack()

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.cubes = load_cubes_im3(directory)
            self.files_listbox.delete(0, tk.END)
            for filename in self.cubes.keys():
                self.files_listbox.insert(tk.END, filename)

    def display_rgb_image(self):
        selected_files = [self.files_listbox.get(idx) for idx in self.files_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("No files selected", "Please select one or more files to display.")
            return

        selected_cubes = [self.cubes[file]['data'] for file in selected_files]
        rgb_image = combine_cubes_to_rgb(selected_cubes)

        self.ax.clear()
        self.ax.imshow(rgb_image)
        self.canvas.draw()


if __name__ == "__main__":
    app = IM3AnalyzerGUI()
    app.mainloop()
