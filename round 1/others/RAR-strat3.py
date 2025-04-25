from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Trader:
    '''
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

		# Orders to be placed on exchange matching engine
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10  # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
		    # String value holding Trader state data required. 
				# It will be delivered as TradingState.traderData on next execution.
        traderData = "SAMPLE" 
        
				# Sample conversion request. Check more details below. 
        conversions = 1
        return result, conversions, traderData
    '''
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        
        result = {}
        orders: List[Order] = []

        RAR = 'RAINFOREST_RESIN'  # alias

        # strategy for RAR
        stable_price = 10000
        
        # maximum orders to not exceed the limit
        pos = 0
        if RAR in state.position:
            pos = state.position[RAR]

        max_buy_orders = 50 - pos
        max_sell_orders = 50 + pos
        
        # optimally place buy orders
        order_depth: OrderDepth = state.order_depths[RAR]
        
        for bid_price, bid_volume in sorted(order_depth.buy_orders.items(), reverse=True):
            if (bid_price <= stable_price):
                continue
            if (max_sell_orders > 0):
                my_order = min(max_sell_orders, bid_volume)
                orders.append(Order(RAR, bid_price, -my_order))  # ask
                max_sell_orders -= my_order
            
        for ask_price, ask_volume in sorted(order_depth.sell_orders.items()):
            if (ask_price >= stable_price):
                continue
            if (max_buy_orders > 0):
                my_order = min(max_buy_orders, -ask_volume)
                orders.append(Order(RAR, ask_price, my_order))  # bid
                max_buy_orders -= my_order
        
        result[RAR] = orders

        print('sending out orders', orders)
        
        traderData = ""
        conversions = 0
        return result, conversions, traderData