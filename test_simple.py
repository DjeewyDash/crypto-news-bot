import tkinter as tk

try:
    root = tk.Tk()
    root.title("Elite Preview")
    root.geometry("360x640")
    root.configure(bg='black')

    # Label de test
    label = tk.Label(root, text="SI TU VOIS CECI,\nCA FONCTIONNE !", fg="white", bg="black", font=("Arial", 14))
    label.pack(expand=True)

    print("Lancement de la fenêtre...")
    root.mainloop()
except Exception as e:
    print(f"Erreur : {e}")
