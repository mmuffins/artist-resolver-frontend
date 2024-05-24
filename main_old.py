import os
import asyncio
import argparse
import httpx
from enum import Enum
from tkinter import *
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from TrackManager import TrackManager
from ttkbootstrap.toast import ToastNotification


def async_run(func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(func(*args, **kwargs))
        else:
            return loop.run_until_complete(func(*args, **kwargs))

    return wrapper


class toast_type(Enum):
    info = 1
    success = 2
    error = 3


class TrackManagerGUI:
    # Mapping between columns and source data in format
    data_mapping = {
        "file_path": {
            "source_object": "track_details",
            "property": "file_path",
            "display_name": "File Path",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "update_file": {
            "source_object": "track_details",
            "property": "update_file",
            "display_name": "Update",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "title": {
            "source_object": "track_details",
            "property": "title",
            "display_name": "Track Title",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "original_title": {
            "source_object": "track_details",
            "property": "original_title",
            "display_name": "Orig Title",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "track_artist": {
            "source_object": "track_details",
            "property": "artist",
            "display_name": "Track Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "artist_sort": {
            "source_object": "mbartist_details",
            "property": "sort_name",
            "display_name": "Sort Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "original_artist": {
            "source_object": "track_details",
            "property": "original_artist",
            "display_name": "Orig Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "album": {
            "source_object": "track_details",
            "property": "album",
            "display_name": "Album",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "product": {
            "source_object": "track_details",
            "property": "product",
            "display_name": "Product",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "original_album": {
            "source_object": "track_details",
            "property": "original_album",
            "display_name": "Orig Album",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "album_artist": {
            "source_object": "track_details",
            "property": "album_artist",
            "display_name": "Album Artist",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "grouping": {
            "source_object": "track_details",
            "property": "grouping",
            "display_name": "Grouping",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "mbid": {
            "source_object": "mbartist_details",
            "property": "mbid",
            "display_name": "MBID",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "type": {
            "source_object": "mbartist_details",
            "property": "type",
            "display_name": "Type",
            "width": 85,
            "editable": False,
            "display": True,
        },
        "artist": {
            "source_object": "mbartist_details",
            "property": "name",
            "display_name": "Artist",
            "width": 100,
            "editable": False,
            "display": True,
        },
        "joinphrase": {
            "source_object": "mbartist_details",
            "property": "joinphrase",
            "display_name": "Join Phrase",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "include": {
            "source_object": "mbartist_details",
            "property": "include",
            "display_name": "",
            "width": 30,
            "editable": False,
            "display": True,
        },
        "custom_name": {
            "source_object": "mbartist_details",
            "property": "custom_name",
            "display_name": "Custom Name",
            "width": 100,
            "editable": True,
            "display": True,
        },
        "custom_original_name": {
            "source_object": "mbartist_details",
            "property": "custom_original_name",
            "display_name": "Custom Orig Name",
            "width": 100,
            "editable": False,
            "display": False,
        },
        "updated_from_server": {
            "source_object": "mbartist_details",
            "property": "updated_from_server",
            "display_name": "Has Server Information",
            "width": 100,
            "editable": False,
            "display": False,
        },
    }

    def __init__(self, root, api_host, api_port):
        self.root = root
        self.api_host = api_host
        self.api_port = api_port

        # Set the scaling factor
        self.root.tk.call("tk", "scaling", 2.0)

        try:
            self.track_manager = self.create_track_manager()
        except Exception as e:
            self.show_toast(
                None, f"Failed to create a TrackManager object: {str(e)}", DANGER
            )
        self.get_server_health()
        self.setup_ui()

    def create_track_manager(self) -> TrackManager:
        try:
            return TrackManager(self.api_host, self.api_port)
        except Exception as e:
            self.show_toast(
                None, f"Failed to create a TrackManager object: {str(e)}", DANGER
            )
            return None

    def setup_ui(self):
        self.root.title("Track Manager")
        self.root.geometry("1000x600")
        self.root.minsize(800, 400)
        self.root.resizable(True, True)

        self.setup_layout()

    def setup_layout(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)

        self.tables_frame = self.setup_tables_frame(main_frame)
        self.actions_frame = self.setup_actions_frame(main_frame)

    def setup_tables_frame(self, main_frame):
        tables_frame = ttk.Frame(main_frame)
        tables_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        self.scrolled_frame = ScrolledFrame(
            tables_frame, bootstyle="primary", autohide=False
        )
        self.scrolled_frame.autohide_scrollbar = True
        self.scrolled_frame.pack(fill=BOTH, expand=True)

        self.tables_inner_frame = ttk.Frame(self.scrolled_frame)
        self.tables_inner_frame.pack(padx=0, pady=0, fill=BOTH, expand=True)

        return self.tables_inner_frame

    def setup_actions_frame(self, main_frame):
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(padx=10, pady=10, side=BOTTOM, fill=X)

        # Checkbox for "Replace original title"
        self.replace_original_title = BooleanVar(value=True)
        self.cb_replace_original_title = ttk.Checkbutton(
            actions_frame,
            text="Replace original title",
            variable=self.replace_original_title,
            command=self.toggle_replace_original_title,
            bootstyle=DEFAULT,
        )

        self.cb_replace_original_title.grid(row=0, column=0, sticky=W, padx=5, pady=2)

        # Checkbox for "Overwrite existing values" (title)
        self.overwrite_existing_original_title = BooleanVar(value=False)
        self.cb_overwrite_existing_original_title = ttk.Checkbutton(
            actions_frame,
            text="Overwrite existing values",
            variable=self.overwrite_existing_original_title,
            bootstyle=DEFAULT,
        )
        self.cb_overwrite_existing_original_title.grid(
            row=1, column=0, sticky=W, padx=5, pady=2
        )
        self.cb_overwrite_existing_original_title.config(state=NORMAL)

        # Checkbox for "Replace original artists"
        self.replace_original_artist = BooleanVar(value=True)
        self.cb_replace_original_artist = ttk.Checkbutton(
            actions_frame,
            text="Replace original artists",
            variable=self.replace_original_artist,
            command=self.toggle_replace_original_artist,
            bootstyle=DEFAULT,
        )
        self.cb_replace_original_artist.grid(row=0, column=1, sticky=W, padx=5, pady=2)

        # Checkbox for "Overwrite existing values" (artist)
        self.overwrite_existing_original_artist = BooleanVar(value=False)
        self.cb_overwrite_existing_original_artist = ttk.Checkbutton(
            actions_frame,
            text="Overwrite existing values",
            variable=self.overwrite_existing_original_artist,
            bootstyle=DEFAULT,
        )
        self.cb_overwrite_existing_original_artist.grid(
            row=1, column=1, sticky=W, padx=5, pady=2
        )
        self.cb_overwrite_existing_original_artist.config(state=NORMAL)

        self.btn_save = Button(actions_frame, text="Save", command=self.save_changes)
        self.btn_save.grid(row=0, column=2, rowspan=2, sticky=E, padx=40, pady=2)

        self.btn_load_files = Button(
            actions_frame, text="Select Folder", command=self.load_directory
        )
        self.btn_load_files.grid(row=0, column=3, rowspan=2, sticky=E, padx=5, pady=2)

        # Make the third column expand to push the buttons to the right
        actions_frame.grid_columnconfigure(2, weight=1)

        return actions_frame

    def toggle_replace_original_title(self):
        if self.replace_original_title.get():
            self.cb_overwrite_existing_original_title.config(state=NORMAL)
        else:
            self.cb_overwrite_existing_original_title.config(state=DISABLED)
            self.overwrite_existing_original_title.set(False)

    def toggle_replace_original_artist(self):
        if self.replace_original_artist.get():
            self.cb_overwrite_existing_original_artist.config(state=NORMAL)
        else:
            self.cb_overwrite_existing_original_artist.config(state=DISABLED)
            self.overwrite_existing_original_artist.set(False)

    def show_toast(
        self,
        title: str = None,
        message: str = None,
        style: ttk.Bootstyle = INFO,
        duration=3000,
    ):
        toast_x = self.root.winfo_x() + ((self.root.winfo_width()) // 2) - 100
        toast_y = self.root.winfo_y() + (self.root.winfo_height()) - 100

        toast = ToastNotification(
            icon="",
            title="",
            message=message,
            duration=duration,
            position=(toast_x, toast_y, "nw"),
            bootstyle=style,
        )
        toast.show_toast()

    @async_run
    async def get_server_health(self):
        try:
            api_is_healthy = await self.track_manager.get_server_health()
            if not api_is_healthy:
                self.show_toast(
                    None,
                    "The server is not healthy. Please check the server status.",
                    DANGER,
                )
        except httpx.RequestError as e:
            self.show_toast(
                None,
                f"Could not reach the server at {self.api_host}:{self.api_port}. Please ensure the server is running and try again.\n\nDetails: {str(e)}",
                DANGER,
            )
        except Exception as e:
            self.show_toast(
                None,
                f"An unexpected error occurred when trying to contact the server: {str(e)}",
                DANGER,
            )

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.track_manager = self.create_track_manager()
            self.get_server_health()
            self.load_and_update_directory(directory)

    @async_run
    async def load_and_update_directory(self, directory):
        try:
            await self.track_manager.load_directory(directory)
        except Exception as e:
            self.show_toast(
                None,
                f"An error occurred when reading directory {directory}:{str(e)}",
                DANGER,
            )

        try:
            await self.track_manager.update_artists_info_from_db()
        except Exception as e:
            self.show_toast(
                None,
                f"An error occurred querying the server for information:{str(e)}",
                DANGER,
            )

        if self.replace_original_title:
            self.track_manager.replace_original_title(
                self.overwrite_existing_original_title
            )

        if self.overwrite_existing_original_artist:
            self.track_manager.replace_original_artist(self.replace_original_artist)

        self.create_track_tables(self.tables_frame)

    def create_track_tables(self, master):
        if not hasattr(self, "treeviews"):
            self.treeviews = {}

        self.clear_existing_track_frames(master)

        for track in self.track_manager.tracks:
            frame = ttk.Frame(master)
            frame.pack(expand=True, fill=BOTH, padx=10, pady=5)

            self.populate_track_info(frame, track)
            tree = self.create_treeview(frame, track)
            self.treeviews[track] = tree  # Store the treeview for later updates
            self.populate_treeview(tree, track)

        # Update the artist labels
        self.update_artist_labels()

    def clear_existing_track_frames(self, master):
        for widget in master.winfo_children():
            widget.destroy()

    def populate_track_info(self, master, track):
        frame = ttk.Frame(master)
        frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        # Use grid for alignment
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        custom_font = ("Helvetica", 12, "bold")
        update_file = BooleanVar(value=track.update_file)
        cb_update_file = Checkbutton(
            frame,
            text=f"{track.title}",
            variable=update_file,
            command=lambda t=track, v=update_file: self.update_update_file(t, v),
            font=custom_font,
            fg="blue",  # Font color
            padx=1,
            pady=1,
        )

        cb_update_file.grid(column=0, row=0, sticky=W)

        label_current_track_artist = Label(
            frame, text=f"{'; '.join(track.artist)}", pady=1
        )
        label_current_track_artist.grid(column=1, row=0, sticky=W)

        label_new_track_artist = Label(
            frame, text=f"{track.formatted_new_artist}", pady=1
        )
        label_new_track_artist.grid(column=0, row=2, sticky=W)

        # Store references to the labels in the track object for later updating
        track.cb_update_file = cb_update_file
        track.label_current_track_artist = label_current_track_artist
        track.label_new_track_artist = label_new_track_artist

    def create_treeview(self, frame, track):
        tree = ttk.Treeview(
            frame,
            columns=tuple(self.data_mapping.keys()),
            show="headings",
            bootstyle=DARK,
        )

        num_rows = len(track.mbArtistDetails)

        tree.pack(expand=True, fill=X, padx=10, pady=10)
        tree["height"] = num_rows

        display_columns = [
            column_id
            for column_id, settings in self.data_mapping.items()
            if settings.get("display", False)
        ]
        tree["displaycolumns"] = display_columns

        for column_id, settings in self.data_mapping.items():
            tree.heading(column_id, text=settings["display_name"])
            tree.column(column_id, width=settings["width"])

        # Define the tag for red-colored cells
        tree.tag_configure("red_font", foreground="red")

        tree.bind("<Button-1>", self.on_single_click)
        tree.bind("<Double-1>", self.on_double_click)

        # Initialize the mapping dictionary for this treeview
        tree.item_to_object = {}

        return tree

    def populate_treeview(self, tree, track):
        try:
            existing_items = tree.get_children()
        except ttk.TclError:
            # If the treeview no longer exists, return early
            return

        item_to_row_id = {
            tree.item_to_object[row]["artist_detail"]: row for row in existing_items
        }

        for artist_detail in track.mbArtistDetails:
            values = self.get_treeview_row_values(track, artist_detail)
            if artist_detail in item_to_row_id:
                row_id = item_to_row_id[artist_detail]
                for column_id, value in zip(self.data_mapping.keys(), values):
                    if column_id == "include":
                        value = "☑" if value else "☐"
                    tree.set(row_id, column_id, value)
            else:
                row_id = tree.insert("", "end", values=tuple(values))
                tree.item_to_object[row_id] = {
                    "track": track,
                    "artist_detail": artist_detail,
                }
                if ("include" in self.data_mapping
                        and self.data_mapping["include"]["source_object"] == "mbartist_details"):
                    tree.set(row_id, "include", "☑" if artist_detail.include else "☐")

            # Apply the red cell tag to the custom_name column if the condition is met
            custom_name = artist_detail.custom_name
            artist_name = artist_detail.name
            if custom_name != artist_name:
                tree.item(row_id, tags=("red_font",))

        self.enforce_column_widths(tree)

    def enforce_column_widths(self, tree):
        for column_id, settings in self.data_mapping.items():
            match column_id:
                case "include":
                    tree.column(column_id, minwidth=30, stretch=False)
                case "type":
                    tree.column(column_id, minwidth=70, stretch=False)
                case _:
                    tree.column(column_id, minwidth=70, stretch=True)

    def get_treeview_row_values(self, track, artist_detail):
        values = []
        for column_id, settings in self.data_mapping.items():
            if settings["source_object"] == "track_details":
                value = getattr(track, settings["property"], "")
            else:
                value = getattr(artist_detail, settings["property"], "")
            if column_id == "include":
                value = "☑" if value else "☐"
            values.append(value)
        return values

    def update_update_file(self, track, var):
        new_value = var.get()
        if track.update_file != new_value:
            track.update_file = new_value

    @async_run
    async def save_changes(self):
        try:
            await self.track_manager.send_changes_to_db()
        except Exception as e:
            self.show_toast(
                None,
                f"An error occurred when sending update data to the server:{str(e)}",
                DANGER,
            )

        try:
            await self.track_manager.save_files()
            self.show_toast(None, "Metadata saved successfully!", SUCCESS)
        except Exception as e:
            self.show_toast(
                None, f"An error occurred when updating the files:{str(e)}", DANGER
            )

        self.create_track_tables(self.tables_frame)

    def get_clicked_cell(self, event, tree):
        region = tree.identify("region", event.x, event.y)

        if region != "cell":
            return None

        return {
            "row": tree.identify_row(event.y),
            "column": tree.identify_column(event.x),
        }

    def on_canvas_configure(self, e):
        self.tables_canvas.itemconfig(self.tables_canvas_window, width=e.width)

    def on_inner_frame_configure(self, e):
        self.tables_canvas.configure(scrollregion=self.tables_canvas.bbox("all"))

    def on_mousewheel(self, event):
        self.tables_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_single_click(self, event):
        tree = event.widget
        clicked = self.get_clicked_cell(event, tree)
        if clicked is None:
            return

        if tree.column(clicked["column"])["id"] == "include":
            row_track = tree.item_to_object.get(clicked["row"])
            if row_track is None:
                raise Exception("Row has no track details.")

            current_value = tree.set(clicked["row"], clicked["column"])
            new_value = False if current_value == "☑" else True

            value_changed = self.save_value_to_manager(
                new_value,
                tree.column(clicked["column"])["id"],
                row_track["track"],
                row_track["artist_detail"],
            )
            if value_changed:
                display_value = "☑" if new_value else "☐"
                tree.set(clicked["row"], clicked["column"], display_value)

    def on_double_click(self, event):
        tree = event.widget
        clicked = self.get_clicked_cell(event, tree)
        if clicked is None:
            return

        if self.data_mapping[tree.column(clicked["column"])["id"]]["editable"] is True:
            self.edit_cell(clicked["row"], clicked["column"], event, tree)

    def edit_cell(self, row, column, event, tree):
        x, y, w, h = tree.bbox(row, column)

        entry = Entry(tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(END, tree.set(row, column))
        entry.focus_set()
        entry.select_range(0, END)

        def save_new_value(event):
            new_value = entry.get()
            tree.set(row, column=column, value=new_value)
            entry.destroy()

            row_track = tree.item_to_object.get(row)
            if row_track is None:
                raise Exception("Row has no track details.")

            value_changed = self.save_value_to_manager(
                new_value,
                tree.column(column)["id"],
                row_track["track"],
                row_track["artist_detail"],
            )

            if value_changed:
                self.create_track_tables(self.tables_inner_frame)

        def close_without_saving(event):
            entry.destroy()

        entry.bind("<Return>", save_new_value)
        entry.bind("<FocusOut>", save_new_value)
        entry.bind("<Escape>", close_without_saving)

    def save_value_to_manager(
        self, new_value, column_id: str, track_details, mbartist_details
    ) -> bool:
        if column_id not in self.data_mapping:
            raise Exception(f"column id {column_id} was not found in data mapping.")

        # Retrieve the object and attribute name
        mapping = self.data_mapping[column_id]
        if mapping["source_object"] == "track_details":
            source_obj = track_details
        else:
            source_obj = mbartist_details

        current_value = getattr(source_obj, mapping["property"])

        if new_value == current_value:
            return False

        # Update the value
        setattr(source_obj, mapping["property"], new_value)

        # Update the relevant treeview items
        for track, tree in self.treeviews.items():
            for row_id, obj in tree.item_to_object.items():
                if obj["artist_detail"] == mbartist_details:
                    display_value = (
                        "☑"
                        if new_value and column_id == "include"
                        else (
                            "☐"
                            if not new_value and column_id == "include"
                            else new_value
                        )
                    )
                    tree.set(row_id, column_id, display_value)

        # Update the artist labels
        self.update_artist_labels()

        return True

    def update_artist_labels(self):
        for track in self.track_manager.tracks:
            # Update each label with the current artist information
            current_artists = "; ".join(track.artist)
            new_artists = track.formatted_new_artist

            track.cb_update_file.config(text=f"{track.title}")
            track.label_current_track_artist.config(text=f"{current_artists}")
            track.label_new_track_artist.config(text=f"{new_artists}")

    def run_sync(self, async_func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_func(*args, **kwargs))


def main():
    parser = argparse.ArgumentParser(prog="Artist Relation Resolver")
    parser.add_argument(
        "-s",
        "--host",
        type=str,
        required=False,
        help="host of the Artist Relation Resolver API",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=str,
        required=False,
        help="Port of the Artist Relation Resolver API",
    )

    args = parser.parse_args()

    api_host = args.host if args.host else os.getenv("ARTIST_RESOLVER_HOST", None)
    api_port = args.port if args.port else os.getenv("ARTIST_RESOLVER_PORT", None)

    root = ttk.Window(themename="darkly")
    TrackManagerGUI(root, api_host, api_port)
    root.mainloop()


if __name__ == "__main__":
    main()
