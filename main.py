import asyncio
from tkinter import *
from tkinter import filedialog, messagebox, ttk

from TrackManager import TrackManager

class TrackManagerGUI:
    # Mapping between columns and source data in format
    data_mapping = {
        "file_path": {"source_object":"track_details", "property":"file_path", "display_name":"File Path", "width":100, "editable":False, "display":False},
        "update_file": {"source_object":"track_details", "property":"update_file", "display_name":"Update", "width":100, "editable":False, "display":False},
        "title": {"source_object":"track_details", "property":"title", "display_name":"Track Title", "width":100, "editable":False, "display":False},
        "original_title": {"source_object":"track_details", "property":"original_title", "display_name":"Orig Title", "width":100, "editable":False, "display":False},
        "track_artist": {"source_object":"track_details", "property":"artist", "display_name":"Track Artist", "width":100, "editable":False, "display":False},
        "artist": {"source_object":"mbartist_details", "property":"name", "display_name":"Artist", "width":100, "editable":False, "display":True},
        "artist_sort": {"source_object":"mbartist_details", "property":"sort_name", "display_name":"Sort Artist", "width":100, "editable":False, "display":False},
        "original_artist": {"source_object":"track_details", "property":"original_artist", "display_name":"Orig Artist", "width":100, "editable":False, "display":False},
        "album": {"source_object":"track_details", "property":"album", "display_name":"Album", "width":100, "editable":False, "display":True},
        "product": {"source_object":"track_details", "property":"product", "display_name":"Product", "width":100, "editable":False, "display":False},
        "original_album": {"source_object":"track_details", "property":"original_album", "display_name":"Orig Album", "width":100, "editable":False, "display":False},
        "album_artist": {"source_object":"track_details", "property":"album_artist", "display_name":"Album Artist", "width":100, "editable":False, "display":False},
        "grouping": {"source_object":"track_details", "property":"grouping", "display_name":"Grouping", "width":100, "editable":False, "display":False},
        "include": {"source_object":"mbartist_details", "property":"include", "display_name":"Set", "width":10, "editable":True, "display":True},
        "mbid": {"source_object":"mbartist_details", "property":"mbid", "display_name":"MBID", "width":100, "editable":False, "display":False},
        "type": {"source_object":"mbartist_details", "property":"type", "display_name":"Type", "width":100, "editable":False, "display":True},
        "joinphrase": {"source_object":"mbartist_details", "property":"joinphrase", "display_name":"Join Phrase", "width":100, "editable":False, "display":False},
        "custom_name": {"source_object":"mbartist_details", "property":"custom_name", "display_name":"Custom Name", "width":100, "editable":True, "display":True},
        "custom_original_name": {"source_object":"mbartist_details", "property":"custom_original_name", "display_name":"Custom Orig Name", "width":100, "editable":True, "display":True}
    }

    def __init__(self, root):
        self.root = root
        self.track_manager = TrackManager()
        self.item_to_object = {}
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Track Manager")
        self.root.geometry("700x380")
        self.root.minsize(800,400)
        self.root.resizable(True, True)

        self.setup_layout()

    def setup_layout(self):
        # main frame to hold elements
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)
        
        self.tables_frame = Frame(main_frame)
        self.tables_frame.pack(padx=10, pady=10, fill=BOTH, expand=True)

        # frames don't support scrollbars by themselves, so we need to define a canvaas
        self.tables_canvas = Canvas(self.tables_frame)
        self.tables_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # Add a scrollbar to the tables_frame
        self.scrollbar = Scrollbar(self.tables_frame, orient=VERTICAL, command=self.tables_canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.inner_frame = Frame(self.tables_canvas)
        self.tables_canvas_window = self.tables_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.buttons_frame = Frame(main_frame)
        self.buttons_frame.pack(padx=10, pady=10, side=BOTTOM)

        # Button to choose directory
        self.btn_select_dir = Button(self.buttons_frame, text="Select Folder", command=self.load_directory)
        self.btn_select_dir.pack(side=RIGHT)

        # Button to update metadata
        self.update_button = Button(self.buttons_frame, text="Save Changes", command=self.save_changes)
        self.update_button.pack(pady=10, side=RIGHT)

        self.tables_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.tables_canvas.bind('<Configure>', self.on_canvas_configure)
        self.tables_canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        self.inner_frame.bind('<Configure>', self.on_inner_frame_configure)


    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            try:
                self.track_manager = TrackManager()
                asyncio.run(self.track_manager.load_directory(directory))
                asyncio.run(self.track_manager.update_artists_info_from_db())
                
                self.populate_tables()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def populate_tables(self):
        # Clear existing frames
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # Populate a new table for each track
        for track in self.track_manager.tracks:
            frame = Frame(self.inner_frame)
            frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

            file_path_label = Label(frame, text=f"File Path: {track.file_path}")
            file_path_label.pack()

            title_label = Label(frame, text=f"Title: {track.title}")
            title_label.pack()

            formatted_artist = track.get_artist_string()
            formatted_artist_label = Label(frame, text=f"Artist: {formatted_artist}")
            formatted_artist_label.pack()

            # Checkbox to enable or disable file updates
            update_file_var = BooleanVar(value=track.update_file)
            update_file_checkbox = Checkbutton(frame, text="Update File", variable=update_file_var, command=lambda t=track, v=update_file_var: self.update_update_file(t, v))
            update_file_checkbox.pack()

            tree = ttk.Treeview(frame, columns=tuple(self.data_mapping.keys()), show='headings')

            # Calculate the appropriate height based on the number of rows
            num_rows = len(track.mbArtistDetails)
            row_height = 20  # Height of each row in pixels
            tree_height = min(num_rows, 10) * row_height  # Max height to show 10 rows at a time

            tree.pack(expand=True, fill=X, padx=10, pady=10)
            tree["height"] = num_rows

            display_columns = [column_id for column_id, settings in self.data_mapping.items() if settings.get("display", False)]
            tree["displaycolumns"] = display_columns

            # Set properties for each column
            for column_id, settings in self.data_mapping.items():
                tree.heading(column_id, text=settings["display_name"])
                tree.column(column_id, width=settings["width"])

            tree.bind("<Button-1>", self.on_single_click)
            tree.bind("<Double-1>", self.on_double_click)

            # Populate the tree with new data
            for artist_detail in track.mbArtistDetails:
                values = []
                for column_id, settings in self.data_mapping.items():
                    # Determine the source object and property
                    if settings["source_object"] == "track_details":
                        value = getattr(track, settings["property"], "")
                    else:
                        value = getattr(artist_detail, settings["property"], "")

                    values.append(value)

                # Insert the new row into the treeview
                row = tree.insert("", "end", values=tuple(values))

                if "include" in self.data_mapping and self.data_mapping["include"]["source_object"] == "mbartist_details":
                    tree.set(row, 'include', '☑' if artist_detail.include == True else '☐')

                # Map the row to the corresponding objects for reference
                self.item_to_object[row] = {"track": track, "artist_detail": artist_detail}

    def update_update_file(self, track, var):
        new_value = var.get()
        if track.update_file != new_value:
            track.update_file = new_value

    def save_changes(self):
        try:
            asyncio.run(self.track_manager.send_changes_to_db())
            asyncio.run(self.track_manager.save_files())
            self.populate_tables()
            messagebox.showinfo("Success", "Metadata saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
            
            row_track = self.item_to_object.get(clicked["row"])
            if (None == row_track):
                raise Exception("Row has no track details.")
            
            current_value = tree.set(clicked["row"], clicked["column"])
            # clicking doesn't automatically change the value, so we need to flip it
            new_value = False if current_value == '☑' else True

            valueChanged = self.save_value_to_manager(new_value, tree.column(clicked["column"])["id"], row_track["track"], row_track["artist_detail"])
            if(valueChanged == True):
                self.populate_tables()


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
            row_track = self.item_to_object.get(row)
            if row_track is None:
                raise Exception("Row has no track details.")
            
            value_changed = self.save_value_to_manager(new_value, tree.column(column)["id"], row_track["track"], row_track["artist_detail"])
            
            if value_changed:
                self.populate_tables()
        
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
    root = Tk()
    app = TrackManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
