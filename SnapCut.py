import os
from tkinter import Tk, filedialog, Canvas, NW, Toplevel, Label

from PIL import Image, ImageTk

class SnapCut:
	ANIMATION_DELAY = 100  # Задержка анимации в миллисекундах / Animation delay in milliseconds

	def __init__(self, root):
		self.root = root
		self.root.withdraw()  # Скрыть главное окно Tkinter / Hide the main Tkinter window
		self.images = []  # Список для хранения путей к изображениями / List to store image paths
		self.current_image_index = -1  # Индекс текущего изображения / Index of the current image
		self.selection_cancelled = False  # Флаг, показывающий, была ли отменена выборка / Flag indicating if the selection was canceled
		self.fullscreen = False  # Флаг, показывающий, находится ли окно в полноэкранном режиме / Flag indicating if the window is in fullscreen mode
		self.load_images()  # Загрузить изображения / Load images
		if self.images:
			self.output_folder = os.path.join(os.path.dirname(self.images[0]), "cropped")
			os.makedirs(self.output_folder, exist_ok=True)  # Создать папку для обрезанных изображений / Create folder for cropped images
			self.create_crop_window()  # Создать окно для обрезки изображений / Create crop window
			self.show_next_image()  # Показать следующее изображение / Show the next image
		self.canvas.config(cursor="cross")  # Установить курсор для холста / Set cursor for the canvas

	def load_images(self):
		# Открытие диалогового окна для выбора изображений / Open file dialog to select images
		filetypes = [("Image files", "*.png;*.jpg;*.jpeg")]
		self.images = filedialog.askopenfilenames(title=u"Выберите изображения / Choose images", filetypes=filetypes)
		self.images = list(self.images)  # Преобразовать в список / Convert to list

	def create_crop_window(self):
		# Создание окна для обрезки изображений / Create crop window
		self.crop_window = Toplevel(self.root)
		self.crop_window.title(u"SnapCut - A Quick Image Cropper")
		
		# Смещение окна / Offset of the window
		self.offset_x = -80
		self.offset_y = -80
		
		# Размеры экрана по умолчанию / Default screen size
		window_width = 1410
		window_height = 900
		screen_width = self.crop_window.winfo_screenwidth() + self.offset_x
		screen_height = self.crop_window.winfo_screenheight() + self.offset_y
		
		# Вычислить позицию окна для центрирования / Calculate the position of the window to center it
		x = (screen_width // 2) - (window_width // 2)
		y = (screen_height // 2) - (window_height // 2)

		self.crop_window.geometry(f"{window_width}x{window_height}+{x}+{y}")  # Установить размеры и позицию окна / Set the size and position of the window
		self.crop_window.protocol("WM_DELETE_WINDOW", self.exit_program)  # Обработка закрытия окна / Handle window close event
		self.canvas = Canvas(self.crop_window)  # Создание холста для рисования / Create a canvas for drawing
		self.canvas.pack(fill="both", expand=True)  # Упаковка холста / Pack the canvas
		
		# Привязать события к функциям / Bind events to functions
		self.canvas.bind("<ButtonPress-1>", self.on_button_press)
		self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
		self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
		self.canvas.bind("<Button-2>", self.on_button_press_middle)
		self.canvas.bind("<B2-Motion>", self.on_mouse_drag)
		self.canvas.bind("<ButtonRelease-2>", self.on_button_release_middle)
		self.canvas.bind("<Button-3>", self.reset_selection)
		self.crop_window.bind("<Escape>", self.exit_program)
		self.crop_window.bind("<space>", self.skip_image)
		self.crop_window.bind("<Right>", self.next_image)
		self.crop_window.bind("<Left>", self.previous_image)
		self.crop_window.bind("<Configure>", self.on_resize)
		self.crop_window.bind("<MouseWheel>", self.on_mouse_wheel)
		
		# Обработчик клавиши для кнопок F и T / Key event handler for F and T keys
		self.crop_window.bind("<Key>", self.check_key)
		
		self.rect = None  # Прямоугольник для выделения / Rectangle for selection

		# Создание метки для счетчика изображений / Create label for image counter
		self.counter_label = Label(self.crop_window, text="", font=("Bahnschrift", 16), bg="gray95", fg="gray30")
		self.counter_label.place(relx=0.5, rely=0.01, anchor='n')

		self.crop_window.focus_force()  # Установить фокус на окно / Force focus on the window

	def toggle_fullscreen(self, event=None):
		# Переключение между полноэкранным и оконным режимами / Toggle between fullscreen and windowed mode
		self.fullscreen = not self.fullscreen
		self.crop_window.attributes("-fullscreen", self.fullscreen)

	def show_next_image(self):
		# Показать следующее изображение / Show the next image
		if self.current_image_index < len(self.images) - 1:
			self.current_image_index += 1
			self.display_image()
		else:
			self.current_image_index = len(self.images) - 1

	def show_previous_image(self):
	# Показать предыдущее изображение / Show the previous image
		if self.current_image_index > 0:
			self.current_image_index -= 1
			self.display_image()
		else:
			self.current_image_index = 0

	def display_image(self):
		# Отобразить текущее изображение / Display the current image
		if self.current_image_index < 0 or self.current_image_index >= len(self.images):
			return
		image_path = self.images[self.current_image_index]
		self.img = Image.open(image_path)  # Открыть изображение / Open image
		self.update_image_display()  # Обновить отображение изображения / Update image display

	def update_image_display(self):
		# Обновить отображение изображения на холсте / Update image display on canvas
		screen_width = self.crop_window.winfo_width()
		screen_height = self.crop_window.winfo_height()

		min_size = 50
		screen_width = max(screen_width, min_size)
		screen_height = max(screen_height, min_size)

		img_ratio = self.img.width / self.img.height  # Соотношение сторон изображения / Image aspect ratio
		screen_ratio = screen_width / screen_height  # Соотношение сторон экрана / Screen aspect ratio
		if img_ratio > screen_ratio:
			# Изображение шире экрана / Image is wider than the screen
			new_width = screen_width
			new_height = int(screen_width / img_ratio)
		else:
			# Изображение выше экрана / Image is taller than the screen
			new_height = screen_height
			new_width = int(screen_height * img_ratio)

		self.img_resized = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
		self.tk_img = ImageTk.PhotoImage(self.img_resized)  # Преобразовать в формат Tkinter / Convert to Tkinter format
		self.offset_x = (screen_width - new_width) // 2  # Вычислить смещение по горизонтали / Calculate horizontal offset
		self.offset_y = (screen_height - new_height) // 2  # Вычислить смещение по вертикали / Calculate vertical offset
		self.canvas.delete("all")  # Очистить холст / Clear the canvas
		
		# Отобразить изображение на холсте / Display the image on the canvas
		self.canvas.create_image(self.offset_x, self.offset_y, image=self.tk_img, anchor=NW)
		self.rect = None

		self.counter_label.config(text=f"{self.current_image_index + 1}/{len(self.images)}")  # Обновить текст счетчика / Update counter label text

	def on_button_press(self, event):
		# Начало выделения при нажатии кнопки мыши / Start selection on mouse button press
		self.start_selection(event)

	def on_button_press_middle(self, event):
		# Начало выделения при нажатии средней кнопки мыши / Start selection on middle mouse button press
		self.start_selection(event)

	def start_selection(self, event):
		# Начало выделения области / Start selection of an area
		self.selection_cancelled = False
		self.start_x = self.canvas.canvasx(event.x) - self.offset_x  # Начальная координата x / Start x-coordinate
		self.start_y = self.canvas.canvasy(event.y) - self.offset_y  # Начальная координата y / Start y-coordinate
		
		# Ограничение начальных координат в пределах изображения / Limit start coordinates within the image
		self.start_x = max(0, min(self.start_x, self.img_resized.width))
		self.start_y = max(0, min(self.start_y, self.img_resized.height))
	
		if self.rect:
			self.canvas.delete(self.rect)  # Удалить предыдущий прямоугольник / Delete the previous rectangle
		self.rect = self.canvas.create_rectangle(self.start_x + self.offset_x, self.start_y + self.offset_y, self.start_x + self.offset_x, self.start_y + self.offset_y, outline='gray50')

	def on_mouse_drag(self, event):
		# Отслеживание движения мыши для выделения / Track mouse movement for selection
		cur_x, cur_y = (self.canvas.canvasx(event.x) - self.offset_x, self.canvas.canvasy(event.y) - self.offset_y)
		
		# Ограничение начальных координат в пределах изображения / Limit the initial coordinates within the image
		cur_x = max(0, min(cur_x, self.img_resized.width))
		cur_y = max(0, min(cur_y, self.img_resized.height))
		
		if self.start_x is not None and self.start_y is not None:
			self.canvas.coords(self.rect, self.start_x + self.offset_x, self.start_y + self.offset_y, cur_x + self.offset_x, cur_y + self.offset_y)

	def on_button_release(self, event):
		# Завершение выделения при отпускании кнопки мыши / End selection on mouse button release
		end_x, end_y = (self.canvas.canvasx(event.x) - self.offset_x, self.canvas.canvasy(event.y) - self.offset_y)
		 
		# Ограничение конечных координат в пределах изображения / Limit the end coordinates within the image
		end_x = max(0, min(end_x, self.img_resized.width))
		end_y = max(0, min(end_y, self.img_resized.height))
		 
		self.canvas.delete(self.rect)  # Удалить прямоугольник выделения / Delete selection rectangle
		self.rect = None

		if self.start_x is not None and self.start_y is not None:
			if abs(end_x - self.start_x) > 1 and abs(end_y - self.start_y) > 1:
				# Если выделенная область имеет хотя бы 2 пикселя, обрезать изображение / If selection area has at least 2 pixels, crop the image
				self.crop_image(int(self.start_x), int(self.start_y), int(end_x), int(end_y))
				if len(self.images) > 1 and self.current_image_index == len(self.images) - 1:
					self.root.after(self.ANIMATION_DELAY, self.exit_program)
				else:
					self.root.after(self.ANIMATION_DELAY, self.show_next_image)
		else:
			self.start_x = None
			self.start_y = None

	def on_button_release_middle(self, event):
		end_x, end_y = (self.canvas.canvasx(event.x) - self.offset_x, self.canvas.canvasy(event.y) - self.offset_y)
		
		# Ограничиваем конечные координаты в пределах изображения
		end_x = max(0, min(end_x, self.img_resized.width))
		end_y = max(0, min(end_y, self.img_resized.height))
		
		self.canvas.delete(self.rect)
		self.rect = None

		if self.start_x is not None and self.start_y is not None:
			if abs(end_x - self.start_x) > 1 and abs(end_y - self.start_y) > 1:
				# Если выделенная область имеет хотя бы 2 пикселя, обрезать изображение / If selection area has at least 2 pixels, crop the image
				self.crop_image(int(self.start_x), int(self.start_y), int(end_x), int(end_y))

	def reset_selection(self, event):
		# Сброс выделенной области / Reset the selection area
		if self.rect:
			self.canvas.delete(self.rect)
			self.rect = None
			self.selection_cancelled = True
			self.start_x = None
			self.start_y = None

	def crop_image(self, x1, y1, x2, y2):
		# Обрезка изображения по заданным координатам / Crop the image according to given coordinates
		x1, x2 = sorted([x1, x2])  # Сортировка координат по x / Sort x coordinates
		y1, y2 = sorted([y1, y2])  # Сортировка координат по y / Sort y coordinates
		scale_x = self.img.width / self.img_resized.width  # Масштаб по x / Scale x
		scale_y = self.img.height / self.img_resized.height  # Масштаб по y / Scale y
		
		# Применение масштаба / Apply scale
		x1 = int(x1 * scale_x)
		y1 = int(y1 * scale_y)
		x2 = int(x2 * scale_x)
		y2 = int(y2 * scale_y)

		cropped_img = self.img.crop((x1, y1, x2, y2))  # Обрезка изображения / Crop the image

		# Определение пути для сохранения обрезанного изображения / Determine path to save cropped image
		base_name = os.path.splitext(os.path.basename(self.images[self.current_image_index]))[0]
		ext = os.path.splitext(os.path.basename(self.images[self.current_image_index]))[1]
		output_path = os.path.join(self.output_folder, f"{base_name}{ext}")
		count = 1
		while os.path.exists(output_path):
			count += 1
			output_path = os.path.join(self.output_folder, f"{base_name}_{count}{ext}")
		cropped_img.save(output_path)  # Сохранение обрезанного изображения / Save cropped image

		self.animate_selection(x1, y1, x2, y2)  # Анимация выделенной области / Animate selection area

	def animate_selection(self, x1, y1, x2, y2):
		# Анимация выделенной области / Animate the selection area
		x1_resized = int(x1 / (self.img.width / self.img_resized.width)) + self.offset_x
		y1_resized = int(y1 / (self.img.height / self.img_resized.height)) + self.offset_y
		x2_resized = int(x2 / (self.img.width / self.img_resized.width)) + self.offset_x
		y2_resized = int(y2 / (self.img.height / self.img_resized.height)) + self.offset_y

		animation_rect = self.canvas.create_rectangle(
			x1_resized, y1_resized,
			x2_resized, y2_resized,
			fill='white', outline='', stipple='gray25'
		)  # Создание прямоугольника для анимации / Create rectangle for animation

		steps = 15  # Количество шагов для анимации / Number of steps for animation

		# Анимация появления / Animation of the appearance
		for step in range(steps + 1):
			alpha = int(255 * (step / steps))
			self.canvas.after(step * (self.ANIMATION_DELAY // (2 * steps)),
							  lambda s=step: self.canvas.itemconfig(animation_rect,
																	fill=f'#{255:02x}{255:02x}{255:02x}'))

		# Анимация исчезновения / Animation of the disappearance
		for step in range(steps + 1):
			alpha = int(255 * (1 - step / steps))
			hex_color = f'#{alpha:02x}{alpha:02x}{alpha:02x}'
			self.canvas.after((steps + step) * (self.ANIMATION_DELAY // (2 * steps)),
							  lambda s=step: self.canvas.itemconfig(animation_rect,
																	fill=f'#{int(255 * (1 - s / steps)):02x}{int(255 * (1 - s / steps)):02x}{int(255 * (1 - s / steps)):02x}'))

		self.canvas.after(self.ANIMATION_DELAY, lambda: self.canvas.delete(animation_rect))  # Удаление прямоугольника после анимации / Remove rectangle after animation

	def skip_image(self, event):
		# Пропустить текущее изображение и показать следующее / Skip current image and show next
		if self.current_image_index < len(self.images) - 1:
			self.root.after(self.ANIMATION_DELAY, self.show_next_image)
		else:
			self.exit_program(event)  # Завершение программы, если изображений больше нет / End program if no more images

	def next_image(self, event):
		# Показать следующее изображение / Show the next image
		if self.current_image_index < len(self.images) - 1:
			self.root.after(self.ANIMATION_DELAY, self.show_next_image)

	def previous_image(self, event):
		# Показать предыдущее изображение / Show the previous image
		if self.current_image_index > 0:
			self.show_previous_image()

	def on_mouse_wheel(self, event):
		# Обработчик прокрутки колесика мыши / Handle mouse wheel event
		if event.delta > 0:  # Показать предыдущее изображение / Show the previous image
			self.previous_image(event)
		else:
			self.next_image(event)  # Показать следующее изображение / Show the next image

	def on_resize(self, event):
		# Обработчик изменения размера окна / Handle window resize event
		self.update_image_display()

	def exit_program(self, event=None):
		# Завершение программы / End the program
		self.crop_window.destroy()  # Закрыть окно обрезки / Close crop window
		self.root.quit()  # Закрыть основное окно / Close main window
		
	def check_key(self, event):
		# Переключить полноэкранный режим / Toggle fullscreen mode
		if event.char.lower() == 'f':
			self.toggle_fullscreen(event)
		elif event.char.lower() == 'а':  # Проверка для русской 'а' / Checking for Russian 'а'
			self.toggle_fullscreen(event)

		# Скрыть счетчик изображений / Toggle the image counter
		elif event.char.lower() == 't':
			self.toggle_counter(event)
		elif event.char.lower() == 'е':# Проверка для русской 'е' / Checking for Russian 'е'
			self.toggle_counter(event)
			 
	def toggle_counter(self, event=None):
		# Функция скрытия счетчика изображений / Toggle the image counter function
		if self.counter_label.winfo_ismapped():
			self.counter_label.place_forget()
		else:
			self.counter_label.place(relx=0.5, rely=0.01, anchor='n')

if __name__ == "__main__":
	root = Tk()
	app = SnapCut(root)
	root.mainloop()