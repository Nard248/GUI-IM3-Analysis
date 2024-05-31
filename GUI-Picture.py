import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw


class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.image = None
        self.photo = None
        self.rect = None
        self.start_x = None
        self.start_y = None

        self.crop_window = None
        self.crop_image = None

        self.setup_menu()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.image = Image.open(file_path)
            self.photo = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            self.canvas.bind("<ButtonPress-1>", self.on_button_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        self.show_crop_window(self.start_x, self.start_y, end_x, end_y)

    def show_crop_window(self, x1, y1, x2, y2):
        if self.crop_window:
            self.crop_window.destroy()

        self.crop_window = tk.Toplevel(self.root)
        self.crop_window.title("Cropped Image")

        crop_box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.crop_image = self.image.crop(crop_box)
        crop_photo = ImageTk.PhotoImage(self.crop_image)

        crop_canvas = tk.Canvas(self.crop_window, width=crop_photo.width(), height=crop_photo.height())
        crop_canvas.pack()
        crop_canvas.create_image(0, 0, anchor=tk.NW, image=crop_photo)

        save_button = tk.Button(self.crop_window, text="Save Image", command=self.save_image)
        save_button.pack()

        self.crop_window.mainloop()

    def save_image(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg *.jpeg"),
                                                            ("BMP files", "*.bmp")])
        if save_path:
            self.crop_image.save(save_path)
            messagebox.showinfo("Image Saved", "Cropped image saved successfully!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()
