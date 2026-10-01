import leap
import time

class ImageListener(leap.Listener):
    def on_image_event(self, event):
        img = event.image()[0]
        try:
            print("C struct properties:")
            print(dir(img._data))
            print("width:", img._data.properties.width)
            print("height:", img._data.properties.height)
            print("data pointer:", img._data.data)
        except Exception as e:
            print(e)
        import sys; sys.exit(0)

def main():
    listener = ImageListener()
    connection = leap.Connection()
    connection.add_listener(listener)
    with connection.open():
        connection.set_policy_flags(leap.PolicyFlag.Images, 0)
        time.sleep(2)

main()
