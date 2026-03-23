import tkinter as tk

root = tk.Tk()
root.title("Obsidian Elite - Preview")
root.geometry("360x640")  # Format iPhone standard
root.configure(bg='black')

# Zone Haute : Graphique ETH
high_zone = tk.Frame(root, bg='black', highlightbackground="#333", highlightthickness=1)
high_zone.place(relx=0.05, rely=0.02, relwidth=0.9, relheight=0.45)
tk.Label(high_zone, text="CHART ETH (LIVE)", fg="white", bg="black").pack(expand=True)

# Zone Milieu : Macro Data (FED / CPI)
mid_zone = tk.Frame(root, bg='black', highlightbackground="#333", highlightthickness=1)
mid_zone.place(relx=0.05, rely=0.49, relwidth=0.9, relheight=0.1)
tk.Label(mid_zone, text="FED: 3.72%  |  CPI: 326.03", fg="#00FF00", bg="black", font=("Arial", 10, "bold")).pack(expand=True)

# Zone Basse : Future Extension
low_zone = tk.Frame(root, bg='black', highlightbackground="#333", highlightthickness=1)
low_zone.place(relx=0.05, rely=0.61, relwidth=0.9, relheight=0.35)
tk.Label(low_zone, text="ZONE RÉSERVÉE", fg="#555", bg="black").pack(expand=True)

root.mainloop()
