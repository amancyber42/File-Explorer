import os
import pathlib
import ctypes
from tkinter import *
from tkinter import messagebox

# --- KONFIGURACIJA ---

# Povećanje DPI svijesti za oštriji prikaz na Windows sustavima
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except (AttributeError, OSError):
    print("Nije moguće postaviti DPI svijest (vjerojatno niste na Windowsima).")

# Glavni prozor aplikacije
root = Tk()
root.title("File Explorer")
root.geometry("800x600")

# Konfiguracija redaka i stupaca da se rastežu s prozorom
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(2, weight=1)

# --- Varijable za povijest navigacije ---
path_history = []
current_history_index = -1

# --- FUNKCIJE ---

def update_navigation_buttons():
    """Ažurira stanje gumbiju 'Nazad' i 'Naprijed'."""
    back_button.config(state=NORMAL if current_history_index > 0 else DISABLED)
    forward_button.config(state=NORMAL if current_history_index < len(path_history) - 1 else DISABLED)

def populate_file_list(path_str):
    """
    Popunjava listbox s datotekama i mapama iz zadane putanje.
    """
    try:
        path_obj = pathlib.Path(path_str)
        if not path_obj.is_dir():
            messagebox.showerror("Greška", f"Putanja nije direktorij: {path_str}")
            return

        directory_contents = sorted(list(path_obj.iterdir()), key=lambda p: (not p.is_dir(), str(p).lower()))
        file_listbox.delete(0, END)

        for item in directory_contents:
            display_name = f"📁 {item.name}" if item.is_dir() else f"📄 {item.name}"
            file_listbox.insert(END, display_name)
            if item.is_dir():
                file_listbox.itemconfig(END, {'fg': '#00529B'})

    except PermissionError:
        messagebox.showerror("Greška", "Nemate dozvolu za pristup ovoj mapi.")
        current_path.set(path_history[current_history_index]) # Vrati na prethodnu ispravnu putanju
    except Exception as e:
        messagebox.showerror("Greška", f"Dogodila se neočekivana greška: {e}")

def on_path_change(*args):
    """
    Okidač koji se poziva svaki put kad se varijabla current_path promijeni.
    Samo ažurira prikaz i stanje gumbiju.
    """
    new_path = current_path.get()
    populate_file_list(new_path)
    update_navigation_buttons()

def navigate(new_path_str):
    """
    Glavna funkcija za novu navigaciju. Ažurira povijest i postavlja novu putanju.
    """
    global path_history, current_history_index

    # Obriši "forward" povijest ako idemo na novu putanju (ne preko gumba naprijed/nazad)
    if current_history_index < len(path_history) - 1:
        path_history = path_history[:current_history_index + 1]
    
    # Dodaj novu putanju u povijest
    path_history.append(new_path_str)
    current_history_index += 1
    
    # Postavi novu putanju, što će okinuti on_path_change
    current_path.set(new_path_str)

def on_item_select(event=None):
    """
    Funkcija koja se poziva dvostrukim klikom ili pritiskom na Enter.
    Otvara datoteku ili ulazi u mapu koristeći 'navigate' funkciju.
    """
    selection_indices = file_listbox.curselection()
    if not selection_indices:
        return

    selected_item_name = file_listbox.get(selection_indices[0]).split(' ', 1)[1]
    new_path = pathlib.Path(current_path.get()) / selected_item_name

    try:
        if new_path.is_file():
            os.startfile(new_path)
        elif new_path.is_dir():
            # Za ulazak u mapu koristimo novu 'navigate' funkciju
            navigate(str(new_path))
    except Exception as e:
        messagebox.showerror("Greška", f"Nije moguće otvoriti '{new_path.name}':\n{e}")

def go_up():
    """Vraća se u nadređeni direktorij koristeći 'navigate' funkciju."""
    parent_path = pathlib.Path(current_path.get()).parent
    navigate(str(parent_path))

def go_back():
    """Vraća se natrag u povijesti."""
    global current_history_index
    if current_history_index > 0:
        current_history_index -= 1
        # Direktno postavlja putanju iz povijesti, ne zovemo navigate()
        current_path.set(path_history[current_history_index])

