import tkinter as tk
import random
import sys
import os
import subprocess

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
SECRET_CODE = "31415"
MAX_LEVEL   = 9      # nivel 9 → 10 números → ganar

BG       = "#000000"
FG       = "#FFFFFF"
YELLOW   = "#FFDC32"
GREEN    = "#50C850"
RED      = "#DC3C3C"
CYAN     = "#50DCDC"
GRAY     = "#A0A0A0"
DARK_BOX = "#141428"

FONT_HUGE  = ("Arial", 96,  "bold")
FONT_BIG   = ("Arial", 60,  "bold")
FONT_MED   = ("Arial", 38,  "bold")
FONT_SMALL = ("Arial", 28)
FONT_TINY  = ("Arial", 20)

# Milisegundos a esperar tras perder el foco antes de reclamar la ventana
FOCUS_DELAY_MS = 1000


# ─────────────────────────────────────────────
#  REINICIO DEL PROCESO
# ─────────────────────────────────────────────
def restart_game():
    """Lanza una nueva instancia del script y cierra la actual."""
    python = sys.executable
    script = os.path.abspath(__file__)
    subprocess.Popen([python, script])
    os._exit(0)


# ─────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────
class MemoryGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Juego de Memoria Numérica")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)   # siempre encima de otras apps
        self.root.configure(bg=BG)

        # ── Bloquear cierres y atajos de escape ───────────────────────
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_attempt)
        self.root.bind("<Escape>",    lambda e: "break")
        self.root.bind("<Alt-F4>",    lambda e: "break")
        self.root.bind("<Control-w>", lambda e: "break")
        self.root.bind("<Control-q>", lambda e: "break")
        self.root.bind("<Super_L>",   lambda e: "break")   # tecla Windows
        self.root.bind("<Super_R>",   lambda e: "break")

        # ── Vigilar pérdida de foco ────────────────────────────────────
        self._allow_unfocus = False   # True solo cuando se sale legalmente
        self.root.bind("<FocusOut>", self._on_focus_out)

        self.W = self.root.winfo_screenwidth()
        self.H = self.root.winfo_screenheight()

        # Estado del juego
        self.level    = 1
        self.sequence = []
        self.seq_idx  = 0

        # Canvas único para todas las pantallas
        self.canvas = tk.Canvas(root, width=self.W, height=self.H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # Input oculto para código secreto
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(root, textvariable=self.entry_var,
                              font=FONT_BIG, bg="#1a1a2e", fg=YELLOW,
                              insertbackground=YELLOW, justify="center",
                              relief="flat", bd=0,
                              highlightthickness=3,
                              highlightcolor=CYAN,
                              highlightbackground=GRAY)

        self.show_instructions()

    # ──────────────────────────────────────────
    #  GESTIÓN DE CIERRE Y FOCO
    # ──────────────────────────────────────────
    def _on_close_attempt(self):
        """El usuario intentó cerrar la ventana → reiniciar el juego desde 0."""
        self._allow_unfocus = True
        restart_game()

    def _on_focus_out(self, event):
        """La ventana perdió el foco → programar la recuperación."""
        if self._allow_unfocus:
            return
        self.root.after(FOCUS_DELAY_MS, self._reclaim_focus)

    def _reclaim_focus(self):
        """Devuelve la ventana al frente y le devuelve el foco."""
        if self._allow_unfocus:
            return
        try:
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
            if self.entry.winfo_ismapped():
                self.entry.focus_set()
        except Exception:
            pass

    # ──────────────────────────────────────────
    #  UTILIDADES CANVAS
    # ──────────────────────────────────────────
    def clear(self):
        self.canvas.delete("all")
        self.entry.place_forget()
        for attr in ("_after_seq", "_after_blink"):
            job = getattr(self, attr, None)
            if job:
                self.root.after_cancel(job)
                setattr(self, attr, None)

    def text(self, x_pct, y_pct, txt, font=FONT_SMALL, color=FG, anchor="center"):
        self.canvas.create_text(
            self.W * x_pct, self.H * y_pct,
            text=txt, font=font, fill=color, anchor=anchor
        )

    def rect_btn(self, x_pct, y_pct, w, h, label, fg, border, tag=None):
        cx, cy = self.W * x_pct, self.H * y_pct
        x0, y0 = cx - w // 2, cy - h // 2
        x1, y1 = cx + w // 2, cy + h // 2
        t = tag or f"btn_{x_pct}_{y_pct}"
        self.canvas.create_rectangle(x0, y0, x1, y1,
                                     fill=DARK_BOX, outline=border,
                                     width=3, tags=t)
        self.canvas.create_text(cx, cy, text=label,
                                font=FONT_MED, fill=fg, tags=t)
        return t

    # ──────────────────────────────────────────
    #  INSTRUCCIONES
    # ──────────────────────────────────────────
    def show_instructions(self):
        self.clear()
        self.text(0.5, 0.07, "─── JUEGO DE MEMORIA NUMÉRICA ───",
                  FONT_MED, YELLOW)
        lines = [
            (0.19, "Cómo jugar:",                                    CYAN),
            (0.27, "Aparecerán números en pantalla uno tras otro.",   FG),
            (0.34, "Después se te hará una pregunta sobre",           FG),
            (0.41, "qué número ocupaba cierta posición.",             YELLOW),
            (0.50, "Nivel 1 → 2 números  ···  Nivel 9 → 10 números", FG),
            (0.59, "Si fallas, vuelves al nivel 1.",                  RED),
            (0.67, "¡Solo al completar el nivel 9 termina el juego!", GREEN),
        ]
        for y, txt, col in lines:
            self.text(0.5, y, txt, FONT_SMALL, col)

        tag = self.rect_btn(0.5, 0.84, 380, 80, "▶  EMPEZAR", GREEN, GREEN, "start")
        self.canvas.tag_bind("start", "<Button-1>", lambda e: self.start_level())

    # ──────────────────────────────────────────
    #  INICIO DE NIVEL
    # ──────────────────────────────────────────
    def start_level(self):
        num_count     = self.level + 1
        self.sequence = random.sample(range(21), num_count)
        self.seq_idx  = 0
        self.show_sequence_step()

    def show_sequence_step(self):
        self.clear()
        idx   = self.seq_idx
        n     = self.sequence[idx]
        total = len(self.sequence)

        self.text(0.5, 0.07,
                  f"Nivel {self.level}  —  Número {idx + 1} de {total}",
                  FONT_TINY, GRAY)
        self.text(0.5, 0.50, str(n), FONT_HUGE, YELLOW)

        self._after_seq = self.root.after(1200, self.between_numbers)

    def between_numbers(self):
        self.clear()
        self.seq_idx += 1
        if self.seq_idx < len(self.sequence):
            self._after_seq = self.root.after(350, self.show_sequence_step)
        else:
            self._after_seq = self.root.after(350, self.show_question)

    # ──────────────────────────────────────────
    #  PREGUNTA
    # ──────────────────────────────────────────
    def show_question(self):
        self.clear()
        seq = self.sequence
        n   = len(seq)

        # Posiciones válidas: 0-based, excluye el último (n-1)
        # → nunca se pregunta el último número ni la secuencia entera
        valid_positions = list(range(0, n - 1))
        pos_idx   = random.choice(valid_positions)
        pos_human = pos_idx + 1

        self.asked_idx  = pos_idx
        correct_answer  = seq[pos_idx]

        ordinals = {1:"primero",2:"segundo",3:"tercero",4:"cuarto",5:"quinto",
                    6:"sexto",7:"séptimo",8:"octavo",9:"noveno",10:"décimo"}
        ord_txt = ordinals.get(pos_human, f"número {pos_human}")

        self.text(0.5, 0.08, f"Nivel {self.level}", FONT_TINY, GRAY)
        self.text(0.5, 0.20, "¿Qué número apareció en", FONT_MED, FG)
        self.text(0.5, 0.30, f"{ord_txt.upper()} lugar?", FONT_MED, YELLOW)

        distractors = set()
        while len(distractors) < 3:
            d = random.randint(0, 20)
            if d != correct_answer:
                distractors.add(d)
        options = [correct_answer] + list(distractors)
        random.shuffle(options)
        self.correct_option = correct_answer
        self.options        = options

        self._draw_option_buttons(options)
        self._show_input(on_submit=self._check_secret_from_question)

    def _draw_option_buttons(self, options, result_idx=None, success=None):
        bw, bh = 200, 100
        gap    = 30
        total  = 4 * bw + 3 * gap
        sx     = (self.W - total) // 2
        by     = int(self.H * 0.50)

        for i, opt in enumerate(options):
            tag = f"opt_{i}"
            bx  = sx + i * (bw + gap)
            cx  = bx + bw // 2
            cy  = by + bh // 2

            if result_idx is not None and i == result_idx:
                border = GREEN if success else RED
                fill   = "#003300" if success else "#330000"
            else:
                border = CYAN
                fill   = DARK_BOX

            self.canvas.create_rectangle(bx, by, bx + bw, by + bh,
                                         fill=fill, outline=border,
                                         width=3, tags=tag)
            self.canvas.create_text(cx, cy, text=str(opt),
                                    font=FONT_MED, fill=FG, tags=tag)
            self.canvas.create_text(cx, by + bh + 24,
                                    text=f"[{i + 1}]",
                                    font=FONT_TINY, fill=GRAY)
            if result_idx is None:
                self.canvas.tag_bind(tag, "<Button-1>",
                                     lambda e, idx=i: self._choose_option(idx))

        self.root.bind("1", lambda e: self._choose_option(0))
        self.root.bind("2", lambda e: self._choose_option(1))
        self.root.bind("3", lambda e: self._choose_option(2))
        self.root.bind("4", lambda e: self._choose_option(3))

    def _choose_option(self, idx):
        for k in ("1","2","3","4"):
            self.root.unbind(k)
        chosen  = self.options[idx]
        success = (chosen == self.correct_option)
        self._show_feedback(idx, success)

    def _show_feedback(self, chosen_idx, success):
        self.canvas.delete("all")
        pos_human = self.asked_idx + 1
        ordinals  = {1:"primero",2:"segundo",3:"tercero",4:"cuarto",5:"quinto",
                     6:"sexto",7:"séptimo",8:"octavo",9:"noveno",10:"décimo"}
        ord_txt   = ordinals.get(pos_human, f"número {pos_human}")

        self.text(0.5, 0.08, f"Nivel {self.level}", FONT_TINY, GRAY)
        self.text(0.5, 0.20, "¿Qué número apareció en", FONT_MED, FG)
        self.text(0.5, 0.30, f"{ord_txt.upper()} lugar?", FONT_MED, YELLOW)
        self._draw_option_buttons(self.options, result_idx=chosen_idx, success=success)

        msg = "¡CORRECTO! ✔" if success else f"INCORRECTO  (era el  {self.correct_option})"
        col = GREEN if success else RED
        self.text(0.5, 0.82, msg, FONT_MED, col)

        self.root.after(1900, lambda: self._after_answer(success))

    def _after_answer(self, success):
        if success:
            self.level += 1
            if self.level > MAX_LEVEL:
                self.show_victory()
            else:
                self.show_transition(success=True)
        else:
            self.level = 1
            self.show_transition(success=False)

    # ──────────────────────────────────────────
    #  INPUT DE TEXTO (código secreto)
    # ──────────────────────────────────────────
    def _show_input(self, on_submit):
        self.entry_var.set("")
        self.entry.place(x=self.W // 2 - 200, y=int(self.H * 0.92),
                         width=400, height=60)
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: on_submit())

    def _check_secret_from_question(self):
        val = self.entry_var.get().strip()
        if val == SECRET_CODE:
            self._allow_unfocus = True
            self.entry.place_forget()
            self.root.unbind("<Return>")
            for k in ("1","2","3","4"):
                self.root.unbind(k)
            self.show_goodbye()
        else:
            # Si no es el código correcto, limpiar silenciosamente
            self.entry_var.set("")
            self.entry.focus_set()

    # ──────────────────────────────────────────
    #  TRANSICIÓN ENTRE NIVELES
    # ──────────────────────────────────────────
    def show_transition(self, success):
        self.clear()
        if success:
            self.text(0.5, 0.36, f"Nivel {self.level - 1} superado  ✔",
                      FONT_MED, GREEN)
            self.text(0.5, 0.50, f"Pasas al nivel {self.level}",
                      FONT_SMALL, FG)
        else:
            self.text(0.5, 0.36, "¡Fallaste!", FONT_MED, RED)
            self.text(0.5, 0.50, "Vuelves al nivel 1", FONT_SMALL, FG)

        tag = self.rect_btn(0.5, 0.72, 360, 80, "CONTINUAR  ▶", GREEN, GREEN, "cont")
        self.canvas.tag_bind("cont", "<Button-1>", lambda e: self.start_level())

    # ──────────────────────────────────────────
    #  VICTORIA
    # ──────────────────────────────────────────
    def show_victory(self):
        self.clear()
        self._allow_unfocus = True
        self.root.attributes("-topmost", False)
        self.text(0.5, 0.28, "🏆  ¡¡FELICIDADES!!  🏆", FONT_MED, YELLOW)
        self.text(0.5, 0.44, "Has completado todos los niveles.", FONT_SMALL, FG)
        self.text(0.5, 0.55, "Eres un maestro de la memoria.",    FONT_SMALL, CYAN)

        tag = self.rect_btn(0.5, 0.74, 320, 80, "SALIR  ✕", RED, RED, "exit")
        self.canvas.tag_bind("exit", "<Button-1>", lambda e: self.root.destroy())

    # ──────────────────────────────────────────
    #  SALIDA CON CÓDIGO SECRETO
    # ──────────────────────────────────────────
    def show_goodbye(self):
        self.clear()
        self.root.attributes("-topmost", False)
        self.text(0.5, 0.40, "Saliendo del juego...", FONT_MED, GRAY)
        self.root.after(1200, self.root.destroy)


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = MemoryGame(root)
    root.mainloop()
