import tkinter as tk
from tkinter import filedialog, Scale, HORIZONTAL
from PIL import Image, ImageTk, ImageSequence
import sys
import os
import time


class GIFPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("GIFF - An Advanced Gif Player")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.fullscreen = False
        self.last_click_time = 0

        # Устанавливаем иконку окна
        self.set_window_icon()

        self.gif_path = None
        self.original_frames = []
        self.current_frame = 0
        self.playing = False
        self.speed_factor = 1.0
        self.delays = []
        self.after_id = None
        self.cached_images = {}
        self.last_update_time = 0
        self.frame_accumulator = 0
        self.resize_id = None

        self.create_widgets()

        # Проверяем аргументы командной строки
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                self.gif_path = file_path
                self.load_gif()
                self.toggle_play_pause()

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.canvas.bind("<Double-Button-1>", self.toggle_fullscreen_canvas)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def set_window_icon(self):
        try:
            # Сначала пытаемся найти иконку в разных местах
            icon_paths = [
                'icon.ico',
                'icon.png',
                os.path.join(os.path.dirname(__file__), 'icon.ico'),
                os.path.join(os.path.dirname(__file__), 'icon.png'),
            ]

            # Если приложение запущено из exe
            if hasattr(sys, '_MEIPASS'):
                icon_paths.append(os.path.join(sys._MEIPASS, 'icon.ico'))
                icon_paths.append(os.path.join(sys._MEIPASS, 'icon.png'))

            icon_found = False

            for icon_path in icon_paths:
                if os.path.exists(icon_path):

                    if icon_path.endswith('.ico'):
                        # Для .ico используем iconbitmap
                        try:
                            self.root.iconbitmap(icon_path)
                            icon_found = True
                            break
                        except Exception as e:
                            print("Error: ", e)
                    elif icon_path.endswith('.png'):
                        # Для .png конвертируем в PhotoImage
                        try:
                            img = Image.open(icon_path)
                            photo = ImageTk.PhotoImage(img)
                            self.root.iconphoto(True, photo)
                            self.icon = photo  # Сохраняем ссылку
                            icon_found = True
                            break
                        except Exception as e:
                            print("Error: ", e)
            if not icon_found:
                print("No icon")
                # Создаем простую иконку по умолчанию
                try:
                    img = Image.new('RGB', (64, 64), color='blue')
                    photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(True, photo)
                    self.icon = photo
                except:
                    pass

        except Exception as e:
            print(f"Error setting the icon: {e}")

    def create_widgets(self):
        self.control_frame = tk.Frame(self.root, bg='lightgray', height=50)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.open_btn = tk.Button(self.control_frame, text="Open GIF", command=self.open_gif)
        self.open_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_pause_btn = tk.Button(self.control_frame, text="▶", command=self.toggle_play_pause, state=tk.DISABLED)
        self.play_pause_btn.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(self.control_frame, text="Speed:", bg='lightgray').pack(side=tk.LEFT, padx=5)
        self.speed_slider = Scale(self.control_frame, from_=0.1, to=3.0, resolution=0.1,
                                  orient=HORIZONTAL, length=150, command=self.change_speed)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        self.fullscreen_btn = tk.Button(self.control_frame, text="Fullscreen", command=self.toggle_fullscreen_button)
        self.fullscreen_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.info_label = tk.Label(self.control_frame, text="No file selected", bg='lightgray')
        self.info_label.pack(side=tk.LEFT, padx=20)

        self.canvas = tk.Canvas(self.root, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.seek_slider = Scale(self.root, from_=0, to=100, orient=HORIZONTAL,
                                 length=780, command=self.seek_frame)
        self.seek_slider.pack(side=tk.BOTTOM, pady=5)
        self.seek_slider.set(0)

    def on_canvas_click(self, event):
        current_time = time.time()
        if current_time - self.last_click_time < 0.3:
            self.toggle_fullscreen()
        self.last_click_time = current_time

    def toggle_fullscreen_canvas(self, event):
        self.toggle_fullscreen()

    def toggle_fullscreen_button(self, event=None):
        self.toggle_fullscreen()

    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.root.attributes("-fullscreen", True)
            self.control_frame.pack_forget()
            self.seek_slider.pack_forget()
            self.fullscreen_btn.config(text="Exit Fullscreen")
        else:
            self.root.attributes("-fullscreen", False)
            self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)
            self.seek_slider.pack(side=tk.BOTTOM, pady=5)
            self.fullscreen_btn.config(text="Fullscreen")

        if self.original_frames:
            self.update_display()

    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.toggle_fullscreen()

    def open_gif(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )

        if file_path:
            self.gif_path = file_path
            self.load_gif()
            self.toggle_play_pause()

    def load_gif(self):
        try:
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None

            self.playing = False
            self.play_pause_btn.config(text="▶", state=tk.DISABLED)

            gif = Image.open(self.gif_path)
            self.original_frames = []
            self.delays = []
            self.cached_images = {}
            self.frame_accumulator = 0

            # Простой и надежный способ загрузки кадров
            frame_count = 0
            while True:
                try:
                    # Копируем текущий кадр
                    frame_image = gif.copy().convert('RGBA')
                    self.original_frames.append(frame_image)

                    # Получаем задержку
                    delay = gif.info.get('duration', 100)
                    if delay == 0 or delay < 10:
                        delay = 100
                    self.delays.append(delay)

                    frame_count += 1

                    # Пытаемся перейти к следующему кадру
                    gif.seek(frame_count)

                except EOFError:
                    # Достигнут конец файла
                    break
                except Exception as e:
                    print(f"Error loading frame {frame_count}: {e}")
                    break

            self.current_frame = 0
            self.play_pause_btn.config(state=tk.NORMAL)

            if len(self.original_frames) > 1:
                self.seek_slider.config(from_=0, to=len(self.original_frames) - 1)
                self.seek_slider.set(0)
            else:
                self.seek_slider.set(0)

            filename = os.path.basename(self.gif_path)
            self.info_label.config(text=f"{filename} | Frames: {len(self.original_frames)}")

            self.update_display()

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def get_scaled_image(self, img, width, height):
        cache_key = f"{id(img)}_{width}_{height}"

        if cache_key in self.cached_images:
            return self.cached_images[cache_key]

        img_width, img_height = img.size

        if img_width <= 0 or img_height <= 0 or width <= 0 or height <= 0:
            tk_img = ImageTk.PhotoImage(img)
            self.cached_images[cache_key] = tk_img
            return tk_img

        width_ratio = width / img_width
        height_ratio = height / img_height

        if width_ratio < height_ratio:
            new_width = width
            new_height = int(img_height * width_ratio)
        else:
            new_height = height
            new_width = int(img_width * height_ratio)

        if new_width <= 0 or new_height <= 0:
            tk_img = ImageTk.PhotoImage(img)
            self.cached_images[cache_key] = tk_img
            return tk_img

        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_img)

        self.cached_images[cache_key] = tk_img
        return tk_img

    def update_display(self):
        if not self.original_frames or self.current_frame >= len(self.original_frames):
            return

        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        current_img = self.original_frames[self.current_frame]
        tk_img = self.get_scaled_image(current_img, canvas_width, canvas_height)

        x = (canvas_width - tk_img.width()) // 2
        y = (canvas_height - tk_img.height()) // 2

        self.canvas.create_image(x, y, anchor=tk.NW, image=tk_img)

        if len(self.original_frames) > 1 and not self.fullscreen:
            self.seek_slider.set(self.current_frame)

    def play_animation(self):
        if not self.original_frames or not self.playing:
            return

        current_time = time.time() * 1000

        if self.last_update_time == 0:
            self.last_update_time = current_time
            delay = 100
        else:
            if self.current_frame < len(self.delays):
                frame_delay = self.delays[self.current_frame] / self.speed_factor
            else:
                frame_delay = 100 / self.speed_factor

            frame_delay = max(30, frame_delay)

            self.frame_accumulator += (current_time - self.last_update_time)

            if self.frame_accumulator >= frame_delay:
                frames_to_advance = int(self.frame_accumulator // frame_delay)
                self.current_frame = (self.current_frame + frames_to_advance) % len(self.original_frames)
                self.frame_accumulator = self.frame_accumulator % frame_delay
                self.update_display()

            delay = max(16, int(frame_delay - self.frame_accumulator))

        self.last_update_time = current_time
        self.after_id = self.root.after(delay, self.play_animation)

    def toggle_play_pause(self):
        if self.playing:
            self.playing = False
            self.play_pause_btn.config(text="▶")
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.last_update_time = 0
            self.frame_accumulator = 0
        else:
            self.playing = True
            self.play_pause_btn.config(text="⏸")
            self.last_update_time = 0
            self.frame_accumulator = 0
            self.play_animation()

    def change_speed(self, value):
        try:
            self.speed_factor = float(value)

            if self.playing:
                if self.after_id:
                    self.root.after_cancel(self.after_id)
                    self.after_id = None
                self.last_update_time = 0
                self.frame_accumulator = 0
                self.play_animation()

        except ValueError:
            pass

    def seek_frame(self, value):
        if self.original_frames:
            try:
                frame_index = int(float(value))
                if 0 <= frame_index < len(self.original_frames):
                    was_playing = self.playing
                    if self.playing:
                        self.playing = False
                        self.play_pause_btn.config(text="▶")
                        if self.after_id:
                            self.root.after_cancel(self.after_id)
                            self.after_id = None

                    self.current_frame = frame_index
                    self.update_display()

                    if was_playing:
                        self.playing = True
                        self.play_pause_btn.config(text="⏸")
                        self.last_update_time = 0
                        self.frame_accumulator = 0
                        self.play_animation()
            except ValueError:
                pass

    def on_resize(self, event):
        if event.widget == self.root and hasattr(self, 'original_frames') and self.original_frames:
            if self.resize_id:
                try:
                    self.root.after_cancel(self.resize_id)
                except:
                    pass
            self.resize_id = self.root.after(100, self.update_display)


def main():
    root = tk.Tk()
    player = GIFPlayer(root)

    root.bind('<Configure>', player.on_resize)

    root.mainloop()


if __name__ == "__main__":
    main()
