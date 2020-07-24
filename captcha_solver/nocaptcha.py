import time
import random
import base64
import os

from io import BytesIO
import PIL.Image as image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from captcha_solver.puzzle_solver import PuzzleSolver
from captcha_solver.actions import ActionChains_Fake

CUT_IMAGE_PATH = os.path.join(os.path.abspath("pic"), "cut.png")
PUZZLE_IMAGE_PATH = os.path.join(os.path.abspath("pic"), "puzzle.png")


class CapatchaSolver(object):
    def __init__(self, driver):
        self.driver = driver

    def solve_captcha(self):
        """
        Solve the captcha in the given url
        :param self.driver: The self.driver of the self.driver to use
        """
        # Starts the captcha operations
        self._browser_actions()
        # Solves how much x distance to slide
        solver = PuzzleSolver(PUZZLE_IMAGE_PATH, CUT_IMAGE_PATH)
        x_distance = solver.get_position()
        # Slide to solve the captcha
        self._btn_slide(x_distance)
        time.sleep(2)

    def _browser_actions(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "geetest_radar_tip")))

        self.driver.find_elements_by_class_name("geetest_radar_tip")[1].click() if len(
            self.driver.find_elements_by_class_name(
                "geetest_radar_tip")) > 1 else self.driver.find_element_by_class_name(
            "geetest_radar_tip").click()
        time.sleep(4)
        # Saves the full image of the captcha
        self._cut_gt_window_image()
        # Save the puzzle part of the captcha
        self._cut_puzzle_part()

    def _cut_puzzle_part(self):
        canvas = self.driver.find_element_by_class_name("geetest_canvas_slice")

        canvas_png = self.driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        with open(PUZZLE_IMAGE_PATH, "wb") as f:
            f.write(base64.b64decode(canvas_png))

    # 直接页面截取图片
    def _cut_gt_window_image(self):
        image_div = self.driver.find_element_by_class_name("geetest_window")
        location = image_div.location
        size = image_div.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size[
            'width']
        screen_shot = self.driver.get_screenshot_as_png()
        screen_shot = image.open(BytesIO(screen_shot))
        captcha = screen_shot.crop((left, top, right, bottom))
        captcha.save(CUT_IMAGE_PATH)
        return self.driver

    # 阈值二值化图片定位
    def _get_x_point(self, bin_img_path=''):
        tmp_x_cur = 0
        img = image.open(bin_img_path).load()
        # 缺口出现范围大概在x轴[48-52]-220,y轴15-145
        for y_cur in range(15, 145):
            b_acc = 0
            tmp_x_cur = 0
            for x_cur in range(48, 220):
                if img[x_cur, y_cur] == 0:
                    if b_acc == 0:
                        tmp_x_cur = x_cur
                    b_acc += 1
                else:
                    if b_acc in range(36, 44):
                        return tmp_x_cur - 40 + b_acc
                    else:
                        b_acc = 0
        return tmp_x_cur

    def _get_start_point(self, bin_img_path=''):
        img = image.open(bin_img_path)
        _pixel = 42
        _color_diff_list = {}
        initial_slider_left_x_index_range = range(6, 14)
        for initial_slider_left_x_index in initial_slider_left_x_index_range:
            back_color_n = 0
            slider_left = {}
            for y_cur in range(118):
                color_n = 0
                for add_to_next in range(_pixel):
                    color_n += img.getpixel((initial_slider_left_x_index, y_cur + add_to_next))
                slider_left[color_n] = y_cur
            w_color_n_max = max(slider_left)
            y_start_cur = slider_left[w_color_n_max]
            print(f'索引{initial_slider_left_x_index}左白值总和:{w_color_n_max}')
            for add_to_next in range(_pixel):
                back_color_n += img.getpixel((initial_slider_left_x_index + 1, y_start_cur + add_to_next))
            print(f'索引{initial_slider_left_x_index}右白值总和:{back_color_n}')
            _color_diff_list[w_color_n_max - back_color_n] = initial_slider_left_x_index
        best_point = _color_diff_list[max(_color_diff_list)]
        print(f'最佳起点:{best_point}')
        return best_point

    # 分割线二值化图片定位
    def _get_x_point_in_contour(self, bin_img_path=''):
        img = image.open(bin_img_path)
        # 拼块外部阴影范围
        _shadow_width = 5
        _pixel = 42
        # 滑块左边位置7px[6\13]处（考虑凸在左的情况），获取滑块位置
        slider_left_x_index = self._get_start_point(bin_img_path)
        slider_left = {}
        for y_cur in range(118):
            color_n = 0
            for add_to_next in range(_pixel):
                color_n += img.getpixel((slider_left_x_index, y_cur + add_to_next))
            slider_left[color_n] = y_cur
        y_max_col = max(slider_left)
        print(f'滑块左边白值总和:{y_max_col}')
        y_start_cur = slider_left[y_max_col]
        print(f'缺口图像y轴初始位置:{y_start_cur}')
        # 缺口出现范围大概在x轴[48-52]-220
        gap_left = {}
        for x_cur in range(slider_left_x_index + _pixel + _shadow_width, 220):
            color_n = 0
            for y_cur in range(y_start_cur, y_start_cur + _pixel):
                color_n += img.getpixel((x_cur, y_cur))
            gap_left[x_cur] = color_n
        _maybe = []
        for x_cur in gap_left:
            if gap_left[x_cur] in range(int(y_max_col * 0.85), int(y_max_col * 1.3)):
                _maybe.append(x_cur)
        print(f'找到缺口可能位置{_maybe}')
        # 没找到暂时返回滑块长度加滑块起始位置
        if len(_maybe) == 0:
            return 42 + slider_left_x_index, slider_left_x_index
        elif len(_maybe) == 1:
            return _maybe[0], slider_left_x_index
        # 多个结果，则找相邻（缺口内不会有太多干扰元素）结果间差距在38-43之间的第一个数
        _max_diff = {}
        for i in range(len(_maybe) - 1):
            if _maybe[i + 1] - _maybe[i] in range(38, 43):
                return _maybe[i], slider_left_x_index
            else:
                _max_diff[_maybe[i + 1] - _maybe[i]] = _maybe[i]
        return _max_diff[max(_max_diff)], slider_left_x_index

    # 模拟滑动
    def _make_curve(self, points):
        """

        :return:
        """
        # curve base
        points = np.array(points)
        x = points[:, 0]
        y = points[:, 1]

        t = range(len(points))
        ipl_t = np.linspace(0.0, len(points) - 1, 100)

        x_tup = si.splrep(t, x, k=3)
        y_tup = si.splrep(t, y, k=3)

        x_list = list(x_tup)
        xl = x.tolist()
        x_list[1] = xl + [0.0, 0.0, 0.0, 0.0]

        y_list = list(y_tup)
        yl = y.tolist()
        y_list[1] = yl + [0.0, 0.0, 0.0, 0.0]

        x_i = si.splev(ipl_t, x_list)
        y_i = si.splev(ipl_t, y_list)
        return (x_i, y_i)

    def _btn_slide(self, x_offset=0, _x_start=22):
        x_offset = x_offset - _x_start
        slider = self.driver.find_element_by_class_name("geetest_slider_button")
        section = x_offset
        left_time = 1
        x_move_list = self._get_x_move_speed(x_offset, left_time, section)
        xy_list = []
        for i in x_move_list:
            xy_list.append([i, random.random()])
        action = ActionChains_Fake(self.driver)
        # action.w3c_actions.key_action.pause = lambda *a, **k: None
        action.move_to_element(slider)
        action.perform()
        # x_i, y_i = self._make_curve(xy_list)
        action.click_and_hold(slider)
        action.perform()
        for x, y in xy_list:
            # Add a little randomization to x and y (IMPORTANT!)
            x += random.uniform(0.01, 0.05)
            y += random.uniform(-0.6, -0.3)

            action.move_by_offset(xoffset=x, yoffset=y)
        action.release()
        action.perform()

    def _get_x_move_speed(self, distance=0, left_time=0, section=10):
        origin_speed = distance * 2
        acc_speed = origin_speed / left_time / left_time / section
        move_offset = []
        new_speed = origin_speed
        for i in range(0, section):
            new_speed = new_speed - acc_speed
            move_offset.append(round(new_speed / section))
            if sum(move_offset) >= distance or (round(new_speed / section)) == 0:
                break
        if sum(move_offset) < distance:
            move_offset.append(distance - sum(move_offset))
        return move_offset
