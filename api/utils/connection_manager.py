from fastapi import WebSocket
from typing import List

class ConnectManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """

        :param websocket: 웹 소켓 연결 추가
        :return:
        """

        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            print(f"연결해제 하였음 {websocket.client}")

    async def broadcast(self, message : dict):
        """

        :param message: 활성 연결에 메세지 브로드 캐스트
        :return:
        """
        for connect in self.active_connections:
            try:
                await connect.send_json(message)
            except Exception as e :
                print(f"연결 실패 {e}")