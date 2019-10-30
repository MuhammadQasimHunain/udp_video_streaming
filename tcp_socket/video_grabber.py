# Standard modules
from threading import Thread, Lock
import time
import sys
# External modules
import cv2
# Local modules
import utils


try:
    from turbojpeg import TurboJPEG
except ImportError as error:
    print("Warning, failed to import turbojpeg, "
          "you will not be able to use it")


class VideoGrabber(Thread):
    """A threaded video grabber.

    Attributes:
    encode_params ():
    cap (str):
    attr2 (:obj:`int`, optional): Description of `attr2`.

    """
    def __init__(self, jpeg_quality, jpeg_lib, resize):
        """Constructor.

        Args:
        jpeg_quality (:obj:`int`): Quality of JPEG encoding, in 0, 100.
        resize (:obj:`float'): resize factor in [0, 1]

        """
        Thread.__init__(self)
        self.cap = cv2.VideoCapture(0)
        self.turbojpeg = TurboJPEG()
        self.resize_factor = resize
        self.running = True
        self.buffer = None
        self.lock = Lock()

        self.jpeg_handler = utils.make_jpeg_handler(jpeg_lib, jpeg_quality)

    def stop(self):
        self.running = False

    def get_buffer(self):
        """Method to access the encoded buffer.

            Returns:
            np.ndarray: the compressed image if one has been acquired.
                        None otherwise.
        """
        if self.buffer is not None:
            self.lock.acquire()
            cpy = self.buffer
            self.lock.release()
            return cpy

    def run(self):
        while self.running:
            success, img = self.cap.read()
            target_size = (int(img.shape[1] * self.resize_factor),
                           int(img.shape[0] * self.resize_factor))
            img = cv2.resize(img, target_size)
            if not success:
                continue

            # JPEG compression
            # Protected by a lock
            # As the main thread may asks to access the buffer
            self.lock.acquire()
            self.buffer = self.jpeg_handler.compress(img)
            self.lock.release()


if __name__ == '__main__':

    jpeg_quality = 100

    grabber = VideoGrabber(jpeg_quality, jpeg_lib='turbo')
    grabber.start()
    time.sleep(1)

    turbo_jpeg = TurboJPEG()

    cv2.namedWindow("Image")

    keep_running = True
    idx = 0
    t0 = time.time()

    while keep_running:
        data = grabber.get_buffer()
        if data is None:
            time.sleep(1)
            continue
        img = turbo_jpeg.decode(data)
        cv2.imshow("Image", img)
        keep_running = not(cv2.waitKey(1) & 0xFF == ord('q'))

        idx += 1
        if idx == 100:
            t1 = time.time()
            sys.stdout.write("\r {:04} images/second    ".format(100/(t1-t0)))
            sys.stdout.flush()
            t0 = t1
            idx = 0

    print()
    print("Quitting")
    grabber.stop()