def go_forward():
    """Ide naprijed u povijesti."""
    global current_history_index
    if current_history_index < len(path_history) - 1:
        current_history_index += 1
        # Direktno postavlja putanju iz povijesti, ne zovemo navigate()
        current_path.set(path_history[current_history_index])

def create_new_item(item_type):
    """Stvara novu datoteku ili mapu u trenutnom direktoriju."""
    item_name = new_item_name.get()
    if not item_name:
        messagebox.showwarning("Upozorenje", "Ime ne može biti prazno.")
        return

    full_path = pathlib.Path(current_path.get()) / item_name

    if full_path.exists():
        messagebox.showerror("Greška", f"'{item_name}' već postoji na ovoj lokaciji.")
        return
    
    try:
        if item_type == 'file':
            full_path.touch()
        elif item_type == 'folder':
            full_path.mkdir()
        
        popup_window.destroy()
        populate_file_list(current_path.get())

    except Exception as e:
        messagebox.showerror("Greška", f"Nije moguće stvoriti '{item_name}':\n{e}")

def open_creation_popup():
    """Otvara popup prozor za stvaranje nove datoteke ili mape."""
    global popup_window, new_item_name
    
    popup_window = Toplevel(root)
    popup_window.title("Stvori novo")
    popup_window.geometry("300x150")
    popup_window.resizable(False, False)
    popup_window.transient(root)
    popup_window.grab_set()

    new_item_name = StringVar(popup_window)

    Label(popup_window, text="Unesite ime:").pack(pady=5)
    Entry(popup_window, textvariable=new_item_name, width=40).pack(pady=5, padx=10)
    
    button_frame = Frame(popup_window)
    button_frame.pack(pady=10)

    Button(button_frame, text="Stvori datoteku", command=lambda: create_new_item('file')).pack(side=LEFT, padx=5)
    Button(button_frame, text="Stvori mapu", command=lambda: create_new_item('folder')).pack(side=LEFT, padx=5)

    root.wait_window(popup_window)

# --- VARIJABLE I WIDGETI ---

current_path = StringVar()
current_path.trace_add('write', on_path_change)

# --- Gornja traka (Navigacija) ---
top_frame = Frame(root)
top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5), padx=5)
top_frame.grid_columnconfigure(3, weight=1)

# Gumbi za navigaciju
back_button = Button(top_frame, text="← Nazad", command=go_back, state=DISABLED)
back_button.grid(row=0, column=0, padx=(0,2), pady=5)

forward_button = Button(top_frame, text="Naprijed →", command=go_forward, state=DISABLED)
forward_button.grid(row=0, column=1, padx=2, pady=5)

# up_button = Button(top_frame, text="↑ Gore", command=go_up)
# up_button.grid(row=0, column=2, padx=(2,10), pady=5)

path_entry = Entry(top_frame, textvariable=current_path, font=("Segoe UI", 10))
path_entry.grid(row=0, column=3, sticky="ew", pady=5)

# --- Meni traka ---
menubar = Menu(root)
root.config(menu=menubar)

file_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Datoteka", menu=file_menu)
file_menu.add_command(label="Stvori novo...", command=open_creation_popup)
file_menu.add_separator()
file_menu.add_command(label="Izađi", command=root.quit)

# --- Glavni dio (Lista datoteka) ---
list_frame = Frame(root)
list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
list_frame.grid_rowconfigure(0, weight=1)
list_frame.grid_columnconfigure(0, weight=1)

file_listbox = Listbox(list_frame, font=("Segoe UI", 11), selectbackground="#DDEEFF", selectforeground="black")
file_listbox.grid(row=0, column=0, sticky="nsew")

scrollbar = Scrollbar(list_frame, orient=VERTICAL, command=file_listbox.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
file_listbox.config(yscrollcommand=scrollbar.set)

file_listbox.bind('<Double-1>', on_item_select)
file_listbox.bind('<Return>', on_item_select)

# --- INICIJALIZACIJA ---

# Postavljanje početne putanje i povijesti
initial_path = str(pathlib.Path.home())
path_history.append(initial_path)
current_history_index = 0
current_path.set(initial_path)

root.mainloop()

