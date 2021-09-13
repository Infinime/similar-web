import logging
import traceback
import sys
import random
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import selenium.common
import time

class StepError(Exception):
    """Recoverable error: the bot should retry the step"""
    pass


class TaskError(Exception):
    """Recoverable error: the bot should retry the task"""
    pass


class TaskFatalError(Exception):
    """Non-Recoverable error: bot should abandon the task"""
    pass


class SetupError(Exception):
    """This is an error in your code, you need to fix it"""
    pass


class base_task():
    """This class defines very low level abstract task handling. We don't deal with selenium yet,
    just completed or failed steps that add up to a task"""

    max_attempts_task = 5
    max_attempts_step = 3
    task_steps = None

    def on_task_start(self):
        """This can be defined in your class. It executes before task starts. Setup browser here"""
        pass

    def on_task_finished(self):
        """This can be defined in your class. Executes when task finishes without errors"""
        pass

    def on_task_error(self, func_name, exc):
        """This can be defined in your class. Executes when we have a Task or Step error"""
        pass

    def on_task_failed(self, exc):
        """This can be defined in your class. Executes when task fails"""
        pass

    def on_task_cleanup(self):
        """This can be defined in your class. Executes when everything is done (always). Cleanup browser here"""
        pass

    def print_exception(self, val):
        exc_type, exc_value, exc_tb = val
        temp = traceback.format_exception(exc_type, exc_value, exc_tb)
        temp = ''.join(temp)
        logging.info(f"Exception for task {self.__class__.__name__} :\n{temp}")

    def execute_task(self):
        current_name = None
        for task_attempt in range(self.max_attempts_task + 1):
            if task_attempt == self.max_attempts_task:
                logging.info(
                    f"Number of step attempts for {self.__class__.__name__} on_task_start exceeded")
                self.on_task_failed(TaskFatalError('Too many attempts'))
                return False

            try:
                logging.info(
                    f"Starting execute_task on {self.__class__.__name__} attempt {task_attempt} / {self.max_attempts_task}")

                if type(self.task_steps) != list:
                    raise SetupError(
                        f"task_steps need to be defined by your class")

                for step_attempt in range(self.max_attempts_step + 1):
                    if step_attempt == self.max_attempts_step:
                        raise TaskError(
                            f"Number of step attempts for {self.__class__.__name__} on_task_start exceeded")
                    try:
                        self.on_task_start()
                        break
                    except StepError:
                        self.print_exception(sys.exc_info())
                        pass

                for step in self.task_steps:
                    if type(step) != tuple:
                        raise SetupError(
                            f"Incorrect task steps, need tuple, got {type(step).__name__}")
                    if len(step) != 2:
                        raise SetupError(
                            f"Incorrect task steps, need len 2, got {len(step)}")
                    step_chk, step_exe = step

                    for step_attempt in range(self.max_attempts_step + 1):
                        if step_attempt == self.max_attempts_step:
                            raise TaskError(
                                f"Number of step attempts for {self.__class__.__name__} check {step_chk.__name__} exec {step_exe.__name__} exceeded")
                        try:
                            logging.info(f"Starting step for {self.__class__.__name__} check {step_chk.__name__} exec {step_exe.__name__} " +
                                         f"attempt {step_attempt} / {self.max_attempts_step}")

                            current_name = step_chk.__name__
                            crv = step_chk()
                            current_name = None

                            if type(crv) != bool:
                                raise SetupError(
                                    f"Incorrect check step {step_chk.__name__} return value, got {type(crv).__name__}, need bool")
                            logging.info(
                                f"{step_chk.__name__} / {self.__class__.__name__} returned {crv}")

                            if not crv:
                                logging.info(
                                    f"{step_exe.__name__} / {self.__class__.__name__} executing")
                                current_name = step_exe.__name__
                                step_exe()
                                current_name = None
                                logging.info(
                                    f"{step_exe.__name__} / {self.__class__.__name__} finished")

                            current_name = step_chk.__name__
                            crv = step_chk()
                            current_name = None

                            if type(crv) != bool:
                                raise SetupError(
                                    f"Incorrect check step {step_chk.__name__} return value, got {type(crv).__name__}, need bool")
                            logging.info(
                                f"{step_chk.__name__} / {self.__class__.__name__} returned {crv}")

                            if crv:
                                break
                        except StepError as e:
                            self.print_exception(sys.exc_info())
                            self.on_task_error(current_name, e)
                            pass

                self.on_task_finished()
                self.on_task_cleanup()
                logging.info(
                    f"Completed execute_task on {self.__class__.__name__} on attempt {task_attempt} / {self.max_attempts_task}")
                return True
            except KeyboardInterrupt as e:
                self.on_task_failed(e)
                self.on_task_cleanup()
                raise
            except SetupError as e:
                self.print_exception(sys.exc_info())
                self.on_task_failed(e)
                self.on_task_cleanup()
                raise
            except TaskError as e:
                self.print_exception(sys.exc_info())
                self.on_task_error(current_name, e)
                self.on_task_cleanup()
                pass
            except TaskFatalError as e:
                self.print_exception(sys.exc_info())
                self.on_task_failed(e)
                self.on_task_cleanup()
                return False
            except:
                self.print_exception(sys.exc_info())
                self.on_task_error(current_name, sys.exc_info())
                self.on_task_cleanup()
                pass


