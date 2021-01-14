from dearpygui.core import *
from dearpygui.simple import *
from loguru import logger
from app_backend import App_backend
import platform
import os
import traceback

class App:
    def __init__(self) -> None:
        self.cwd = os.getcwd()
        logger.info(f"CWD: {self.cwd}")
        self.app_name = "Bingo"
        self.init = False
        self.app_backend = None

    def check_init(self) -> None:
        if not self.init:
            if platform.system() == "Windows":
                self.app_backend = App_backend(os.getenv("APPDATA"), "bingo.db")
            else:
                self.app_backend = App_backend(os.getcwd(), "bingo.db")
            self.init = True

    def verify_game(self, sender, data) -> None:
        try:
            self.close_window(sender)
            delete_item("Error")
        except:
            pass
        if not self.init:
            delete_item("Load Game")
            self.load_game()
            self.error_window("Please create or choose a game.")

    def close_window(self, sender, data) -> None:
        delete_item(sender)

    def update_game_id_text(self, game_id: int) -> None:
        set_value("game_id_display", f"Game ID: {game_id}")

    def create_game(self, sender, data) -> None:
        self.app_backend.create_game()
        logger.info(f"Created Game ID: {self.app_backend.game_id}")
        delete_item("Create New Game")
        self.update_game_id_text(self.app_backend.game_id)
        self.get_combinations()

    def create_game_window(self, sender, data) -> None:
        try:
            self.close_window("Create New Game", None)
            self.close_window("Load Game", None)
            self.reset_combination()
            self.check_init()
        except Exception:
            pass
        with window("Create New Game", on_close=self.verify_game, autosize=True):
            add_button("Confirm", callback=self.create_game)

    def get_combinations(self) -> None:
        combination = self.app_backend.get_combination_from_game()
        if not combination:
            logger.info("No combo")
            add_button("Draw", callback=self.create_combination, parent=self.app_name)
        else:
            try:
                delete_item("Draw")
                delete_item("Winning numbers:")
                self.reset_combination(False)
            except Exception:
                pass
            combination = list(reversed(combination.split(",")))
            logger.debug(combination)
            self.write_combination(combination)

    def write_combination(self, combination: list) -> None:
        add_button(
            "Next Number",
            parent=self.app_name,
            callback=self.get_combination_one_by_one,
            callback_data=combination,
        )
        add_button(
            "Show all numbers",
            parent=self.app_name,
            callback=self.get_combination_all,
            callback_data=combination,
        )
        add_text("Winning numbers:", parent=self.app_name)
        add_spacing(name="block", parent=self.app_name)

    def get_combination_all(self, sender, combination) -> list:
        write_text = []
        self.reset_combination(False)
        logger.debug(combination)
        for index in range(0, len(combination), 5):
            write_text.append(" ".join(combination[index : index + 5]))
        for text in write_text:
            logger.debug(f"text: {text}")
            add_text(text, parent=self.app_name)
        self.reset_combination_properties()

    def get_combination_one_by_one(self, sender, combination) -> list:
        write_text = []
        try:
            i = 1
            for index in range(0, len(combination), 5):
                for j in range(1, 6):
                    write_text.append(
                        {
                            "source": f"draw_{i}",
                            "text": " ".join(combination[index : index + j]),
                        }
                    )
                i += 1
        except Exception:
            logger.error(traceback.format_exc())
        try:
            last_source = get_data("last_source")
            index = get_data("num_index")
            if index == None:
                delete_data("num_index")
                add_data("num_index", 0)
                index = 0
            if get_data("source") == None:
                delete_data("source")
                add_data("source", write_text[0]["source"])
            current_source = get_data("source")
            if current_source != last_source:
                add_text(
                    write_text[index]["text"],
                    parent=self.app_name,
                    source=current_source,
                    before="block",
                )
            else:
                set_value(current_source, write_text[index]["text"])
            delete_data("num_index")
            add_data("num_index", index + 1)
            delete_data("last_source")
            add_data("last_source", current_source)
            delete_data("source")
            add_data("source", write_text[index + 1]["source"])
        except IndexError:
            self.reset_combination_properties()
        return

    def reset_data(self) -> None:
        add_data("num_index", None)
        add_data("last_source", None)
        add_data("source", None)

    def reset_combination_properties(self):
        delete_item("Next Number")
        delete_item("Show all numbers")
        delete_item("block")

    def reset_combination(self, reset_text=True) -> None:
        try:
            combination = self.app_backend.get_combination_from_game()
            combination = list(reversed(combination.split(",")))
            for index in range(0, len(combination), 5):
                for j in range(1, 6):
                    text = " ".join(combination[index : index + j])
                    delete_item(text)
            if reset_text:
                self.update_game_id_text("N/A")
            self.reset_combination_properties()
            self.reset_data()
        except:
            pass

    def create_combination(self, sender, data) -> None:
        self.app_backend.generate_winning_combination(self.app_backend.game_id)
        self.get_combinations()

    def open_game(self, sender, data) -> None:
        selected_cell = get_table_selections("Games")
        logger.debug(selected_cell)
        self.app_backend.game_id = selected_cell[0][0] + 1
        logger.debug(self.app_backend.game_id)
        delete_item("Open Game")
        self.update_game_id_text(self.app_backend.game_id)
        self.get_combinations()

    def open_games_table(self) -> None:
        games = self.app_backend.get_all_games()
        table_name = "Games"
        add_table(table_name, ["Game ID", "Created On"], callback=self.open_game)
        for game in games:
            add_row(table_name, [f"{game['game_id']}", f"{game['created_datetime']}"])

    def open_game_window(self, sender, data) -> None:
        try:
            self.close_window("Open Game", None)
            self.close_window("Load Game", None)
            self.check_init()
            self.reset_combination(True)
        except Exception:
            pass
        with window("Open Game", on_close=self.verify_game, width=1000, height=400):
            self.open_games_table()
            add_button("Cancel", callback=self.close_open_game)

    def close_open_game(self, sender, data) -> None:
        delete_item("Open Game")

    def check_numbers(self, numbers: list) -> tuple:
        valid = False
        index = 0
        error = ""
        try:
            for index, number in enumerate(numbers):
                valid_input = 1 <= int(number) <= 48
                if valid_input:
                    valid = True
                else:
                    valid = False
                    error = f"Number is not between 1 and 48. (Number: {index+1})"
                    break
            if len(set(numbers)) != 6:
                valid = False
                error = f"Duplicate numbers. Check input."
        except Exception:
            valid = False
            error = f"Did not enter a number (Number: {index+1})"
        finally:
            return valid, error, numbers

    def check_text(self, text: str) -> tuple:
        if text and not text.isspace():
            text = text.rstrip()
            text = text.lstrip()
            return True, text
        return False, text

    def check_number(self, number: str) -> tuple:
        valid = False
        try:
            number = int(number)
            valid = True
        except:
            pass
        finally:
            return valid, number

    def create_ticket(self, sender, data) -> None:
        self.check_init()
        success = False
        ticket_id = 0
        name = get_value("ticket_name")
        valid_name, name = self.check_text(name)
        bet_amount = get_value("bet_amount")
        valid_amount, bet_amount = self.check_number(bet_amount)
        numbers = [get_value(f"ticket_num_{num}") for num in range(1, 7)]
        valid_numbers, error, numbers = self.check_numbers(numbers)
        if valid_name and valid_numbers and valid_amount:
            numbers = [int(x) for x in numbers]
            entry = {"name": name, "amount": bet_amount, "numbers": numbers}
            game_id = self.app_backend.game_id
            if game_id == 0:
                self.error_window("Please create or choose a game.")
            else:
                ticket_id = self.app_backend.create_ticket(entry)
                success = True
        else:
            if not valid_name:
                error = "Name and/or bet amount is not valid."
            elif not valid_amount:
                error = "Bet amount is not valid."
            self.error_window(error)
        if success:
            delete_item("Create New Ticket")
            with window(
                "Confirm new ticket",
                on_close=self.close_window,
                autosize=True,
            ):
                add_text("Ticket created with the following information: ")
                add_text(f"Name: {name}")
                add_text(f"Bet Amount: {bet_amount}")
                add_text(f"Numbers: {', '.join([str(x) for x in numbers])}")
                add_button(
                    "View Ticket", callback=self.open_ticket, callback_data=ticket_id
                )
                add_button("Close Window", callback=self.close_create_ticket_window)

    def close_create_ticket_window(self, sender, data) -> None:
        delete_item("Confirm new ticket")

    def error_window(self, error: str) -> None:
        with window("Error", on_close=self.close_window):
            add_text(error)
            add_button("OK", callback=self.close_error)

    def close_error(self, sender, data) -> None:
        delete_item("Error")

    def create_ticket_window(self, sender, data) -> None:
        try:
            self.close_window("Create New Ticket", None)
            self.close_window("Load Game", None)
        except Exception:
            pass
        if not self.init:
            self.verify_game(None, None)
        else:
            with window("Create New Ticket", autosize=True, on_close=self.close_window):
                add_input_text("Name", source="ticket_name")
                add_input_text("Amount", source="bet_amount")
                add_input_text("Number 1", source="ticket_num_1")
                add_input_text("Number 2", source="ticket_num_2")
                add_input_text("Number 3", source="ticket_num_3")
                add_input_text("Number 4", source="ticket_num_4")
                add_input_text("Number 5", source="ticket_num_5")
                add_input_text("Number 6", source="ticket_num_6")
                add_button("Create Ticket", callback=self.create_ticket)

    def open_ticket(self, sender, data) -> None:
        if isinstance(data, list):
            path = f"{data[0]}/{data[1]}"
        else:
            if platform.system() == "Windows":
                path = f"{os.getenv('APPDATA')}/tickets/game_{self.app_backend.game_id}/ticket_{data}.pdf"
            else:
                path = f"{os.getcwd()}/tickets/game_{self.app_backend.game_id}/ticket_{data}.pdf"
        self.app_backend.open_ticket(path)

    def open_ticket_window(self, sender, data) -> None:
        open_file_dialog(callback=self.open_ticket)

    def load_game(self) -> None:
        with window("Load Game", autosize=True, on_close=self.verify_game):
            add_button("Create new game", callback=self.create_game_window)
            add_button("Load game", callback=self.open_game_window)
    
    def reset_callback(self, sender, data) -> None:
        self.check_init()
        self.app_backend.reset_app()
        delete_item("Reset#")
        with window("Reset##", on_close=self.close_app):
            add_text("Reset complete.\nRestart the app to complete reset.")
            add_button("Close App", callback=self.close_app)

    def reset_window(self, sender, data) -> None:
        with window("Reset#", autosize=True):
            add_text("Are you sure you want to reset?\nYou cannot reverse this action.", parent="Reset#")
            add_button("Confirm", callback=self.reset_callback)
    
    def close_app(self, sender, data):
        stop_dearpygui()

    def show(self) -> None:
        with window(self.app_name):
            set_main_window_size(1920, 1080)
            set_main_window_resizable(True)
            set_global_font_scale(1.25)
            with menu_bar("Main Menu Bar"):

                with menu("Game"):
                    add_menu_item("New game", callback=self.create_game_window)
                    add_menu_item("Open game", callback=self.open_game_window)

                with menu("Ticket"):
                    add_menu_item("New ticket", callback=self.create_ticket_window)
                    add_menu_item("Open ticket", callback=self.open_ticket_window)

                with menu("Settings"):
                    add_menu_item("Show style menu", callback=show_style_editor)
                    add_menu_item("Reset", callback=self.reset_window)

            add_text(f"Game ID: N/A", source="game_id_display", parent=self.app_name)
            self.reset_data()

        self.load_game()

        start_dearpygui(primary_window=self.app_name)


if __name__ == "__main__":
    app = App()
    app.show()
