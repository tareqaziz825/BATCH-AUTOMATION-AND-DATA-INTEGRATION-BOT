# ─────────────────────────────────────────────────────────────
#  main.py  –  Entry point
#  Run: python main.py
# ─────────────────────────────────────────────────────────────

import sys
from gui.app import BatchBotApp


def main():
    app = BatchBotApp()
    app.mainloop()


if __name__ == "__main__":
    main()