if __name__ == "__main__":
    step_login = False
    step_posted = False

    class base_task_test(base_task):
        def __init__(self):
            self.task_steps = [
                (self.check_login, self.execute_login), (self.check_post, self.execute_post)]

        def on_task_start(self):
            logging.info("on_task_start")
            self.driver = webdriver.Firefox()
            self.driver.get("https://apply.redsell.xyz")
            self.passwords = {"stage_1": "", "stage_2": "", "stage_3": ""}
            self.find_pass()

        def find_pass(self):
            logging.info("Finding pass")
            '''The Actual code that does work, the code that searches
            and updates the pass'''
            paragraphs = self.driver.find_elements_by_tag_name("p")
            for para in paragraphs:
                if "password" in para.text.lower():
                    if "stage 1" in para.text.lower():
                        self.passwords['stage_1'] = para.text.split(" is ")[1]
                    if "stage 2" in para.text.lower():
                        self.passwords['stage_2'] = para.text.split(" is ")[1]
                    if "stage 3" in para.text.lower():
                        self.passwords['stage_3'] = para.text.split(" is ")[1]

            try:
                h1 = self.driver.find_element_by_tag_name("h1")
                if "Test complete!" in h1.text:
                    self.on_task_finished()
            except selenium.common.exceptions.NoSuchElementException:
                pass
            self.input_passes()

        def next_step(self):
            logging.info("next step, let's go")
            time.sleep(2.7)
            self.find_pass()

        def input_passes(self):
            input_fields = self.driver.find_elements_by_tag_name("input")
            for field in input_fields:
                for password in self.passwords:
                    try:
                        #time.sleep(3)
                        if self.driver.find_element_by_id(password) and self.driver.find_element_by_id(password) == field:
                            field.send_keys(self.passwords[password])
                    except:
                        logging.info("didn't ask for pass")
                        continue
                if field.get_property("type") == "submit" and field.get_property("value").lower() == "proceed":
                    field.send_keys(Keys.RETURN)
                    self.next_step()
                    break

        def on_task_finished(self):
            logging.info("on_task_finished")
            self.on_task_cleanup()

        def on_task_error(self, func_name, exc):
            logging.info(f"on_task_error in {func_name}")

        def on_task_failed(self, exc):
            logging.info("on_task_failed")

        def on_task_cleanup(self):
            logging.info("on_task_cleanup")

        def check_login(self):
            logging.info("check_login")
            if step_login:
                return True
            else:
                return False

        def execute_login(self):
            logging.info("execute_login")
            global step_login
            if random.randrange(4) == 0:
                raise TaskError('Expected random failure, please try again')

            if random.randrange(2) == 0:
                step_login = True
            else:
                logging.info("execute_login failed")

        def check_post(self):
            logging.info("check_post")
            if step_posted:
                return True
            else:
                return False

        def execute_post(self):
            logging.info("execute_post")
            global step_posted
            global step_login
            if not step_login:
                raise SetupError(
                    "Something went very wrong. We aren't logged in")

            if random.randrange(4) == 0:
                raise Exception('Unexpected random failure, please try again')

            if random.randrange(4) == 0:
                raise TaskFatalError(
                    'Ooops, something happened that means that completing the task is impossible (eg. thread locked)')

            if random.randrange(4) == 0:
                step_posted = True
            else:
                logging.info("execute_post failed")

    logging.basicConfig(level=logging.DEBUG)
    test = base_task_test()
    test.execute_task()
