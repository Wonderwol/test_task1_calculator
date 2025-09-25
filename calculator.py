import customtkinter as ctk
import ast
import operator
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

OPERATIONS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv
}

UNARY = {
        ast.UAdd: lambda x: x,
        ast.USub: lambda x: -x
}


def eval_node(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATIONS:
        return OPERATIONS[type(node.op)](eval_node(node.left),
                                         eval_node(node.right))
    raise ValueError("Недопустимое выражение")


def safe_eval(expr):
    tree = ast.parse(expr, mode="eval")
    return eval_node(tree.body)


root = ctk.CTk()
root.title("Калькулятор")
root.geometry("480x640")
root.resizable(False, False)
root.configure(fg_color="#1e1e1e")
root.iconbitmap("icons/calculator.ico")

# Поле ввода
entry = ctk.CTkEntry(root, font=("Arial", 28), fg_color="#2b2b2b",
                     text_color="white", border_color="white",
                     border_width=2, corner_radius=12)
entry.pack(fill="x", padx=20, pady=(20, 10), ipady=12)


def set_entry(value: str):
    entry.delete(0, "end")
    entry.insert(0, value)
    entry.icursor(len(value))


def reset_entry():
    set_entry("0")


def backspace():
    if entry.get() in ("0", "Ошибка"):
        reset_entry()
        return
    if entry.select_present():
        start, end = entry.index("sel.first"), entry.index("sel.last")
        entry.delete(start, end)
        entry.icursor(start)
    else:
        pos = entry.index("insert")
        if pos > 0:
            entry.delete(pos - 1)
            entry.icursor(pos - 1)
    if not entry.get():
        reset_entry()


# История вычислений
history_box = ctk.CTkTextbox(root, height=180, fg_color="#2b2b2b",
                             text_color="white", border_color="white",
                             border_width=2, corner_radius=12, cursor="arrow")
history_box.pack(fill="both", padx=20, pady=(0, 10))
for seq in ["<Key>", "<Button-1>", "<Button-2>", "<Button-3>"]:
    history_box.bind(seq, lambda e: "break")


def format_for_history(expr):
    result = []
    for i, ch in enumerate(expr):
        if ch == "-" and (i == 0 or expr[i - 1] in "(*+-/"):
            result.append(ch)
        elif ch in "+-*/()":
            result.append(f" {ch} ")
        else:
            result.append(ch)
    return ' '.join(''.join(result).split())


def add_history(expr, result):
    history_box.configure(state="normal")
    history_box.insert("0.0", f"{format_for_history(expr)} = {result}\n")
    history_box.configure(state="disabled")


# Основные операции
def add_char(ch):
    current = entry.get()
    pos = entry.index("insert")

    if current == "Ошибка":
        set_entry(ch)
        return

    # Специальная обработка для "0"
    if current == "0":
        if ch == ".":
            set_entry("0.")
        elif ch in "+-*/":
            set_entry("0"+ch)
        else:
            set_entry(ch)
        return

    # Запрещаем два арифметических знака подряд
    if ch in "+-*/" and current[-1] in "+-*/":
        return

    # Запрещаем вторую точку в одном числе
    if ch == ".":
        # Найти последний оператор
        last_op = max(current.rfind(op) for op in "+-*/")
        # Выделяем часть числа после последнего оператора
        if "." in current[last_op+1:]:
            return

    # Вставка символа на место курсора
    if entry.select_present():
        start, end = entry.index("sel.first"), entry.index("sel.last")
        entry.delete(start, end)
        entry.insert(start, ch)
        entry.icursor(start + 1)
    else:
        entry.insert(pos, ch)
        entry.icursor(pos + 1)


def calculate():
    expr = entry.get().replace(" ", "")
    if not expr or expr == "0":
        reset_entry()
        return

    # Если выражение оканчивается на оператор, не вычисляем
    if re.match(r".*[+\-*/]$", expr):
        return

    try:
        res = safe_eval(expr)

        # Округляем результат и форматируем для красивого отображения
        if isinstance(res, float):
            res = round(res, 10)  # оставляем максимум 9 знаков после запятой
            res_str = f"{res:.10g}"  # убираем лишние нули и длинные дроби
        else:
            res_str = str(res)

        set_entry(res_str)

        # Записываем в историю, если выражение не оканчивается на оператор
        if re.search(r"[+\-*/]", expr):
            add_history(expr, res_str)

    except Exception:
        set_entry("Ошибка")


buttons = [
    ["7", "8", "9", "C", "⌫"],
    ["4", "5", "6", "*", "/"],
    ["1", "2", "3", "+", "-"],
    [".", "0", "(", ")", "="]
]

frame = ctk.CTkFrame(root, fg_color="#1e1e1e", corner_radius=15)
frame.pack(padx=20, pady=10, fill="x")
btn_size = 70

default_style = {"fg_color": "#00cc44", "hover_color": "#009933",
                 "font": ("Arial", 20)}
special_styles = {
    "=": {"fg_color": "#00ff66", "hover_color": "#00cc44",
          "font": ("Arial", 22, "bold"), "command": calculate},
    "C": {"fg_color": "#ff4d4d", "hover_color": "#ff3333",
          "command": reset_entry},
    "⌫": {"fg_color": "#ff4d4d", "hover_color": "#ff3333",
          "command": backspace},
}

for r, row in enumerate(buttons):
    for c, char in enumerate(row):
        style = {**default_style, **special_styles.get(char, {})}
        cmd = style.get("command", lambda ch=char: add_char(ch))
        btn = ctk.CTkButton(frame, text=char, command=cmd,
                            fg_color=style["fg_color"],
                            hover_color=style["hover_color"],
                            text_color="white", corner_radius=12,
                            font=style["font"],
                            width=btn_size, height=btn_size)
        btn.grid(row=r, column=c, padx=6, pady=6)
        frame.grid_columnconfigure(c, weight=1)

# Клавиатура
allowed_chars = "0123456789+-*/()."
KEY_ACTIONS = {"Return": calculate, "equal": calculate,
               "Escape": reset_entry, "BackSpace": backspace}


def key_handler(event):
    # Навигация стрелками
    if event.keysym in ("Left", "Right", "Home", "End"):
        return

    # Блокируем пробел
    if event.char == " ":
        return "break"

    # Разрешённые символы калькулятора
    if event.char in allowed_chars:
        add_char(event.char)
        return "break"

    # Действия клавиш (Enter, Escape, BackSpace)
    if event.keysym in KEY_ACTIONS:
        KEY_ACTIONS[event.keysym]()
        return "break"

    return "break"


entry.bind("<Key>", key_handler)
root.bind("<Map>", lambda e: entry.focus_set())
reset_entry()

root.mainloop()
