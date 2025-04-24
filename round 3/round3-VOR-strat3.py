from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle
import math
import numpy as np

############### PARAMETERS ##############
current_day = 0   # ******** TO DO: CHANGE TO DAY 3
window_size = 10
lo_signal_threshold = 0.5
hi_signal_threshold = 3
############### CONSTANTS ###############
SQI = 'SQUID_INK'
KLP = 'KELP'
RAR = 'RAINFOREST_RESIN'

CST = 'CROISSANTS'
JAM = 'JAMS'
DJE = 'DJEMBES'
PB1 = 'PICNIC_BASKET1'
PB2 = 'PICNIC_BASKET2'

VOR = 'VOLCANIC_ROCK'
VOR_C9500 = 'VOLCANIC_ROCK_VOUCHER_9500'
VOR_C9750 = 'VOLCANIC_ROCK_VOUCHER_9750'
VOR_C10000 = 'VOLCANIC_ROCK_VOUCHER_10000'
VOR_C10250 = 'VOLCANIC_ROCK_VOUCHER_10250'
VOR_C10500 = 'VOLCANIC_ROCK_VOUCHER_10500'

coupons = [VOR_C9500, VOR_C9750, VOR_C10000, VOR_C10250, VOR_C10500]
strikes = {VOR_C9500: 9500, \
            VOR_C9750: 9750, \
            VOR_C10000: 10000, \
            VOR_C10250: 10250, \
            VOR_C10500: 10500}


symbols_r1 = {SQI, KLP, RAR}
symbols_r2 = {CST, JAM, DJE, PB1, PB2}
symbols_r3 = {VOR, VOR_C9500, VOR_C9750, VOR_C10000, VOR_C10250, VOR_C10500}
symbols = symbols_r1.union(symbols_r2).union(symbols_r3)

position_limits = {VOR: 400, VOR_C9500: 200, VOR_C9750: 200, VOR_C10000: 200, VOR_C10250: 200, VOR_C10500: 200, \
                   CST: 250, JAM: 350, DJE: 60, PB1: 60, PB2: 100, \
                   SQI: 50, KLP: 50, RAR: 50}

