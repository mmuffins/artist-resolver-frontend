import os
import asyncio
import argparse
import httpx
from enum import Enum
from tkinter import *
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from TrackManager import TrackManager

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
        "file_path": {"source_object":"track_details", "property":"file_path", "display_name":"File Path", "width":100, "editable":False, "display":False},
        "update_file": {"source_object":"track_details", "property":"update_file", "display_name":"Update", "width":100, "editable":False, "display":False},
        "title": {"source_object":"track_details", "property":"title", "display_name":"Track Title", "width":100, "editable":False, "display":False},
        "original_title": {"source_object":"track_details", "property":"original_title", "display_name":"Orig Title", "width":100, "editable":False, "display":False},
        "track_artist": {"source_object":"track_details", "property":"artist", "display_name":"Track Artist", "width":100, "editable":False, "display":False},
        "artist_sort": {"source_object":"mbartist_details", "property":"sort_name", "display_name":"Sort Artist", "width":100, "editable":False, "display":False},
        "original_artist": {"source_object":"track_details", "property":"original_artist", "display_name":"Orig Artist", "width":100, "editable":False, "display":False},
        "album": {"source_object":"track_details", "property":"album", "display_name":"Album", "width":100, "editable":False, "display":False},
        "product": {"source_object":"track_details", "property":"product", "display_name":"Product", "width":100, "editable":False, "display":False},
        "original_album": {"source_object":"track_details", "property":"original_album", "display_name":"Orig Album", "width":100, "editable":False, "display":False},
        "album_artist": {"source_object":"track_details", "property":"album_artist", "display_name":"Album Artist", "width":100, "editable":False, "display":False},
        "grouping": {"source_object":"track_details", "property":"grouping", "display_name":"Grouping", "width":100, "editable":False, "display":False},
        "include": {"source_object":"mbartist_details", "property":"include", "display_name":"Set", "width":30, "editable":True, "display":True},
        "mbid": {"source_object":"mbartist_details", "property":"mbid", "display_name":"MBID", "width":100, "editable":False, "display":False},
        "type": {"source_object":"mbartist_details", "property":"type", "display_name":"Type", "width":75, "editable":False, "display":True},
        "artist": {"source_object":"mbartist_details", "property":"name", "display_name":"Artist", "width":100, "editable":False, "display":True},
        "joinphrase": {"source_object":"mbartist_details", "property":"joinphrase", "display_name":"Join Phrase", "width":100, "editable":False, "display":False},
        "custom_name": {"source_object":"mbartist_details", "property":"custom_name", "display_name":"Custom Name", "width":100, "editable":True, "display":True},
        "custom_original_name": {"source_object":"mbartist_details", "property":"custom_original_name", "display_name":"Custom Orig Name", "width":100, "editable":False, "display":False},
        "updated_from_server": {"source_object":"mbartist_details", "property":"updated_from_server", "display_name":"Has Server Information", "width":100, "editable":False, "display":False},
    }

    def __init__(self, root, api_host, api_port):
        self.root = root
        self.api_host = api_host
        self.api_port = api_port

        try:
            self.track_manager = self.create_track_manager()
        except Exception as e:
            self.show_toast(toast_type.error, f"Failed to create a TrackManager object: {str(e)}")
        self.get_server_health()
        self.setup_ui()

    def create_track_manager(self) -> TrackManager:
        try:
            return TrackManager(self.api_host, self.api_port)
        except Exception as e:
            self.show_toast(toast_type.error, f"Failed to create a TrackManager object: {str(e)}")
            return None

    def setup_ui(self):
        self.root.title("Track Manager")
        self.root.geometry("700x600")
        self.root.minsize(800,400)
        self.root.resizable(True, True)

        self.setup_layout()

    def setup_layout(self):
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)
        
        self.tables_frame = self.setup_tables_frame(main_frame)
        self.actions_frame = self.setup_actions_frame(main_frame)

    def setup_tables_frame(self, main_frame):
        tables_frame = Frame(main_frame)
        tables_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        # frames don't support scrolling by themselves, so we need to create a canvas
        self.tables_canvas = Canvas(tables_frame)
        self.tables_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.scrollbar = Scrollbar(tables_frame, orient=VERTICAL, command=self.tables_canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.tables_inner_frame = Frame(self.tables_canvas)
        self.tables_canvas_window = self.tables_canvas.create_window((0, 0), window=self.tables_inner_frame, anchor="nw")

        self.tables_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tables_canvas.bind('<Configure>', self.on_canvas_configure)
        self.tables_canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        self.tables_inner_frame.bind('<Configure>', self.on_inner_frame_configure)
        
        return tables_frame

    def setup_actions_frame(self, main_frame):
        actions_frame = Frame(main_frame)
        actions_frame.pack(padx=10, pady=10, side=BOTTOM, fill=X)

        # Checkbox for "Replace original title"
        self.replace_original_title = BooleanVar(value=True)
        self.cb_replace_original_title = Checkbutton(
            actions_frame, 
            text="Replace original title", 
            variable=self.replace_original_title,
            command=self.toggle_replace_original_title
        )
        
        self.cb_replace_original_title.grid(row=0, column=0, sticky=W, padx=5, pady=2)

        # Checkbox for "Overwrite existing values" (title)
        self.overwrite_existing_original_title = BooleanVar(value=False)
        self.cb_overwrite_existing_original_title = Checkbutton(
            actions_frame, 
            text="Overwrite existing values", 
            variable=self.overwrite_existing_original_title
        )
        self.cb_overwrite_existing_original_title.grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.cb_overwrite_existing_original_title.config(state=NORMAL)

        # Checkbox for "Replace original artists"
        self.replace_original_artist = BooleanVar(value=True)
        self.cb_replace_original_artist = Checkbutton(
            actions_frame, 
            text="Replace original artists", 
            variable=self.replace_original_artist,
            command=self.toggle_replace_original_artist
        )
        self.cb_replace_original_artist.grid(row=0, column=1, sticky=W, padx=5, pady=2)

        # Checkbox for "Overwrite existing values" (artist)
        self.overwrite_existing_original_artist = BooleanVar(value=False)
        self.cb_overwrite_existing_original_artist = Checkbutton(
            actions_frame, 
            text="Overwrite existing values", 
            variable=self.overwrite_existing_original_artist
        )
        self.cb_overwrite_existing_original_artist.grid(row=1, column=1, sticky=W, padx=5, pady=2)
        self.cb_overwrite_existing_original_artist.config(state=NORMAL)

        self.btn_load_files = Button(actions_frame, text="Select Folder", command=self.load_directory)
        self.btn_load_files.grid(row=0, column=2, rowspan=2, sticky=E, padx=5, pady=2)

        self.btn_save = Button(actions_frame, text="Save Changes", command=self.save_changes)
        self.btn_save.grid(row=0, column=3, rowspan=2, sticky=E, padx=5, pady=2)

        # Make the third column expand to push the buttons to the right
        actions_frame.grid_columnconfigure(2, weight=1)

        return actions_frame

    def toggle_replace_original_title(self):
        self.show_toast(toast_type.info, "aaa bbb ccc fff")
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

    def show_toast(self, type:toast_type, message:str, duration=3000):

        toast = Toplevel(self.root)
        toast.overrideredirect(True)  # Remove window decorations

        # Calculate the position for the bottom right corner
        self.root.update_idletasks()  # Ensure geometry info is up-to-date
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        toast.geometry(f"+{root_x + (root_width // 2) - 100}+{root_y + root_height - 100}")

        styles = {
            toast_type.error: {"bg": "red", "fg":"white"},
            toast_type.info: {"bg": "green", "fg":"black"},
        }
        
        style = styles.get(type, styles[toast_type.info])

        label = Label(toast, text=message, bg=style["bg"], fg=style["fg"], padx=10, pady=5)
        label.pack()

        self.root.after(duration, toast.destroy)  # Automatically destroy the toast after the duration

    @async_run
    async def get_server_health(self):
        try:
            api_is_healthy = await self.track_manager.get_server_health()
            if not api_is_healthy:
                self.show_toast(toast_type.error, "The server is not healthy. Please check the server status.")
        except httpx.RequestError as e:
            self.show_toast(toast_type.error, f"Could not reach the server at {self.api_host}:{self.api_port}. Please ensure the server is running and try again.\n\nDetails: {str(e)}")
        except Exception as e:
            self.show_toast(toast_type.error, f"An unexpected error occurred when trying to contact the server: {str(e)}")

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
            self.show_toast(toast_type.error, f"An error occurred when reading directory {directory}:{str(e)}")
        
        try:
            await self.track_manager.update_artists_info_from_db()
        except Exception as e:
            self.show_toast(toast_type.error,  f"An error occurred querying the server for information:{str(e)}")

        if self.replace_original_title:
            self.track_manager.replace_original_title(self.overwrite_existing_original_title)

        if self.overwrite_existing_original_artist:
            self.track_manager.replace_original_artist(self.replace_original_artist)

        self.create_track_tables(self.tables_inner_frame)

    def create_track_tables(self, master):
        self.clear_existing_track_frames(master)

        for track in self.track_manager.tracks:
            frame = Frame(master)
            frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

            self.populate_track_info(frame, track)
            tree = self.create_treeview(frame, track)
            self.populate_treeview(tree, track)

    def clear_existing_track_frames(self, master):
        for widget in master.winfo_children():
            widget.destroy()

    def populate_track_info(self, master, track):
        frame = Frame(master)
        frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

        # Use grid for alignment
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        update_file = BooleanVar(value=track.update_file)
        cb_update_file = Checkbutton(frame, text=f"{track.title}", variable=update_file, command=lambda t=track, v=update_file: self.update_update_file(t, v))
        cb_update_file.grid(column=0, row=0, sticky=W)

        label_current_track_artist = Label(frame, text=f"Artist: {"; ".join(track.artist)}")
        label_current_track_artist.grid(column=0, row=1, sticky=W)
        
        label_new_track_artist = Label(frame, text=f"Artist: {track.get_artist_string()}")
        label_new_track_artist.grid(column=0,row=2, sticky=W)

    def create_treeview(self, frame, track):
        tree = ttk.Treeview(frame, columns=tuple(self.data_mapping.keys()), show='headings', bootstyle=DEFAULT)

        num_rows = len(track.mbArtistDetails)
        row_height = 20
        tree_height = min(num_rows, 10) * row_height

        tree.pack(expand=True, fill=X, padx=10, pady=10)
        tree["height"] = num_rows

        display_columns = [column_id for column_id, settings in self.data_mapping.items() if settings.get("display", False)]
        tree["displaycolumns"] = display_columns

        for column_id, settings in self.data_mapping.items():
            tree.heading(column_id, text=settings["display_name"])
            tree.column(column_id, width=settings["width"])

        tree.bind("<Button-1>", self.on_single_click)
        tree.bind("<Double-1>", self.on_double_click)

        # Initialize the mapping dictionary for this treeview
        tree.item_to_object = {}
        
        return tree

    def populate_treeview(self, tree, track):
        for artist_detail in track.mbArtistDetails:
            values = self.get_treeview_row_values(track, artist_detail)
            row = tree.insert("", "end", values=tuple(values))

            # include needs to be handled differently since it gets converted to a checkbox
            if "include" in self.data_mapping and self.data_mapping["include"]["source_object"] == "mbartist_details":
                tree.set(row, 'include', '☑' if artist_detail.include else '☐')

            tree.item_to_object[row] = {"track": track, "artist_detail": artist_detail}

        self.enforce_column_widths(tree)

    def enforce_column_widths(self, tree):
        for column_id, settings in self.data_mapping.items():
            match column_id:
                case "include":
                    tree.column(column_id, minwidth=30, stretch=False)
                case "type":
                    tree.column(column_id, minwidth=60, stretch=False)
                case _:
                    tree.column(column_id, minwidth=70, stretch=True)

    def get_treeview_row_values(self, track, artist_detail):
        values = []
        for column_id, settings in self.data_mapping.items():
            if settings["source_object"] == "track_details":
                value = getattr(track, settings["property"], "")
            else:
                value = getattr(artist_detail, settings["property"], "")
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
            self.show_toast(toast_type.error, f"An error occurred when sending update data to the server:{str(e)}")
        
        try:
            await self.track_manager.save_files()
            self.show_toast(toast_type.error, "Metadata saved successfully!")
        except Exception as e:
            self.show_toast(toast_type.error, f"An error occurred when updating the files:{str(e)}")
        
        self.create_track_tables(self.tables_inner_frame)

    def get_clicked_cell(self, event, tree):
        region = tree.identify("region", event.x, event.y)

        if(region != "cell"):
            return None
        
        return {
            "row": tree.identify_row(event.y),
            "column": tree.identify_column(event.x)
        }

    def on_canvas_configure(self, e):
        self.tables_canvas.itemconfig(self.tables_canvas_window, width=e.width)
    
    def on_inner_frame_configure(self, e):
        self.tables_canvas.configure(scrollregion=self.tables_canvas.bbox("all"))
        
    def on_mousewheel(self, event):
        self.tables_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_single_click(self, event):
        tree = event.widget
        clicked = self.get_clicked_cell(event, tree)
        if (clicked == None):
            return
            
        # include is the only column that changes its value on a single click,
        # so it needs to be treated differently
        if ((tree.column(clicked["column"])["id"] == "include") and 
            (self.data_mapping[tree.column(clicked["column"])["id"]]["editable"] == True)):
            
            row_track = tree.item_to_object.get(clicked["row"])
            if (None == row_track):
                raise Exception("Row has no track details.")
            
            current_value = tree.set(clicked["row"], clicked["column"])
            # clicking doesn't automatically change the value, so we need to flip it
            new_value = False if current_value == '☑' else True

            valueChanged = self.save_value_to_manager(new_value, tree.column(clicked["column"])["id"], row_track["track"], row_track["artist_detail"])
            if(valueChanged == True):
                self.create_track_tables(self.tables_inner_frame)

    def on_double_click(self, event):
        tree = event.widget
        clicked = self.get_clicked_cell(event, tree)
        if(clicked == None):
            return

        if (self.data_mapping[tree.column(clicked["column"])["id"]]["editable"] == True):
            self.edit_cell(clicked["row"], clicked["column"], event, tree)

    def edit_cell(self, row, column, event, tree):
        # Create the Entry widget and place it at the cell position
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

            # Update the underlying data structure
            row_track = tree.item_to_object.get(row)
            if row_track is None:
                raise Exception("Row has no track details.")
            
            value_changed = self.save_value_to_manager(new_value, tree.column(column)["id"], row_track["track"], row_track["artist_detail"])
            
            if value_changed:
                self.create_track_tables(self.tables_inner_frame)
        
        def close_without_saving(event):
            entry.destroy()

        entry.bind("<Return>", save_new_value)
        entry.bind("<FocusOut>", save_new_value)
        entry.bind("<Escape>", close_without_saving)

    def save_value_to_manager(self, new_value, column_id:str, track_details, mbartist_details) -> bool:
        if column_id not in self.data_mapping:
            raise Exception(f"column id {column_id} was not found in data mapping.")
        
        # Retrieve the object and attribute name
        mapping = self.data_mapping[column_id]
        if(mapping["source_object"] == "track_details"):
            source_obj = track_details
        else:
            source_obj = mbartist_details

        current_value = getattr(source_obj, mapping["property"])

        if new_value == current_value:
            return False

        # Update the value
        setattr(source_obj, mapping["property"], new_value)
        return True

    def run_sync(self, async_func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_func(*args, **kwargs))

def main():
    parser = argparse.ArgumentParser(
    prog = 'Artist Relation Resolver')
    parser.add_argument('-s', '--host', type=str, required=False ,help="host of the Artist Relation Resolver API")
    parser.add_argument('-p', '--port', type=str, required=False ,help="Port of the Artist Relation Resolver API")

    args = parser.parse_args()

    api_host = args.host if args.host else os.getenv('ARTIST_RESOLVER_HOST', None)
    api_port = args.port if args.port else os.getenv('ARTIST_RESOLVER_PORT', None)

    root = ttk.Window(themename="darkly")
    
    app = TrackManagerGUI(root, api_host, api_port)
    root.mainloop()

if __name__ == "__main__":
    main()
