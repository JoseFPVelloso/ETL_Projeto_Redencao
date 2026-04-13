"""
Atualizador da Base Unificada — Programa Redenção (SEPE)
=========================================================
Ponto de entrada. Execute este arquivo para abrir a interface.

    python main.py
"""

from interface import AppAtualizador
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = AppAtualizador(root)
    root.mainloop()