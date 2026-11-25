
import shutil
import threading
import queue
import tkinter as tk

from tkinter import ttk, filedialog, messagebox
from pathlib import Path


class FileMoverApp:

    def __init__(self, root):
        self.root = root
        self.root.title("File Mover")
        self.root.geometry("850x750")
        self.root.minsize(680, 600)

        self.event_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread = None

        # Folder settings
        self.source_var = tk.StringVar()
        self.destination_var = tk.StringVar()

        # File type settings
        self.file_type_vars = {
            "PDF": tk.BooleanVar(value=True),
            "Word": tk.BooleanVar(value=False),
            "Excel": tk.BooleanVar(value=False),
            "PowerPoint": tk.BooleanVar(value=False),
            "Text / CSV": tk.BooleanVar(value=False),
            "Images": tk.BooleanVar(value=False),
        }

        self.custom_extensions_var = tk.StringVar()

        # Options
        self.recursive_var = tk.BooleanVar(value=False)
        self.preserve_structure_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Ready")
        self.current_file_var = tk.StringVar(value="")

        self.build_ui()

        self.root.after(100, self.process_queue)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def build_ui(self):

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(5, weight=1)

        # Title
        title_frame = ttk.Frame(main)
        title_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 10)
        )

        ttk.Label(
            title_frame,
            text="File Mover",
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Move files between folders"
        ).pack(anchor="w")

        # --------------------------------------------------
        # Folder selection
        # --------------------------------------------------

        folder_frame = ttk.LabelFrame(
            main,
            text="Folders",
            padding=8
        )

        folder_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=5
        )

        folder_frame.columnconfigure(1, weight=1)

        ttk.Label(
            folder_frame,
            text="Source folder"
        ).grid(row=0, column=0, sticky="w", pady=4)

        ttk.Entry(
            folder_frame,
            textvariable=self.source_var
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5
        )

        ttk.Button(
            folder_frame,
            text="Browse...",
            command=self.select_source
        ).grid(row=0, column=2)

        ttk.Label(
            folder_frame,
            text="Destination folder"
        ).grid(row=1, column=0, sticky="w", pady=4)

        ttk.Entry(
            folder_frame,
            textvariable=self.destination_var
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=5
        )

        ttk.Button(
            folder_frame,
            text="Browse...",
            command=self.select_destination
        ).grid(row=1, column=2)

        # --------------------------------------------------
        # File types
        # --------------------------------------------------

        file_types_frame = ttk.LabelFrame(
            main,
            text="File Types to Move",
            padding=8
        )

        file_types_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=5
        )

        file_type_items = [
            ("PDF", "PDF"),
            ("Word", "Word (.doc, .docx)"),
            ("Excel", "Excel (.xls, .xlsx, .xlsm, .xlsb)"),
            ("PowerPoint", "PowerPoint (.ppt, .pptx, .pptm)"),
            ("Text / CSV", "Text / CSV (.txt, .csv)"),
            ("Images", "Images (.jpg, .png, .jpeg, .tiff)"),
        ]

        for index, (key, label) in enumerate(file_type_items):

            ttk.Checkbutton(
                file_types_frame,
                text=label,
                variable=self.file_type_vars[key]
            ).grid(
                row=index // 2,
                column=index % 2,
                sticky="w",
                padx=8,
                pady=3
            )

        # Custom extensions
        ttk.Label(
            file_types_frame,
            text="Custom extensions:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=8,
            pady=5
        )

        ttk.Entry(
            file_types_frame,
            textvariable=self.custom_extensions_var
        ).grid(
            row=3,
            column=1,
            sticky="ew",
            padx=8,
            pady=5
        )

        ttk.Label(
            file_types_frame,
            text="Example: .zip, .json, .md",
            foreground="gray"
        ).grid(
            row=4,
            column=1,
            sticky="w",
            padx=8
        )

        file_types_frame.columnconfigure(1, weight=1)

        # --------------------------------------------------
        # Options
        # --------------------------------------------------

        options_frame = ttk.LabelFrame(
            main,
            text="Options",
            padding=8
        )

        options_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=5
        )

        ttk.Checkbutton(
            options_frame,
            text="Include files in subfolders",
            variable=self.recursive_var
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Preserve source folder structure",
            variable=self.preserve_structure_var
        ).pack(anchor="w", pady=2)

        ttk.Checkbutton(
            options_frame,
            text="Overwrite files with the same name",
            variable=self.overwrite_var
        ).pack(anchor="w", pady=2)

        # --------------------------------------------------
        # Progress
        # --------------------------------------------------

        progress_frame = ttk.LabelFrame(
            main,
            text="Progress",
            padding=8
        )

        progress_frame.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=5
        )

        ttk.Label(
            progress_frame,
            textvariable=self.status_var
        ).pack(anchor="w")

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate"
        )

        self.progress_bar.pack(
            fill="x",
            pady=5
        )

        ttk.Label(
            progress_frame,
            textvariable=self.current_file_var
        ).pack(anchor="w")

        # --------------------------------------------------
        # Activity log
        # --------------------------------------------------

        log_frame = ttk.LabelFrame(
            main,
            text="Activity Log",
            padding=5
        )

        log_frame.grid(
            row=5,
            column=0,
            sticky="nsew",
            pady=5
        )

        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            height=5,
            wrap="word",
            state="disabled"
        )

        scrollbar = ttk.Scrollbar(
            log_frame,
            command=self.log_text.yview
        )

        self.log_text.configure(
            yscrollcommand=scrollbar.set
        )

        self.log_text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        # --------------------------------------------------
        # Bottom buttons
        # --------------------------------------------------

        button_frame = ttk.Frame(main)

        button_frame.grid(
            row=6,
            column=0,
            sticky="ew",
            pady=(10, 0)
        )

        self.start_button = ttk.Button(
            button_frame,
            text="▶ Start Moving Files",
            command=self.start_moving
        )

        self.start_button.pack(side="left")

        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_moving,
            state="disabled"
        )

        self.cancel_button.pack(
            side="left",
            padx=10
        )

        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log
        ).pack(side="right")

    # --------------------------------------------------
    # Folder selection
    # --------------------------------------------------

    def select_source(self):

        folder = filedialog.askdirectory(
            title="Select Source Folder"
        )

        if folder:
            self.source_var.set(folder)

    def select_destination(self):

        folder = filedialog.askdirectory(
            title="Select Destination Folder"
        )

        if folder:
            self.destination_var.set(folder)

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(self, message):

        self.log_text.configure(state="normal")

        self.log_text.insert(
            "end",
            message + "\n"
        )

        self.log_text.see("end")

        self.log_text.configure(state="disabled")

    def clear_log(self):

        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # --------------------------------------------------
    # File extensions
    # --------------------------------------------------

    def get_selected_extensions(self):

        extension_map = {
            "PDF": [".pdf"],

            "Word": [
                ".doc",
                ".docx"
            ],

            "Excel": [
                ".xls",
                ".xlsx",
                ".xlsm",
                ".xlsb"
            ],

            "PowerPoint": [
                ".ppt",
                ".pptx",
                ".pptm"
            ],

            "Text / CSV": [
                ".txt",
                ".csv"
            ],

            "Images": [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".tif",
                ".tiff"
            ],
        }

        selected_extensions = set()

        # Selected categories
        for file_type, variable in self.file_type_vars.items():

            if variable.get():

                selected_extensions.update(
                    extension_map[file_type]
                )

        # Custom extensions
        custom_text = self.custom_extensions_var.get().strip()

        if custom_text:

            custom_items = (
                custom_text
                .replace(";", ",")
                .split(",")
            )

            for item in custom_items:

                extension = item.strip().lower()

                if not extension:
                    continue

                if not extension.startswith("."):
                    extension = "." + extension

                selected_extensions.add(extension)

        return selected_extensions

    # --------------------------------------------------
    # Find matching files
    # --------------------------------------------------

    def get_matching_files(
        self,
        source,
        destination,
        selected_extensions
    ):

        if self.recursive_var.get():
            candidates = source.rglob("*")
        else:
            candidates = source.iterdir()

        matched_files = []

        for path in candidates:

            if not path.is_file():
                continue

            if path.suffix.lower() not in selected_extensions:
                continue

            # Exclude destination folder and its contents
            if destination == path or destination in path.parents:
                continue

            matched_files.append(path)

        return matched_files

    # --------------------------------------------------
    # Determine destination filename
    # --------------------------------------------------

    def get_target_path(
        self,
        file_path,
        source,
        destination
    ):

        if (
            self.preserve_structure_var.get()
            and self.recursive_var.get()
        ):

            relative_path = file_path.relative_to(source)

            target = destination / relative_path

        else:

            target = destination / file_path.name

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Overwrite existing file
        if self.overwrite_var.get():
            return target

        # No conflict
        if not target.exists():
            return target

        # Generate unique filename
        counter = 1

        while True:

            new_name = (
                f"{target.stem}_{counter}{target.suffix}"
            )

            new_target = target.with_name(new_name)

            if not new_target.exists():
                return new_target

            counter += 1

    # --------------------------------------------------
    # Start operation
    # --------------------------------------------------

    def start_moving(self):

        source_text = self.source_var.get().strip()
        destination_text = self.destination_var.get().strip()

        if not source_text or not destination_text:

            messagebox.showwarning(
                "Missing Folder",
                "Please select both source and destination folders."
            )

            return

        source = Path(source_text).expanduser().resolve()
        destination = Path(destination_text).expanduser().resolve()

        if not source.exists() or not source.is_dir():

            messagebox.showerror(
                "Invalid Source",
                "The source folder does not exist."
            )

            return

        if source == destination:

            messagebox.showerror(
                "Invalid Destination",
                "Source and destination cannot be the same."
            )

            return

        if destination.is_relative_to(source):

            messagebox.showerror(
                "Invalid Destination",
                "Destination cannot be inside the source folder."
            )

            return

        selected_extensions = self.get_selected_extensions()

        if not selected_extensions:

            messagebox.showwarning(
                "No File Types",
                "Please select at least one file type "
                "or enter custom extensions."
            )

            return

        # Reset
        self.cancel_event.clear()
        self.progress_var.set(0)

        self.status_var.set("Preparing...")
        self.current_file_var.set("")

        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")

        self.log("")
        self.log("Starting file move operation...")
        self.log(f"Source: {source}")
        self.log(f"Destination: {destination}")
        self.log(f"Extensions: {', '.join(sorted(selected_extensions))}")

        self.worker_thread = threading.Thread(
            target=self.move_worker,
            args=(
                source,
                destination,
                selected_extensions
            ),
            daemon=True
        )

        self.worker_thread.start()

    # --------------------------------------------------
    # Background worker
    # --------------------------------------------------

    def move_worker(
        self,
        source,
        destination,
        selected_extensions
    ):

        moved = 0
        failed = 0
        total = 0

        try:

            destination.mkdir(
                parents=True,
                exist_ok=True
            )

            files = self.get_matching_files(
                source,
                destination,
                selected_extensions
            )

            total = len(files)

            self.event_queue.put(
                ("total", total)
            )

            if total == 0:

                self.event_queue.put(
                    ("log", "No matching files found.")
                )

            for index, file_path in enumerate(files, start=1):

                if self.cancel_event.is_set():
                    break

                self.event_queue.put(
                    (
                        "current",
                        f"Processing: {file_path.name}"
                    )
                )

                try:

                    target_path = self.get_target_path(
                        file_path,
                        source,
                        destination
                    )

                    shutil.move(
                        str(file_path),
                        str(target_path)
                    )

                    moved += 1

                    self.event_queue.put(
                        (
                            "log",
                            f"Moved: {file_path.name} "
                            f"-> {target_path}"
                        )
                    )

                except Exception as error:

                    failed += 1

                    self.event_queue.put(
                        (
                            "log",
                            f"ERROR: {file_path.name}: {error}"
                        )
                    )

                self.event_queue.put(
                    (
                        "progress",
                        index,
                        total
                    )
                )

            cancelled = self.cancel_event.is_set()

            self.event_queue.put(
                (
                    "finished",
                    moved,
                    failed,
                    total,
                    cancelled
                )
            )

        except Exception as error:

            self.event_queue.put(
                ("fatal", str(error))
            )

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    def cancel_moving(self):

        self.cancel_event.set()

        self.status_var.set("Cancelling...")

        self.cancel_button.configure(
            state="disabled"
        )

    # --------------------------------------------------
    # Process background events
    # --------------------------------------------------

    def process_queue(self):

        try:

            while True:

                event = self.event_queue.get_nowait()

                event_type = event[0]

                if event_type == "total":

                    total = event[1]

                    self.status_var.set(
                        f"Found {total} matching file(s)"
                    )

                elif event_type == "current":

                    self.current_file_var.set(
                        event[1]
                    )

                elif event_type == "log":

                    self.log(event[1])

                elif event_type == "progress":

                    index, total = event[1], event[2]

                    if total > 0:

                        percentage = index / total * 100

                        self.progress_var.set(
                            percentage
                        )

                    self.status_var.set(
                        f"Processed {index} of {total} files"
                    )

                elif event_type == "finished":

                    moved, failed, total, cancelled = event[1:]

                    self.start_button.configure(
                        state="normal"
                    )

                    self.cancel_button.configure(
                        state="disabled"
                    )

                    self.current_file_var.set("")

                    if cancelled:

                        self.status_var.set(
                            "Operation cancelled"
                        )

                    else:

                        self.status_var.set(
                            "Completed"
                        )

                    self.log("")
                    self.log("========== SUMMARY ==========")
                    self.log(f"Total files: {total}")
                    self.log(f"Successfully moved: {moved}")
                    self.log(f"Failed: {failed}")

                    if cancelled:
                        self.log("Operation was cancelled.")

                    if not cancelled:

                        messagebox.showinfo(
                            "File Move Completed",
                            f"Successfully moved: {moved}\n"
                            f"Failed: {failed}"
                        )

                elif event_type == "fatal":

                    self.start_button.configure(
                        state="normal"
                    )

                    self.cancel_button.configure(
                        state="disabled"
                    )

                    self.status_var.set("Error")

                    messagebox.showerror(
                        "Error",
                        event[1]
                    )

        except queue.Empty:
            pass

        self.root.after(
            100,
            self.process_queue
        )


# --------------------------------------------------
# Application entry point
# --------------------------------------------------

if __name__ == "__main__":

    root = tk.Tk()

    try:

        style = ttk.Style()
        style.theme_use("aqua")

    except tk.TclError:
        pass

    app = FileMoverApp(root)

    root.mainloop()
