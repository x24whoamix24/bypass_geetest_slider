from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.remote.command import Command


class ActionChains_Fake(ActionChains):
    def __init__(self, driver):
        super().__init__(driver)

    def move_by_offset(self, xoffset, yoffset):
        """
        Moving the mouse to an offset from current mouse position.

        :Args:
         - xoffset: X offset to move to, as a positive or negative integer.
         - yoffset: Y offset to move to, as a positive or negative integer.
        """
        if self._driver.w3c:
            self.w3c_actions.pointer_action.source.create_pointer_move(origin=interaction.POINTER,
                                                                       duration=1,
                                                                       x=int(xoffset),
                                                                       y=int(yoffset))
        else:
            self._actions.append(lambda: self._driver.execute(
                Command.MOVE_TO, {
                    'xoffset': int(xoffset),
                    'yoffset': int(yoffset)}))
        return self
