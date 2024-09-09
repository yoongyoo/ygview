from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QFont, QColor, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QInputDialog, QGraphicsView, QGraphicsPixmapItem, QWidget, QVBoxLayout, QGraphicsScene
import numpy as np
import cv2
import keyboard

class View(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.images = []
        self.is_change = False
        self.current_index = 0  # 현재 선택된 영상의 인덱스
        self.swap_with_index = None  # 특정 영상과 교체할 때 사용할 인덱스
        self.swap_with_user_defined = False

    def init_ui(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

    def set_image(self, file_name):
        if file_name.lower().endswith((".jpg", ".bmp", ".png")):
            img_array = np.fromfile(file_name, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif file_name.lower().endswith(".raw"):
            file = open(file_name, 'rb')
            img = np.fromfile(file, dtype='int16', sep="")
            width, height = 8192, 6144  # Example dimensions
            img = img.reshape((height, width))
            img = img >> 2
            img = np.uint8(img)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            print("Unsupported format")
            exit(-1)

        image = Image()
        image.file_name = file_name
        image.mouseMoved.connect(self.mouseMoved)
        image.mousePressed.connect(self.mousePressed)
        image.mouseReleased.connect(self.mouseReleased)
        image.wheelPressed.connect(self.wheelPressed)
        self.images.append(image)
        image.set_image(img)
        image.fitInView()

    # def swap_images(self, index1, index2):

    #     rgb1 = self.images[index1].image_view[0, 0]
    #     rgb2 = self.images[index2].image_view[0, 0]

    #     print("before", rgb1, rgb2)

    #     if 0 <= index1 < len(self.images) and 0 <= index2 < len(self.images):
    #         # 리스트에서 두 영상을 교체
    #         print("run swap", index1, index2)

    #         img1 = self.images[index2].image_view
    #         img2 = self.images[index1].image_view
    #         self.images[index1], self.images[index2] = self.images[index2], self.images[index1]

    #         rgb1 = self.images[index1].image_view[0, 0]
    #         rgb2 = self.images[index2].image_view[0, 0]

    #         self.images[index1].set_image(img1)
    #         self.images[index2].set_image(img2)

    #         print("after", rgb1, rgb2)
    #         # self.update_view()

    #         for image in self.images:
    #             image.draw_image()

    def swap_images(self, index1, index2):
        if 0 <= index1 < len(self.images) and 0 <= index2 < len(self.images):
            # 리스트에서 이미지 데이터를 교체
            # self.images[index1], self.images[index2] = self.images[index2], self.images[index1]

            # 교체된 이미지 데이터를 가져옴
            img1 = self.images[index1].image_view
            img2 = self.images[index2].image_view

            # 각 이미지에 새로운 QPixmap을 설정 (화면 갱신을 위해)
            self.images[index2]._photo.setPixmap(QPixmap.fromImage(self.convert_to_qimage(img1)))
            self.images[index1]._photo.setPixmap(QPixmap.fromImage(self.convert_to_qimage(img2)))

            # 화면에 즉시 반영되도록 뷰 업데이트
            self.images[index1].update()
            self.images[index2].update()

            self.images[index1], self.images[index2] = self.images[index2], self.images[index1]

    def convert_to_qimage(self, image):
        """이미지 배열을 QImage로 변환하는 헬퍼 함수."""
        height, width, pattern = image.shape
        return QImage(image.data, width, height, width * pattern, QImage.Format_RGB888)

            



    def update_view(self):
        """영상의 위치가 변경된 후 화면을 갱신하는 함수."""
        for i, image in enumerate(self.images):
            print("img index", i)
            image.draw_image()  # 각 이미지의 새로운 위치를 설정

    def mouseMoved(self, event):
        for image in self.images:
            image.mouseMoveEventHandler(event)

    def mousePressed(self, event):
        for image in self.images:
            image.mousePressEventHandler(event)

    def mouseReleased(self, event):
        for image in self.images:
            image.mouseReleaseEventHandler(event)

    def wheelPressed(self, event):
        for image in self.images:
            image.wheelEventHandler(event)
        self.SyncCenter()

    def SyncCenter(self):
        if not keyboard.is_pressed("ctrl"):
            current_img, current_img_idx = self.current_image()
            if current_img is not None:
                center = current_img.getCenter()
                for image in self.images:
                    if image is not current_img:
                        image.setCenter(center)

    def current_image(self):     
        for idx, img in enumerate(self.images):
            if img.underMouse():
                return img, idx
        return None, None

    def keyPressEvent(self, event):
        self.SyncCenter()

        if event.key() == Qt.Key_T:
            self.handle_swap_images()
        elif event.key() == Qt.Key_Y:
            self.open_swap_dialog()
        QWidget.keyPressEvent(self, event)

    def handle_swap_images(self):
        current_img, self.current_index = self.current_image()
        if current_img is not None:
            if((self.swap_with_user_defined is False) or (self.current_index == self.swap_with_index)):
                print("automatically next index")
                self.swap_with_index = (self.current_index + 1) % len(self.images)

            print(self.current_index, self.swap_with_index)
            self.swap_images(self.current_index, self.swap_with_index)

    def open_swap_dialog(self):
        """영상 교체를 위한 다이얼로그를 띄우는 함수."""
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setLabelText("교체할 영상 번호를 입력하세요:")
        dialog.setIntRange(0, len(self.images) - 1)
        dialog.setIntValue(self.current_index)
        if dialog.exec_() == QInputDialog.Accepted:
            _swap_with_index = dialog.intValue()
            if _swap_with_index == self.current_index:
                print("same index with current_index, automatically selected next index")
                _swap_with_index = (self.current_index + 1) % len(self.images)

            self.swap_with_index = _swap_with_index

            print("swap dialog", self.current_index, self.swap_with_index)

            self.swap_with_user_defined = True
            # self.swap_images(self.current_index, self.swap_with_index)
            # self.current_index = self.swap_with_index

class Image(QGraphicsView):
    mouseMoved = pyqtSignal(QMouseEvent)
    mousePressed = pyqtSignal(QMouseEvent)
    mouseReleased = pyqtSignal(QMouseEvent)
    wheelPressed = pyqtSignal(QWheelEvent)

    def __init__(self):
        super().__init__()
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)

        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QGraphicsView.NoFrame)
        self.zoom_idx = 0

    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            ratio = min(viewrect.width() / scenerect.width(), viewrect.height() / scenerect.height())
            self.scale(ratio, ratio)
            self.zoom_idx = 0

    def set_image(self, image):
        self.image_view = image
        self.height, self.width, self.pattern = image.shape
        self.draw_image()

    # def swap_images(self, index1, index2):
    #     """두 영상의 위치를 바꾸고 화면을 갱신하는 함수."""
    #     if 0 <= index1 < len(self.images) and 0 <= index2 < len(self.images):
    #         # 리스트에서 두 영상을 교체
    #         self.images[index1], self.images[index2] = self.images[index2], self.images[index1]
    #         self.update_view()  # 화면을 갱신

    # def update_view(self):
    #     """영상의 위치가 변경된 후 화면을 갱신하는 함수."""
    #     for i, image in enumerate(self.images):
    #         image.update_position(i)  # 각 이미지의 새로운 위치를 설정

    def draw_image(self):
        qImg = QImage(self.image_view.data, self.width, self.height, self.width * self.pattern, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qImg)

        if pixmap and not pixmap.isNull():
            self._empty = False
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self._photo.setPixmap(QPixmap())

    def paintEvent(self, event):
        super().paintEvent(event)  # 부모 클래스의 paintEvent 호출

        if self.zoom_idx >= 25:
            painter = QPainter(self.viewport())
            if painter.isActive():
                font = QFont("Arial", 8)  # 적절한 글자 크기로 설정
                painter.setFont(font)
                painter.setPen(QColor(255, 0, 0))  # 글씨색을 하얀색으로 설정

                # 현재 보이는 영역의 픽셀 좌표만 계산하여 RGB 값 디스플레이
                view_rect = self.viewport().rect()
                scene_rect = self.mapToScene(view_rect).boundingRect()

                # 이미지 좌표를 계산하기 위한 변환
                transform = self.transform()
                inverse_transform = transform.inverted()[0]  # 역변환 행렬

                # # View의 영역에서 각 픽셀에 대해 RGB 값을 계산하여 표시

                # print(view_rect)
                # print(view_rect.height(), view_rect.width())
                # print(view_rect.left(), view_rect.right(), view_rect.top(), view_rect.bottom())

                y_intv = 0
                x_intv = 0
                for y in range(int(scene_rect.top()), int(scene_rect.bottom())):
                    x_intv = 0
                    for x in range(int(scene_rect.left()), int(scene_rect.right())):
                        # 이미지 좌표로 변환
                        image_point = inverse_transform.map(QPointF(x, y))
                        draw_x = int(image_point.x() + x_intv) + 20
                        draw_y = int(image_point.y() + y_intv) + 20

                        rgb = self.image_view[int(y), int(x)]
                        r, g, b = rgb

                        print(x, y, draw_x, draw_y)

                        # 이미지의 범위를 벗어나지 않는 경우
                        if 0 <= draw_x < view_rect.width() and 0 <= draw_y < view_rect.height():
                            # 화면상의 픽셀 중앙에 RGB 값을 표시
                            painter.drawText(draw_x, draw_y, f"R:{r} G:{g} B:{b}")
                        
                        x_intv = x_intv + transform.m11()

                    y_intv = y_intv + transform.m22()

    def wheelEventHandler(self, event):
        if event.angleDelta().y() > 0:
            if self.zoom_idx < 27:
                self.zoom_idx += 1
                self.scale(5/4, 5/4)
                self.is_change = True
            else:
                self.is_change = False
        elif event.angleDelta().y() < 0:
            if self.zoom_idx > 0:
                self.zoom_idx -= 1
                self.scale(4/5, 4/5)
                self.is_change = True
            else:
                self.is_change = False

        self.update()  # paintEvent 호출을 위해 업데이트

    def wheelEvent(self, event):
        if keyboard.is_pressed("ctrl"):
            self.wheelEventHandler(event)
        else:
            self.wheelPressed.emit(event)

    def mouseMoveEventHandler(self, event):
        QGraphicsView.mouseMoveEvent(self, event)
        self.update()  # 마우스 이동 시 화면 업데이트

    def mouseMoveEvent(self, event):
        if keyboard.is_pressed("ctrl"):
            self.mouseMoveEventHandler(event)
        else:
            self.mouseMoved.emit(event)
        self.update()  # 마우스 이동 시 화면 업데이트

    def mousePressEventHandler(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        QGraphicsView.mousePressEvent(self, event)

    def mousePressEvent(self, event):
        if keyboard.is_pressed("ctrl"):
            self.mousePressEventHandler(event)
        else:
            self.mousePressed.emit(event)

    def mouseReleaseEventHandler(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
        elif event.button() == Qt.RightButton:
            self.fitInView()
            self.setDragMode(QGraphicsView.NoDrag)
        QGraphicsView.mouseReleaseEvent(self, event)

    def mouseReleaseEvent(self, event):
        if keyboard.is_pressed("ctrl"):
            self.mouseReleaseEventHandler(event)
        else:
            self.mouseReleased.emit(event)

    def setCenter(self, center):
        self.centerOn(center)
    
    def getCenter(self):
        return self.mapToScene(self.rect().center())
    
    def update_position(self, index):
        self.draw_image()
