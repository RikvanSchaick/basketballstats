from tkinter import *

# Root window
root = Tk()

# Window title & dimension
root.title("BOB stats")
root.geometry('350x200')

# Window Content
lbl =Label(root, text = "Test")
lbl.grid()

# Text input
txt = Entry(root, width=10)
txt.grid(column=1, row=0)

# Button
def clicked():
    res = "You wrote " + txt.get()
    lbl.configure(text=res)

btn = Button(root, text="Click me",
             fg="red", command=clicked)
btn.grid(column=2, row=0)

# Menu
menu =Menu(root)
item = Menu(menu)
item.add_command(label='New')
menu.add_cascade(label="File", menu=item)
root.config(menu=menu)

# Execute window
root.mainloop()