import time
import cv2
import math
import numpy as np
from enum import Flag, auto

class TimeManagerState(Flag):
    """
    タイムマネージャーのフラッグ
    """
    WAIT = auto()
    MEASURE = auto()


class TimeManager:
    """
    時間管理クラス
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.state = TimeManagerState.WAIT
        self.start = time.time()
        self.end = self.start

    def start_measure(self):
        """
        計測開始
        """
        if self.state == TimeManagerState.WAIT:
            self.start = time.time()
            self.state = TimeManagerState.MEASURE

    def time(self):
        """
        時間を取得する関数
        計測中は計測開始してからの時間を返す
        待機中はself.endとself.startの差を返す

        Output:
            t: float  経過時間
        """
        if self.state == TimeManagerState.MEASURE:
            t = time.time() - self.start
        elif self.state == TimeManagerState.WAIT:
            t = self.end - self.start

        return t

    def finish_measure(self):
        """
        計測終了
        """
        if self.state == TimeManagerState.MEASURE:
            self.end = time.time()
            self.state = TimeManagerState.WAIT

"""
Gameクラスで使用する関数群
"""
#####################################################

def clahe(image):

    img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    image = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

    return image

def is_center(x, y, center_x, center_y):
    # error
    ERR = 25

    return (x<=center_x+ERR and x>=center_x-ERR and y <= center_y+ERR  and y>=center_y-ERR)

def detect_color(image, color_bottom, color_top):
    # ブラー
    image = cv2.blur(image, (5,5))

    # ヒストグラム平坦化
    image = clahe(image)

    # RGBからHSVに色調変換
    hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 指定した色の範囲でマスク画像を作成
    msk_img = cv2.inRange(hsv_img, color_bottom, color_top)

    # マスク画像を返す
    return msk_img

def draw_circle(image, x, y, r, color):
    """
    指定座標を中心とした円を描画する関数

    Args:
        image: 描画先の映像
        x: 中心のx座標
        y: 中心のy座標
        r: 円の半径
        color: 三角形の色 (BGR)

    Outputs:
        image: 円が描画された画像
    """

    # フレームの中心に円を描画
    marker_thickness = 2  # 線の太さ
    cv2.circle(image, (x, y), r, color, marker_thickness)

    return image



def draw_triangle(image, x, y, r, color):
    """
    指定座標を中心とした正三角形を描画する関数

    Args:
        image: 描画先の画像
        x: 中心のx座標
        y: 中心のy座標
        r: 中心から頂点の距離
        color: 三角形の色 (BGR)

    Outputs:
        image: 正三角形が描画された画像
    """
    pnt1 = [x, y-r]
    pnt2 = [x + (math.sqrt(3) / 2) * r, y + (r / 2)]
    pnt3 = [x - (math.sqrt(3) / 2) * r, y + (r / 2)]

    pts = np.array([pnt1, pnt2, pnt3], dtype='int32')

    cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
    cv2.fillConvexPoly(image, pts, (0, 255, 0))

    return image

#######################################################

class GameState(Flag):
    """
    ゲーム状態のフラッグ
    READY: 開始準備状態
    PLAY: プレイ中
    GAME_OVER: ゲームオーバー
    CLEAR: ゲームクリア
    """

    READY = auto()
    PLAY = auto()
    GAME_OVER = auto()
    CLEAR = auto()

class Game():
    """
    ゲームシステムクラス
    """

    def __init__(self):
        """
        コンストラクタ
        """
        self.timemanager = TimeManager()
        self.state = GameState.READY
        self.start_pnt = 0
        self.goal_pnt = 0
        self.collision = False

    def detect_start(self, image, add=True):
        """
        スタート地点を検出するメソッド

        Args:
            image: カメラ映像
            add: bool start_pntを加算するかどうか

        Outputs:
            bool: 映像の中心がgoal地点にいるか否か
            image: カメラ映像
        """

        # 青色の閾値を設定
        COLOR_BLUE_BOTTOM = np.array([90,128,64])
        COLOR_BLUE_TOP = np.array([150,255,255])

        # 画像のサイズを取得
        height, width = image.shape[:2]

        # 画像の中心を取得
        center_x, center_y = width // 2, height // 2

        # 切り取る大きさ
        CROP_RECT = 30

        # 画像の中心を切り取る
        crop_img = image[center_y-CROP_RECT : center_y+CROP_RECT, center_x-CROP_RECT : center_x+CROP_RECT]

        crop_height, crop_width = crop_img.shape[:2]
        crop_center_x , crop_center_y = crop_width // 2, crop_height // 2

        msk_img = detect_color(crop_img, COLOR_BLUE_BOTTOM, COLOR_BLUE_TOP)
        # msk_img = detect_color(image, COLOR_BLUE_BOTTOM, COLOR_BLUE_TOP)
        # masked_img = cv2.bitwise_and(image, image, mask= msk_img)


        _, _, _, centroids = cv2.connectedComponentsWithStats(msk_img)
        centroids = np.delete(centroids, 0, 0)

        """
        for _i in range(0, min(len(centroids), 3)):
            cv2.putText(masked_img, "blue point", (int(centroids[_i][0]), int(centroids[_i][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255-(_i*50)), 2)

        if len(centroids) > 0 and is_center(centroids[0][0], centroids[0][1], crop_center_x, crop_center_y):
            print("detect start!")
            self.start_pnt += 1

        return masked_img

        """

        if len(centroids) > 0 and is_center(centroids[0][0], centroids[0][1], crop_center_x, crop_center_y):
            print("detect start!")
            if add:
                self.start_pnt += 1
            return True, image
        else:
            return False, image

        # """

    def detect_goal(self, image, add=True):
        """
        ゴール地点を検出するメソッド

        Args:
            image: カメラ映像
            add: bool goal_pntを加算するかどうか

        Outputs:
            bool: 映像の中心がゴール地点か否か
            image: カメラ映像
        """

        # 赤色の閾値を設定
        COLOR_RED_BOTTOM1 = np.array([0, 50, 50])
        COLOR_RED_BOTTOM2 = np.array([174, 50, 50])
        COLOR_RED_TOP1 = np.array([6, 255, 255])
        COLOR_RED_TOP2 = np.array([180,255,255])

        # 画像のサイズを取得
        height, width = image.shape[:2]

        # 画像の中心を取得
        center_x, center_y = width // 2, height // 2

        # 切り取る大きさ
        CROP_RECT = 30

        # 画像の中心を切り取る
        crop_img = image[center_y-CROP_RECT : center_y+CROP_RECT, center_x-CROP_RECT : center_x+CROP_RECT]

        crop_height, crop_width = crop_img.shape[:2]
        crop_center_x , crop_center_y = crop_width // 2, crop_height // 2


        # マスク画像を取得
        msk_img1 = detect_color(crop_img, COLOR_RED_BOTTOM1, COLOR_RED_TOP1)
        msk_img2 = detect_color(crop_img, COLOR_RED_BOTTOM2, COLOR_RED_TOP2)
        msk_img = msk_img1 + msk_img2
        # masked_img = cv2.bitwise_and(image, image, mask= msk_img)

        _, _, _, centroids = cv2.connectedComponentsWithStats(msk_img)

        centroids = np.delete(centroids, 0, 0)

        """
        for _i in range(0, min(len(centroids), 3)):
            cv2.putText(masked_img, "red point", (int(centroids[_i][0]), int(centroids[_i][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0,255-(_i*50)), 2)

        return masked_img

        """

        if len(centroids) > 0 and is_center(centroids[0][0], centroids[0][1], crop_center_x, crop_center_y):
            print("detect goal!")
            if add:
                self.goal_pnt += 1
            return True, image
        else:
            return False, image

        # """

    def detect_center_contours(self, image):
        """
        カメラ映像の中心の輪郭を検出するメソッド

        Args:
            image: カメラ映像

        Outputs:
            contours: 輪郭線
            image: 輪郭線と検出図形を付加したカメラ映像
        """

        # 画像のサイズを取得
        height, width = image.shape[:2]

        # 画像の中心を取得
        center_x, center_y = width // 2, height // 2

        # 切り取る画像のサイズ
        CROP_RECT = 30

        crop_img = image[center_y-CROP_RECT : center_y+CROP_RECT, center_x-CROP_RECT : center_x+CROP_RECT]

        # Canny 法
        canny_image = cv2.Canny(crop_img, 100, 200)

        # モルフォロジー演算
        morp_image = cv2.morphologyEx(canny_image, cv2.MORPH_CLOSE, np.ones((5, 5), dtype=canny_image.dtype))

        # 輪郭線を取得
        contours, _ = cv2.findContours(morp_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
                arclen = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, arclen * 4.0e-2, True)
                crop_img = cv2.drawContours(crop_img, [approx], -1, (255,0,0), 3, cv2.LINE_AA)
                """
                if len(approx) == 3:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    position = np.asarray(approx).reshape((-1, 2)).max(axis=0).astype('int32')
                    px, py = position
                    cv2.putText(crop_img, "triangle", (px, py), font, 0.3, (0, 0, 0), 2, cv2.LINE_AA)
                """

        image[center_y-CROP_RECT : center_y+CROP_RECT, center_x-CROP_RECT : center_x+CROP_RECT] = crop_img

        return contours, image

    def collision_check(self, image):
        """
        衝突を判定するメソッド

        Args:
            image: カメラ映像

        Outputs:
            collision: bool 衝突したかどうか
            image: カメラ映像
        """
        collision = False

        contours, image = self.detect_center_contours(image)

        # 各輪郭線が三角形かどうか判断
        is_triangle = False
        for cnt in contours:
            arclen = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, arclen * 4.0e-2, True)
            n_gon = len(approx)
            if (n_gon == 3):
                is_triangle = True

        if len(contours) > 0 and is_triangle == False:
            print("collision occur!")
            collision = True

        return collision, image



    def reset(self):
        """
        ゲームをリセットするメソッド
        """

        self.state = GameState.READY
        self.start_pnt = 0
        self.goal_pnt = 0
        self.collision = False
        self.timemanager = TimeManager()

    def state_changer(self):
        """
        ステートマシンを更新するメソッド
        """

        if self.start_pnt > 10 and self.state == GameState.READY:
            self.start_pnt = 0
            self.state = GameState.PLAY
            self.timemanager.start_measure()
        elif self.goal_pnt > 10 and self.state == GameState.PLAY:
            self.goal_pnt = 0
            self.state = GameState.CLEAR
            self.timemanager.finish_measure()
        elif self.collision and self.state == GameState.PLAY:
            self.collision = False
            self.state = GameState.GAME_OVER

    def rogic(self, image):
        """
        ゲームロジックを動かすメソッド

        Args:
            image: カメラ映像

        Outputs:
            image: 処理を施したカメラ映像
        """
        if self.state == GameState.READY:
            _, image = self.detect_start(image)

            height, width = image.shape[:2]
            center_x, center_y = width//2, height//2

            image = draw_circle(image, center_x, center_y, 10, (0, 255, 0))
        elif self.state == GameState.PLAY:
            is_start, _ = self.detect_start(image, add=False)
            is_goal, _ = self.detect_goal(image)

            height, width = image.shape[:2]
            center_x, center_y = width//2, height//2

            image = draw_triangle(image, center_x, center_y, 10, (0, 255, 0))

            if (not is_start) and (not is_goal):
                self.collision, image = self.collision_check(image)

        elif self.state == GameState.GAME_OVER:
            height, width = image.shape[:2]
            center_x, center_y = width//2, height//2

            image = draw_triangle(image, center_x, center_y, 10, (0, 255, 0))

        self.state_changer()

        return image