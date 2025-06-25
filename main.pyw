import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, simpledialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import json

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("kpv - paint by kaakaow")
        # State
        self.pen_color = "#000000"
        self.bg_color = "#FFFFFF"
        self.pen_width = 5
        self.tool = "pen"
        self.eraser_mode = False
        self.bg_image = None
        self.drawn_items = []
        self.undone_items = []

        self.start_x = None
        self.start_y = None
        self.temp_shape = None
        self.last_x = None
        self.last_y = None

        self.create_ui()
        self.bind_events()

    def create_ui(self):
        top = ttk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X)

        # Tool buttons
        for t in ["Pen", "Eraser", "Rect", "Oval", "Line", "Text", "Undo"]:
            ttk.Button(top, text=t, command=lambda tool=t.lower(): self.set_tool(tool)).pack(side=tk.LEFT, padx=2)

        # Color + Thickness
        self.color_preview = tk.Label(top, width=2, bg=self.pen_color)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Color", command=self.choose_color).pack(side=tk.LEFT)

        self.slider = ttk.Scale(top, from_=1, to=20, orient=tk.HORIZONTAL, command=self.update_thickness)
        self.slider.set(self.pen_width)
        self.slider.pack(side=tk.LEFT, padx=10)
        ttk.Label(top, text="Pen Size").pack(side=tk.LEFT)


        ttk.Button(top, text="BG Color", command=self.set_bg_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="BG Image", command=self.load_bg_image).pack(side=tk.LEFT, padx=5)

        # Canvas
        self.canvas = tk.Canvas(self.root, bg=self.bg_color, width=800, height=600, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())

    def set_tool(self, tool):
        if tool in ["undo", "redo"]:
            getattr(self, tool)()
        else:
            self.tool = tool
            self.eraser_mode = (tool == "eraser")

    def update_thickness(self, val):
        self.pen_width = int(float(val))

    def choose_color(self):
        color = colorchooser.askcolor(color=self.pen_color)[1]
        if color:
            self.pen_color = color
            self.eraser_mode = False
            self.color_preview.config(bg=color)

    def on_click(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.last_x, self.last_y = event.x, event.y

        if self.tool == "text":
            text = simpledialog.askstring("Text Tool", "Enter text:")
            if text:
                item = self.canvas.create_text(event.x, event.y, text=text, fill=self.pen_color, anchor="nw", font=("Arial", self.pen_width + 8))
                self.drawn_items.append(("text", item))
                self.undone_items.clear()

    def on_drag(self, event):
        if self.tool == "pen" or self.tool == "eraser":
            color = self.bg_color if self.eraser_mode else self.pen_color
            line = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                           fill=color, width=self.pen_width, capstyle=tk.ROUND)
            self.drawn_items.append(("line", line))
            self.undone_items.clear()
            self.last_x, self.last_y = event.x, event.y
        elif self.tool in ["rect", "oval", "line"]:
            if self.temp_shape:
                self.canvas.delete(self.temp_shape)
            color = self.pen_color
            if self.tool == "rect":
                self.temp_shape = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y,
                                                               outline=color, width=self.pen_width)
            elif self.tool == "oval":
                self.temp_shape = self.canvas.create_oval(self.start_x, self.start_y, event.x, event.y,
                                                          outline=color, width=self.pen_width)
            elif self.tool == "line":
                self.temp_shape = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y,
                                                          fill=color, width=self.pen_width)

    def on_release(self, event):
        if self.temp_shape:
            self.drawn_items.append((self.tool, self.temp_shape))
            self.temp_shape = None
            self.undone_items.clear()

    def undo(self):
        if self.drawn_items:
            tool, item = self.drawn_items.pop()
            self.canvas.delete(item)
            self.undone_items.append((tool, item))

    def redo(self):
        if self.undone_items:
            # Redo not implemented fully because canvas items can't be restored
            messagebox.showinfo("Redo", "Redo is a placeholder (full redo requires item recreation).")

    def save_kpw(self):
        path = filedialog.asksaveasfilename(defaultextension=".kpw")
        if not path: return
        data = [self.canvas.itemconfig(i[1]) for i in self.drawn_items]
        with open(path, "w") as f:
            json.dump(data, f)

    def load_kpw(self):
        path = filedialog.askopenfilename(filetypes=[("KPW", "*.kpw")])
        if not path: return
        self.clear_canvas()
        with open(path, "r") as f:
            try:
                data = json.load(f)
                for item in data:
                    if 'text' in item:
                        self.canvas.create_text(item['text'][-1], text=item['text'][-1],
                                                fill=item['fill'][-1], font=("Arial", self.pen_width + 8))
                    else:
                        self.canvas.create_line(0, 0, 100, 100)  # Dummy placeholder
            except Exception as e:
                messagebox.showerror("Error", f"Couldn't load: {e}")

    def save_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path: return
        image = Image.new("RGB", (800, 600), self.bg_color)
        draw = ImageDraw.Draw(image)
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            conf = self.canvas.itemconfig(item)
            color = conf.get("fill", ("", "", ""))[-1]
            width = int(conf.get("width", ("", "", "1"))[-1])
            if self.canvas.type(item) == "line" and len(coords) >= 4:
                draw.line(coords, fill=color, width=width)
        image.save(path)

    def set_bg_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.bg_color = color
            self.canvas.config(bg=color)

    def load_bg_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.bmp")])
        if not path: return
        img = Image.open(path).resize((800, 600))
        self.bg_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.drawn_items.clear()
        self.undone_items.clear()

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()
