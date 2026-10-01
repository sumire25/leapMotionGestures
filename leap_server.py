import leap
import time
import json
import asyncio
import websockets
import base64
import numpy as np
import cv2
from leapc_cffi import ffi

class TrackingListener(leap.Listener):
    def __init__(self):
        super().__init__()
        self.latest_frame_data = None
        self.latest_image_b64 = None

    def on_tracking_event(self, event):
        if not event.hands:
            self.latest_frame_data = []
            return
            
        hands_data = []
        for hand in event.hands:
            # MediaPipe uses a 21-point hand model. We construct this from Leap data.
            # Leap coordinates are in mm. The JS app's math is scale-invariant, 
            # so we can send raw mm directly!
            
            lm = [None] * 21
            # 0: Wrist
            lm[0] = {"x": hand.arm.next_joint.x, "y": hand.arm.next_joint.y, "z": hand.arm.next_joint.z}
            
            # Map the 5 fingers. Leap finger_ids: 0=Thumb, 1=Index, 2=Middle, 3=Ring, 4=Pinky
            # MediaPipe finger base indices: Thumb=1, Index=5, Middle=9, Ring=13, Pinky=17
            base_indices = {0: 1, 1: 5, 2: 9, 3: 13, 4: 17}
            
            for digit in hand.digits:
                base = base_indices[digit.finger_id]
                # MCP
                lm[base] = {"x": digit.proximal.prev_joint.x, "y": digit.proximal.prev_joint.y, "z": digit.proximal.prev_joint.z}
                # PIP
                lm[base+1] = {"x": digit.intermediate.prev_joint.x, "y": digit.intermediate.prev_joint.y, "z": digit.intermediate.prev_joint.z}
                # DIP
                lm[base+2] = {"x": digit.distal.prev_joint.x, "y": digit.distal.prev_joint.y, "z": digit.distal.prev_joint.z}
                # TIP
                lm[base+3] = {"x": digit.distal.next_joint.x, "y": digit.distal.next_joint.y, "z": digit.distal.next_joint.z}
                
            hands_data.append(lm)
            
        self.latest_frame_data = hands_data

    def on_image_event(self, event):
        try:
            # event.image()[0] is the left camera, [1] is the right camera
            img = event.image()[0]
            w = img._data.properties.width
            h = img._data.properties.height
            bpp = img._data.properties.bpp
            
            # Extract raw bytes using cffi
            buf = ffi.buffer(img._data.data, w * h * bpp)
            arr = np.frombuffer(buf, dtype=np.uint8).reshape((h, w))
            
            # Encode as JPEG
            success, enc = cv2.imencode('.jpg', arr)
            if success:
                self.latest_image_b64 = base64.b64encode(enc).decode('utf-8')
        except Exception as e:
            print("Image processing error:", e)

listener = TrackingListener()

async def broadcast_leap(websocket):
    print("Web browser connected!")
    try:
        while True:
            payload = {}
            if listener.latest_frame_data is not None:
                payload["hands"] = listener.latest_frame_data
                listener.latest_frame_data = None
            if listener.latest_image_b64 is not None:
                payload["image"] = listener.latest_image_b64
                listener.latest_image_b64 = None
                
            if payload:
                await websocket.send(json.dumps(payload))
                
            await asyncio.sleep(0.016)  # ~60 fps
    except websockets.exceptions.ConnectionClosed:
        print("Web browser disconnected.")

async def main():
    connection = leap.Connection()
    connection.add_listener(listener)
    with connection.open():
        connection.set_tracking_mode(leap.TrackingMode.Desktop)
        try:
            # Request images from the Leap Motion
            connection.set_policy_flags(leap.PolicyFlag.Images, 0)
        except Exception as e:
            print("Could not set policy flag for images:", e)
            
        print("Leap Motion listening... Starting WebSocket server on ws://localhost:8765")
        
        async with websockets.serve(broadcast_leap, "localhost", 8765):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
