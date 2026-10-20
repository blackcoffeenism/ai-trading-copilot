import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
import aiohttp
from fastapi import WebSocket

logger = logging.getLogger("binance_ws")
logging.basicConfig(level=logging.INFO)

class BinanceWebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        # Default symbols we track and subscribe to on Binance
        self.symbols = ["btcusdt", "ethusdt", "solusdt", "xrpusdt", "adausdt", "dogeusdt"]
        
    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active clients: {len(self.active_connections)}")
        
    def disconnect_client(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active clients: {len(self.active_connections)}")
            
    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        # Create a list of send coroutines
        payload = json.dumps(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect_client(conn)

    async def start(self):
        """Starts the Binance WebSocket background consumer task."""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._consume_binance_stream())
        logger.info("Binance consumer background task initialized.")

    async def stop(self):
        """Stops the consumer loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Binance consumer background task terminated.")

    async def _consume_binance_stream(self):
        # Construct the multi-stream subscription URL
        # Streams format: symbol@streamName
        # e.g., btcusdt@ticker / btcusdt@kline_1m / btcusdt@trade / btcusdt@depth5
        stream_names = []
        for sym in self.symbols:
            stream_names.append(f"{sym}@ticker")
            stream_names.append(f"{sym}@kline_1m")
            stream_names.append(f"{sym}@trade")
            stream_names.append(f"{sym}@depth5")
            
        url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(stream_names)}"
        
        backoff = 1  # starting backoff in seconds
        
        while self.running:
            logger.info(f"Connecting to Binance Stream: {url}")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url) as ws:
                        logger.info("Successfully connected to Binance WebSocket API.")
                        backoff = 1  # reset backoff upon successful connection
                        
                        async for msg in ws:
                            if not self.running:
                                break
                                
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                stream = data.get("stream", "")
                                payload = data.get("data", {})
                                
                                # Format and standardise payload before broadcasting to UI client
                                formatted_message = self._format_binance_data(stream, payload)
                                if formatted_message:
                                    await self.broadcast(formatted_message)
                                    
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                logger.warning("Binance WS stream closed or returned an error. Reconnecting...")
                                break
                                
            except Exception as e:
                logger.error(f"Error in Binance stream client: {str(e)}. Attempting reconnection...")
                
            # Disconnected or failed. Apply backoff and retry.
            logger.info(f"Sleeping for {backoff} seconds before reconnecting...")
            await asyncio.sleep(backoff)
            backoff = min(60, backoff * 2)  # Exponential backoff capped at 60s

    def _format_binance_data(self, stream: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parses raw Binance WS frames into structured models for UI clients."""
        try:
            symbol = stream.split("@")[0].upper()
            stream_type = stream.split("@")[1]
            
            if "ticker" in stream_type:
                return {
                    "type": "ticker",
                    "symbol": symbol,
                    "price": float(data.get("c", 0)),          # Close price
                    "change_24h": float(data.get("p", 0)),     # Price change
                    "change_pct": float(data.get("P", 0)),     # Percent change
                    "volume_24h": float(data.get("v", 0)),     # Total volume
                    "high_24h": float(data.get("h", 0)),
                    "low_24h": float(data.get("l", 0)),
                }
                
            elif "kline" in stream_type:
                kline = data.get("k", {})
                return {
                    "type": "kline",
                    "symbol": symbol,
                    "interval": kline.get("i"),
                    "kline": {
                        "time": int(kline.get("t", 0)) // 1000, # convert millisecond timestamp to second timestamp
                        "open": float(kline.get("o", 0)),
                        "high": float(kline.get("h", 0)),
                        "low": float(kline.get("l", 0)),
                        "close": float(kline.get("c", 0)),
                        "volume": float(kline.get("v", 0)),
                        "closed": kline.get("x", False)       # Is bar complete
                    }
                }
                
            elif "trade" in stream_type:
                return {
                    "type": "trade",
                    "symbol": symbol,
                    "time": int(data.get("T", 0)) // 1000,
                    "price": float(data.get("p", 0)),
                    "quantity": float(data.get("q", 0)),
                    "buyer_maker": data.get("m", False)        # True if sell, False if buy
                }
                
            elif "depth" in stream_type:
                return {
                    "type": "depth",
                    "symbol": symbol,
                    "bids": [[float(price), float(qty)] for price, qty in data.get("b", [])],
                    "asks": [[float(price), float(qty)] for price, qty in data.get("a", [])]
                }
                
        except Exception as e:
            logger.error(f"Error parsing stream packet: {str(e)}")
            
        return None

# Global instance
binance_ws_manager = BinanceWebSocketManager()
