import curses
import sqlite3
import os

# HydroToDo Beta
# Caracteres para borda arredondada
TL = '╭'
TR = '╮'
BL = '╰'
BR = '╯'
H  = '─'
V  = '│'

DB_PATH = os.path.join(os.path.dirname(__file__), '.todos.db')

ASCII_TITLE = [
    "██╗  ██╗██╗   ██╗██████╗ ██████╗  ██████╗ ████████╗ ██████╗ ██████╗  ██████╗ ",
    "██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔══██╗██╔═══██╗",
    "███████║ ╚████╔╝ ██║  ██║██████╔╝██║   ██║   ██║   ██║   ██║██║  ██║██║   ██║",
    "██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██║   ██║   ██║   ██║   ██║██║  ██║██║   ██║",
    "██║  ██║   ██║   ██████╔╝██║  ██║╚██████╔╝   ██║   ╚██████╔╝██████╔╝╚██████╔╝",
    "╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═════╝  ╚═════╝ ",
    "                                                                              "
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL DEFAULT 'Geral'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_categories (
                    name TEXT PRIMARY KEY
                )''')
    c.execute("PRAGMA table_info(todos)")
    columns = [row[1] for row in c.fetchall()]
    if 'category' not in columns:
        c.execute("ALTER TABLE todos ADD COLUMN category TEXT NOT NULL DEFAULT 'Geral'")
    conn.commit()
    conn.close()


def load_todos(category='Geral'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, text, done FROM todos WHERE category = ?', (category,))
    todos = [{'id': row[0], 'text': row[1], 'done': bool(row[2])} for row in c.fetchall()]
    conn.close()
    return todos


def add_todo(text, category='Geral'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO todos (text, done, category) VALUES (?, 0, ?)', (text, category))
    conn.commit()
    conn.close()


def update_todo_done(todo_id, done):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE todos SET done = ? WHERE id = ?', (int(done), todo_id))
    conn.commit()
    conn.close()


def delete_todo(todo_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()


def add_deleted_category(cat):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO deleted_categories (name) VALUES (?)', (cat,))
    conn.commit()
    conn.close()


def remove_deleted_category(cat):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM deleted_categories WHERE name = ?', (cat,))
    conn.commit()
    conn.close()


def delete_todos_by_category(category):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM todos WHERE category = ?', (category,))
    conn.commit()
    conn.close()


def draw_rounded_box(win, y, x, h, w):
    win.addstr(y, x, TL + H * (w - 2) + TR)
    for i in range(1, h - 1):
        win.addstr(y + i, x, V)
        win.addstr(y + i, x + w - 1, V)
    win.addstr(y + h - 1, x, BL + H * (w - 2) + BR)


def get_all_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT category FROM todos')
    cats = [row[0] for row in c.fetchall()]
    c.execute('SELECT name FROM deleted_categories')
    deleted = set(row[0] for row in c.fetchall())
    conn.close()
    filtered = [cat for cat in cats if cat not in deleted]
    return filtered if filtered else ['Geral']


def main(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    init_db()
    # Estrutura para abas
    tab_categories = get_all_categories()
    tabs = [load_todos(cat) for cat in tab_categories]
    current_tab = 0
    max_tabs = 10
    current_indices = [0 for _ in tab_categories]

    show_help = False
    help_lines = [
        "Comandos disponíveis:",
        "",
        "↑↓         Navegar entre tarefas",
        "Enter      Marcar/desmarcar tarefa",
        "a          Adicionar nova tarefa",
        "d          Deletar tarefa selecionada",
        "Ctrl+T     Nova aba",
        "Ctrl+W     Fechar aba",
        "←/→        Trocar aba",
        "h          Mostrar/ocultar ajuda",
        "q          Sair do programa",
    ]

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Verificação de resolução mínima
        min_width = 80
        min_height = 30
        if width < min_width or height < min_height:
            msg = f"Resolução atual: {width}x{height} | Mínima: {min_width}x{min_height}"
            stdscr.clear()
            stdscr.addstr(height // 2, max(0, (width - len(msg)) // 2), msg, curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord('q'), 3):  # 'q', Ctrl+C
                break
            continue

        # Caixa do título
        title_box_w = max(len(line) for line in ASCII_TITLE) + 4
        title_box_h = len(ASCII_TITLE) + 2
        title_box_x = (width - title_box_w) // 2
        title_box_y = 1
        draw_rounded_box(stdscr, title_box_y, title_box_x, title_box_h, title_box_w)
        for i, line in enumerate(ASCII_TITLE):
            stdscr.addstr(title_box_y + 1 + i, title_box_x + 2, line, curses.color_pair(3) | curses.A_BOLD)

        if show_help:
            # Tela de ajuda centralizada, mas um pouco mais para baixo
            help_w = max(len(line) for line in help_lines) + 4
            help_h = len(help_lines) + 2
            help_x = (width - help_w) // 2
            help_y = max(2, (height - help_h) // 2 + height // 10)  # desloca para baixo
            draw_rounded_box(stdscr, help_y, help_x, help_h, help_w)
            for i, line in enumerate(help_lines):
                stdscr.addstr(help_y + 1 + i, help_x + 2, line, curses.color_pair(2) | curses.A_BOLD)
        else:
            # Abas no topo (melhor destaque)
            tab_strs = []
            for i, cat in enumerate(tab_categories):
                if i == current_tab:
                    tab_strs.append(f"╭─[{cat}]─╮")
                else:
                    tab_strs.append(f"  {cat}  ")
            tab_bar = " ".join(tab_strs)
            stdscr.addstr(title_box_y + title_box_h, max(0, (width - len(tab_bar)) // 2), tab_bar, curses.color_pair(2) | curses.A_BOLD)

            # Caixa principal da aba
            box_w = min(50, width - 4)
            box_h = min(max(10, len(tabs[current_tab]) + 5), height - title_box_h - 7)
            box_x = (width - box_w) // 2
            box_y = title_box_y + title_box_h + 2
            draw_rounded_box(stdscr, box_y, box_x, box_h, box_w)
            todos = tabs[current_tab]
            # Garante que o índice selecionado está dentro do tamanho da lista
            if current_indices[current_tab] >= len(todos):
                current_indices[current_tab] = max(0, len(todos) - 1)
            current_index = current_indices[current_tab]
            # SCROLL
            max_visible = box_h - 4
            if len(todos) > max_visible:
                if current_index < max_visible // 2:
                    start = 0
                elif current_index > len(todos) - (max_visible // 2):
                    start = len(todos) - max_visible
                else:
                    start = current_index - max_visible // 2
                end = start + max_visible
            else:
                start = 0
                end = len(todos)
            if len(todos) == 0:
                msg = "Nenhuma tarefa ainda..."
                msg_y = box_y + (box_h // 2)
                msg_x = box_x + ((box_w - len(msg)) // 2)
                stdscr.addstr(msg_y, msg_x, msg, curses.color_pair(2) | curses.A_BOLD)
            elif len(todos) > 0:
                for idx, i in enumerate(range(start, end)):
                    if 0 <= i < len(todos):
                        todo = todos[i]
                        prefix = "[X] " if todo['done'] else "[ ] "
                        line = prefix + todo['text']
                        attr = curses.color_pair(1) | curses.A_BOLD if i == current_index else 0
                        stdscr.addstr(box_y + 2 + idx, box_x + 2, line[:box_w-4], attr)
            # Indicadores de scroll
            if start > 0:
                stdscr.addstr(box_y + 1, box_x + box_w - 3, '↑', curses.color_pair(2) | curses.A_BOLD)
            if end < len(todos):
                stdscr.addstr(box_y + box_h - 2, box_x + box_w - 3, '↓', curses.color_pair(2) | curses.A_BOLD)

        # Comando de ajuda minimalista
        help_hint = "Pressione 'h' para ajuda"
        stdscr.addstr(height - 2, max(0, (width - len(help_hint)) // 2), help_hint, curses.color_pair(4) | curses.A_BOLD)

        stdscr.refresh()
        key = stdscr.getch()

        # Atalhos de abas
        if key == 20:  # Ctrl+T
            if len(tabs) < max_tabs:
                curses.echo()
                prompt = "Nome da nova categoria: "
                stdscr.addstr(height - 4, 2, " " * (width - 4))
                stdscr.addstr(height - 4, 2, prompt, curses.A_BOLD)
                stdscr.refresh()
                cat = stdscr.getstr(height - 4, 2 + len(prompt), 20).decode().strip()
                curses.noecho()
                if cat and cat not in tab_categories:
                    remove_deleted_category(cat)
                    tab_categories.append(cat)
                    tabs.append(load_todos(cat))
                    current_indices.append(0)
                    current_tab = len(tabs) - 1
        elif key == 23:  # Ctrl+W
            if len(tabs) > 1:
                add_deleted_category(tab_categories[current_tab])
                delete_todos_by_category(tab_categories[current_tab])
                tab_categories.pop(current_tab)
                tabs.pop(current_tab)
                current_indices.pop(current_tab)
                if current_tab >= len(tabs):
                    current_tab = len(tabs) - 1
        elif key == 545:  # Ctrl+Left
            if current_tab > 0:
                current_tab -= 1
        elif key == 560:  # Ctrl+Right
            if current_tab < len(tabs) - 1:
                current_tab += 1
        elif key == curses.KEY_LEFT:
            if current_tab > 0:
                current_tab -= 1
        elif key == curses.KEY_RIGHT:
            if current_tab < len(tabs) - 1:
                current_tab += 1
        elif key == ord('h'):
            show_help = not show_help
        elif key == ord('q'):
            break
        elif key == curses.KEY_UP:
            if current_indices[current_tab] > 0:
                current_indices[current_tab] -= 1
        elif key == curses.KEY_DOWN:
            if current_indices[current_tab] < len(tabs[current_tab]) - 1:
                current_indices[current_tab] += 1
        elif key == ord('\n') and tabs[current_tab]:
            todos = tabs[current_tab]
            idx = current_indices[current_tab]
            if 0 <= idx < len(todos):
                todos[idx]['done'] = not todos[idx]['done']
                update_todo_done(todos[idx]['id'], todos[idx]['done'])
                # Atualiza a lista da aba
                tabs[current_tab] = load_todos(tab_categories[current_tab])
        elif key == ord('a'):
            curses.echo()
            prompt = "Nova tarefa: "
            box_y = title_box_y + title_box_h + 2
            box_x = (width - min(50, width - 4)) // 2
            box_w = min(50, width - 4)
            box_h = min(max(10, len(tabs[current_tab]) + 5), height - title_box_h - 7)
            stdscr.addstr(box_y + box_h - 2, box_x + 2, " " * (box_w - 4))
            stdscr.addstr(box_y + box_h - 2, box_x + 2, prompt, curses.A_BOLD)
            stdscr.refresh()
            text = stdscr.getstr(box_y + box_h - 2, box_x + 2 + len(prompt), box_w - 4 - len(prompt)).decode()
            if text.strip():
                add_todo(text, tab_categories[current_tab])
                tabs[current_tab] = load_todos(tab_categories[current_tab])
                current_indices[current_tab] = len(tabs[current_tab]) - 1
            curses.noecho()
        elif key == ord('d') and tabs[current_tab]:
            todos = tabs[current_tab]
            idx = current_indices[current_tab]
            if 0 <= idx < len(todos):
                delete_todo(todos[idx]['id'])
                tabs[current_tab] = load_todos(tab_categories[current_tab])
                # Ajusta o índice para não ultrapassar o tamanho da lista
                if current_indices[current_tab] >= len(tabs[current_tab]):
                    current_indices[current_tab] = max(0, len(tabs[current_tab]) - 1)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass  # Sai silenciosamente ao pressionar Ctrl+C