# z score to buy / sell signals
def f(z):
    if (abs(z) < lo_signal_threshold):
        return 0
    elif (abs(z) > hi_signal_threshold):
        return 1 if z > 0 else -1
    else:
        mag = (abs(z) - lo_signal_threshold) / (hi_signal_threshold - lo_signal_threshold)
        return mag if z > 0 else -mag

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bsm_call_price(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Manually computed CDF values using norm_cdf
    N_d1 = norm_cdf(d1)
    N_d2 = norm_cdf(d2)
    
    return S * N_d1 - K * np.exp(-r * T) * N_d2

def bsm_delta(S, K, T, r, sigma):
    if (sigma < 1e-6):
        return 0  # no hedging then!
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    N_d1 = norm_cdf(d1)

    return N_d1

def implied_volatility(S, K, T, r, C):
    left = 0.0
    right = 1e3
    num_iters = 50
    for _ in range(num_iters):
        mid = (left + right) / 2
        if (bsm_call_price(S, K, T, r, mid) > C):
            right = mid
        else:
            left = mid
    return left



class Trader:
    def run(self, state: TradingState):
        ############# HISTORY ##############
        history_IV = {}
        history_xi = {}
        history_zz = {}
        if (state.traderData == ""):
            traderData = {}
            for product in symbols:
                history_IV[product] = []
                history_xi[product] = []
                history_zz[product] = []
        else:
            traderData = jsonpickle.decode(state.traderData)
            for product in symbols:
                history_IV[product] = (traderData['IV'])[product]
                history_xi[product] = (traderData['xi'])[product]
                history_zz[product] = (traderData['zz'])[product]
        ############### DATA ###############
        # print("traderData: " + state.traderData)
        # print("Observations: " + str(state.observations))

        

        current_timestamp = state.timestamp
        def time_to_T(day, timestamp):
            return (8000000 - 1000000*day - timestamp) / 1000000
        T = time_to_T(current_day, current_timestamp)

        result = {}
        orders: List[Order] = []

        
        ############# USEFUL INFO #############
        bid_prices = {}
        ask_prices = {}
        highest_bids = {}
        lowest_asks = {}
        cur_pos = {}
        avg_prices = {}
        max_buy = {}
        max_sell = {}
        
        for S in symbols:
            # get current position
            cur_pos[S] = 0
            if (S in state.position):
                cur_pos[S] = state.position[S]
            max_buy[S] = position_limits[S] - cur_pos[S]
            max_sell[S] = position_limits[S] + cur_pos[S]
            
            order_depth_S: OrderDepth = state.order_depths[S]
            
            total_bid_volume = 0
            total_bid_prices = 0

            total_ask_volume = 0
            total_ask_prices = 0
            
            for bid_price, bid_volume in order_depth_S.buy_orders.items():
                total_bid_volume += bid_volume
                total_bid_prices += bid_price * bid_volume
            avg_bid_price = total_bid_prices / total_bid_volume if total_bid_volume > 0 else math.nan
            
            for ask_price, ask_volume in order_depth_S.sell_orders.items():
                total_ask_volume += (-ask_volume)
                total_ask_prices += ask_price * (-ask_volume)
            avg_ask_price = total_ask_prices / total_ask_volume if total_ask_volume > 0 else math.nan

            highest_bids[S] = max(order_depth_S.buy_orders) if total_bid_volume > 0 else math.nan
            lowest_asks[S] = min(order_depth_S.sell_orders) if total_ask_volume > 0 else math.nan

            # basically only happens for options
            if (total_bid_volume == 0):
                avg_bid_price = avg_ask_price - 1
                highest_bids[S] = lowest_asks[S] - 1
            if (total_ask_volume == 0):
                avg_ask_price = avg_bid_price + 1
                lowest_asks[S] = highest_bids[S] + 1

            bid_prices[S] = avg_bid_price
            ask_prices[S] = avg_ask_price
            avg_prices[S] = (avg_bid_price + avg_ask_price) / 2

        target_position = {}

        # logic for options
        # always looking to liquidate...
        for product in symbols:
            target_position[product] = 0

        IV = {}
        delta = {}
        xi = {}
        z_score = {}

        # for the parabolic fit
        x = []
        y = []
        for product in coupons:
            IV[product] = implied_volatility(S=avg_prices[VOR], K=strikes[product], T=T, r=0, C=avg_prices[product])
            delta[product] = bsm_delta(S=avg_prices[VOR], K=strikes[product], T=T, r=0, sigma=IV[product])
            xi[product] = np.log(avg_prices[VOR] / strikes[product]) / np.sqrt(T)

        L = len(history_IV[VOR_C9500])
        for product in coupons:
            history_IV[product].append(IV[product])
            history_xi[product].append(xi[product])
            if (L == window_size):
                history_IV[product] = history_IV[product][1:]
                history_xi[product] = history_xi[product][1:]
    
        if (L < window_size):
            coeffs = [0, 0, 0]
        else:
            for product in coupons:
                x.extend(history_xi[product])
                y.extend(history_IV[product])
            # fit a parabola
            coeffs = np.polyfit(x, y, 2)
        poly = np.poly1d(coeffs)

        diffs = {}
        for product in coupons:
            diff = poly(xi[product]) - IV[product]
            if (L < window_size):  # no signals if too early
                diff = 0
            else:
                history_zz[product] = history_zz[product][1:]
                
            history_zz[product].append(diff)
            diffs[product] = diff

            # compute z score of diffs
            if (L == window_size):
                z = diff / np.std(history_zz[product])
                
                target_position[product] = round(f(z) * position_limits[product])
                if (target_position[product] != cur_pos[product]):
                    print(product, ': ', target_position[product], ' from ', cur_pos[product], 'z =', z)
        
        # delta hedge using the volcanic rocks
        for product in coupons:
            target_position[VOR] -= cur_pos[product] * delta[product]  # should aim to hedge current position!
        target_position[VOR] = round(target_position[VOR])
        if (target_position[VOR] > position_limits[VOR]):
            target_position[VOR] = position_limits[VOR]
        elif (target_position[VOR] < -position_limits[VOR]):
            target_position[VOR] = -position_limits[VOR]
        
        for product in symbols_r3:
            target_buy_price = round(avg_prices[product])
            target_sell_price = round(avg_prices[product])
            if (product == VOR): # different spread, so.....
                target_buy_price = math.floor(bid_prices[product]) + 1
                target_sell_price = math.ceil(ask_prices[product]) - 1
            if (target_position[product] > cur_pos[product]):
                result[product] = [Order(product, target_buy_price, target_position[product] - cur_pos[product])]
            if (target_position[product] < cur_pos[product]):
                result[product] = [Order(product, target_sell_price, target_position[product] - cur_pos[product])]
        
        # get new history
        history = {'IV': history_IV, 'xi': history_xi, 'zz': history_zz}
        traderData = jsonpickle.encode(history)

        conversions = 0
        return result, conversions, traderData