import asyncio
import traceback
import logging

from ccxt import async_support

"""
Buy every minute if the previous last price goes up and sell if it goes down

Exchange: bitFlyer lightning FX
Symbol: BTC/JPY
"""


async def get_position(client: async_support.bitflyer):
    """
    :param client:
    :return: Long/Short amount
    """
    response = await client.private_get_getpositions(params={"product_code": "FX_BTC_JPY"})
    long_size = sum([x['size'] for x in response if x['side'] == "BUY"])
    short_size = sum([x['size'] for x in response if x['side'] == "SELL"])
    return long_size, short_size


async def get_collateral(client: async_support.bitflyer):
    """
    :param client:
    :return: collateral
    """
    response = await client.fetch2(path='getcollateral', api='private', method='GET')
    return int(response['collateral'])


async def get_ltp(client: async_support.bitflyer):
    """
    :param client:
    :return: last price
    """
    data = await client.fetch_ticker(symbol='BTC/JPY', params={"product_code": "FX_BTC_JPY"})
    return data["info"]["ltp"]


async def send_order(client: async_support.bitflyer, side, size, price=0, order_type="market"):
    """
    :param client:
    :param side: "BUY" or "SELL"
    :param size: minimum order size is 0.01
    :param price: if the order type is "market", set 0 instead
    :param order_type: "market" or "limit"
    :return: order response from a server
    """
    return await client.create_order(symbol='BTC/JPY', type=order_type, side=side, amount=size, price=price, params={"product_code": "FX_BTC_JPY"})


async def trade(client: async_support.bitflyer):
    """
    :param client:
    """
    prev_ltp = None

    while True:
        try:
            collateral = await get_collateral(client)

            if collateral < 10000:
                continue

            ltp = await get_ltp(client)
            logging.info(f"ltp={ltp}")

            if prev_ltp is None:
                prev_ltp = ltp
                continue

            long_size, short_size = await get_position(client)

            logging.info(f"collatral={collateral}, L={long_size}, S={short_size}")

            size = 0.01

            if ltp > prev_ltp and long_size < size:
                response = await send_order(client, side="BUY", size=size)
                logging.info(f"BUY:{response}")
            elif ltp < prev_ltp and short_size < size:
                response = await send_order(client, side="SELL", size=size)
                logging.info(f"SELL:{response}")
        except:
            traceback.print_exc()
        finally:
            await asyncio.sleep(60)


if __name__ == '__main__':
    cc = async_support.bitflyer({
        'apiKey': "*******",
        'secret': "*******"
    })

    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)

    logging.root.setLevel(logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.INFO)

    try:
        loop.run_until_complete(
            asyncio.gather(
                trade(client=cc)
            )
        )
    except:
        traceback.print_exc()
    finally:
        loop.close()
