"""
interface.py — Interface gráfica do Atualizador
================================================
UI em Tkinter com visual limpo e feedback em tempo real.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import threading

from processor import atualizar_base


# ──────────────────────────────────────────────────────────────────────────────
# PALETA DE CORES
# ──────────────────────────────────────────────────────────────────────────────

COR = {
    'bg':          '#F8F7F4',
    'card':        '#FFFFFF',
    'borda':       '#E0DED8',
    'borda_foco':  '#185FA5',
    'texto':       '#1A1A1A',
    'texto_sec':   '#5F5E5A',
    'texto_hint':  '#A09E98',
    'verde':       '#1D9E75',
    'verde_hover': '#0F6E56',
    'azul':        '#185FA5',
    'vermelho':    '#A32D2D',
    'amarelo_bg':  '#FAEEDA',
    'amarelo_tx':  '#633806',
}


# ──────────────────────────────────────────────────────────────────────────────
# COMPONENTES REUTILIZÁVEIS
# ──────────────────────────────────────────────────────────────────────────────

class FileSelector(tk.Frame):
    """Campo de seleção de arquivo com label, entrada readonly e botão."""

    def __init__(self, parent, numero, label, filetypes, **kwargs):
        super().__init__(parent, bg=COR['card'], **kwargs)
        self.filetypes = filetypes
        self.path_var = tk.StringVar()

        # Número do passo
        num_lbl = tk.Label(self, text=str(numero), bg=COR['azul'], fg='white',
                           font=('Arial', 10, 'bold'), width=2, height=1)
        num_lbl.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky='ns')

        # Label
        tk.Label(self, text=label, bg=COR['card'], fg=COR['texto'],
                 font=('Arial', 10, 'bold'), anchor='w').grid(
            row=0, column=1, columnspan=2, sticky='ew', pady=(0, 4))

        # Entrada
        self.entry = tk.Entry(self, textvariable=self.path_var, state='readonly',
                              readonlybackground='#F1EFE8', fg=COR['texto_sec'],
                              relief='flat', bd=0, font=('Arial', 9),
                              highlightthickness=1, highlightbackground=COR['borda'],
                              highlightcolor=COR['borda_foco'])
        self.entry.grid(row=1, column=1, sticky='ew', ipady=6, padx=(0, 8))

        # Botão
        self.btn = tk.Button(self, text='Procurar', bg=COR['bg'], fg=COR['azul'],
                             font=('Arial', 9, 'bold'), relief='flat', bd=0,
                             cursor='hand2', padx=12, pady=4,
                             highlightthickness=1, highlightbackground=COR['borda'],
                             activebackground=COR['borda'], command=self._selecionar)
        self.btn.grid(row=1, column=2, sticky='ew')
        self.btn.bind('<Enter>', lambda e: self.btn.config(bg=COR['borda']))
        self.btn.bind('<Leave>', lambda e: self.btn.config(bg=COR['bg']))

        self.columnconfigure(1, weight=1)

    def _selecionar(self):
        path = filedialog.askopenfilename(filetypes=self.filetypes)
        if path:
            self.path_var.set(path)

    def get(self):
        return self.path_var.get()

    def set_error(self, erro=True):
        color = COR['vermelho'] if erro else COR['borda']
        self.entry.config(highlightcolor=color, highlightbackground=color)


class ProgressCard(tk.Frame):
    """Card com barra de progresso e mensagem de status."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COR['card'],
                         highlightthickness=1, highlightbackground=COR['borda'], **kwargs)
        self._visible = False

        self.lbl_status = tk.Label(self, text='', bg=COR['card'], fg=COR['texto_sec'],
                                   font=('Arial', 9), anchor='w')
        self.lbl_status.pack(fill='x', padx=16, pady=(14, 4))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Verde.Horizontal.TProgressbar',
                        troughcolor=COR['borda'], background=COR['verde'],
                        bordercolor=COR['card'], lightcolor=COR['verde'],
                        darkcolor=COR['verde'])

        self.bar = ttk.Progressbar(self, style='Verde.Horizontal.TProgressbar',
                                   length=400, mode='determinate', maximum=100)
        self.bar.pack(fill='x', padx=16, pady=(0, 14))

    def update(self, valor, mensagem):
        self.lbl_status.config(text=mensagem)
        self.bar['value'] = valor

    def reset(self):
        self.bar['value'] = 0
        self.lbl_status.config(text='')


