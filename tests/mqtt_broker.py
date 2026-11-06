"""Локальний MQTT-брокер для тестів (WebSocket і TCP). Використання: python tests/mqtt_broker.py WS_ПОРТ [TCP_ПОРТ]"""
import asyncio,sys
from amqtt.broker import Broker
ls={'default':{'type':'ws','bind':'127.0.0.1:'+sys.argv[1]}}
if len(sys.argv)>2:ls['tcp']={'type':'tcp','bind':'127.0.0.1:'+sys.argv[2]}
async def main():
    b=Broker({'listeners':ls,'auth':{'allow-anonymous':True},'topic-check':{'enabled':False}});await b.start();await asyncio.Event().wait()
asyncio.run(main())