class InfoBadge(tk.Label):
    """Pequena tag colorida para exibir informações."""

    def __init__(self, parent, texto, cor_bg, cor_tx, **kwargs):
        super().__init__(parent, text=texto, bg=cor_bg, fg=cor_tx,
                         font=('Arial', 8, 'bold'), padx=8, pady=2,
                         relief='flat', **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# APLICAÇÃO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

class AppAtualizador:

    def __init__(self, root):
        self.root = root
        self._configurar_janela()
        self._construir_ui()

    # ── Configuração da janela ────────────────────────────────────────────────

    def _configurar_janela(self):
        self.root.title('Atualizador — Base Unificada BI · Programa Redenção')
        self.root.geometry('620x580')
        self.root.resizable(False, False)
        self.root.configure(bg=COR['bg'])

        # Centralizar na tela
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self.root, bg=COR['bg'])
        outer.pack(fill='both', expand=True, padx=24, pady=20)

        # ── Cabeçalho ────────────────────────────────────────────────────────
        header = tk.Frame(outer, bg=COR['bg'])
        header.pack(fill='x', pady=(0, 20))

        tk.Label(header, text='Base Unificada BI', bg=COR['bg'], fg=COR['texto'],
                 font=('Arial', 18, 'bold')).pack(anchor='w')
        tk.Label(header, text='Programa Redenção · SEPE — São Paulo',
                 bg=COR['bg'], fg=COR['texto_sec'], font=('Arial', 10)).pack(anchor='w')

        # Linha separadora
        sep = tk.Frame(outer, height=1, bg=COR['borda'])
        sep.pack(fill='x', pady=(0, 20))

        # ── Card de seleção de arquivos ───────────────────────────────────────
        card_files = tk.Frame(outer, bg=COR['card'],
                              highlightthickness=1, highlightbackground=COR['borda'])
        card_files.pack(fill='x', pady=(0, 12))

        tk.Label(card_files, text='Arquivos', bg=COR['card'], fg=COR['texto_sec'],
                 font=('Arial', 8, 'bold')).pack(anchor='w', padx=16, pady=(14, 10))

        self.sel_base = FileSelector(
            card_files, 1,
            'Base Unificada atual do (Base do PowerBI)  (.xlsx)',
            [('Arquivos Excel', '*.xlsx')]
        )
        self.sel_base.pack(fill='x', padx=16, pady=(0, 14))

        tk.Frame(card_files, height=1, bg=COR['borda']).pack(fill='x', padx=16)

        self.sel_diario = FileSelector(
            card_files, 2,
            'Registro Diário (base de perfil online) (.xlsx ou .csv)',
            [('Planilhas suportadas', '*.xlsx *.csv'),
             ('Excel', '*.xlsx'), ('CSV', '*.csv')]
        )
        self.sel_diario.pack(fill='x', padx=16, pady=(14, 16))

        # ── Card de regras aplicadas ──────────────────────────────────────────
        card_regras = tk.Frame(outer, bg=COR['amarelo_bg'],
                               highlightthickness=1, highlightbackground='#FAC775')
        card_regras.pack(fill='x', pady=(0, 12))

        tk.Label(card_regras, text='Regras aplicadas automaticamente',
                 bg=COR['amarelo_bg'], fg=COR['amarelo_tx'],
                 font=('Arial', 8, 'bold')).pack(anchor='w', padx=14, pady=(10, 6))

        regras_frame = tk.Frame(card_regras, bg=COR['amarelo_bg'])
        regras_frame.pack(fill='x', padx=14, pady=(0, 10))

        regras = [
            ('Gênero / Sexo', 'CIS · TRANS · NÃO INFORMADO'),
            ('IST · TB · PcD', 'SIM · NÃO · NÃO INFORMADO'),
            ('Pop Rua · Usuário', 'SIM · NÃO · NÃO INFORMADO'),
            ('Território', 'Padronização canônica'),
            ('Enriquecimento', 'Intra-dia por ID + Data'),
            ('MV', 'Cálculo consolidado por ID'),
        ]
        for i, (campo, desc) in enumerate(regras):
            col = i % 3
            row = i // 3
            f = tk.Frame(regras_frame, bg=COR['amarelo_bg'])
            f.grid(row=row, column=col, sticky='w', padx=(0, 16), pady=1)
            tk.Label(f, text=f'• {campo}:', bg=COR['amarelo_bg'],
                     fg=COR['amarelo_tx'], font=('Arial', 8, 'bold')).pack(side='left')
            tk.Label(f, text=f' {desc}', bg=COR['amarelo_bg'],
                     fg=COR['amarelo_tx'], font=('Arial', 8)).pack(side='left')

        # ── Progresso ────────────────────────────────────────────────────────
        self.progress = ProgressCard(outer)
        self.progress.pack(fill='x', pady=(0, 12))

        # ── Botão principal ───────────────────────────────────────────────────
        self.btn_executar = tk.Button(
            outer, text='▶   Atualizar Base Unificada',
            bg=COR['verde'], fg='white',
            font=('Arial', 12, 'bold'),
            relief='flat', bd=0, cursor='hand2',
            padx=0, pady=12,
            activebackground=COR['verde_hover'],
            activeforeground='white',
            command=self._executar
        )
        self.btn_executar.pack(fill='x')
        self.btn_executar.bind('<Enter>', lambda e: self.btn_executar.config(bg=COR['verde_hover']))
        self.btn_executar.bind('<Leave>', lambda e: self.btn_executar.config(bg=COR['verde']))

        # ── Rodapé ────────────────────────────────────────────────────────────
        tk.Label(outer, text='SEPE · Secretaria Executiva de Projetos Estratégicos · São Paulo',
                 bg=COR['bg'], fg=COR['texto_hint'], font=('Arial', 8)).pack(pady=(12, 0))

    # ── Lógica de execução ────────────────────────────────────────────────────

    def _executar(self):
        base   = self.sel_base.get()
        diario = self.sel_diario.get()

        valido = True
        if not base:
            self.sel_base.set_error(True)
            valido = False
        else:
            self.sel_base.set_error(False)

        if not diario:
            self.sel_diario.set_error(True)
            valido = False
        else:
            self.sel_diario.set_error(False)

        if not valido:
            messagebox.showwarning('Arquivos faltando',
                                   'Selecione ambos os arquivos antes de continuar.')
            return

        data_hoje = datetime.now().strftime('%d_%m_%Y')
        path_saida = filedialog.asksaveasfilename(
            title='Salvar Base Atualizada Como...',
            defaultextension='.xlsx',
            filetypes=[('Arquivos Excel', '*.xlsx')],
            initialfile=f'BASEBI_{data_hoje}_PERFIS.xlsx'
        )
        if not path_saida:
            return

        self.btn_executar.config(state='disabled', text='Processando...',
                                 bg='#888780', cursor='watch')
        self.progress.reset()
        self.root.update()

        def _rodar():
            def _cb(pct, msg):
                self.root.after(0, lambda: self.progress.update(pct, msg))
                self.root.after(0, self.root.update)

            sucesso, mensagem = atualizar_base(base, diario, path_saida, callback=_cb)
            self.root.after(0, lambda: self._finalizar(sucesso, mensagem))

        threading.Thread(target=_rodar, daemon=True).start()

    def _finalizar(self, sucesso, mensagem):
        self.btn_executar.config(state='normal',
                                 text='▶   Atualizar Base BI',
                                 bg=COR['verde'], cursor='hand2')
        if sucesso:
            self.progress.update(100, 'Concluído com sucesso.')
            messagebox.showinfo('Concluído', mensagem)
        else:
            self.progress.update(0, 'Erro durante o processamento.')
            messagebox.showerror('Erro', mensagem)
